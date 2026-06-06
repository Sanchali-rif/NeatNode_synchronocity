from __future__ import annotations
 
import json
import os
import re
import sqlite3
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
 
# ── OpenRouter config (shared with cleaning_model) ─────────────────────────
# Keep this in sync with cleaning_model.py — or move to a shared config.py
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "gpt-oss-120b:free"
OPENROUTER_TIMEOUT   = 15
OPENROUTER_RETRIES   = 2
OPENROUTER_BACKOFF   = 2
OPENROUTER_COOLDOWN  = 12
 
FALLBACK_SQL = "SELECT * FROM cleaned_data LIMIT 20"
 
 
@dataclass
class QueryResult:
    question: str
    intent: str
    title: str
    summary: str
    sql_like: str
    matched_row_count: int
    total_row_count: int
    table_headers: list[str]
    table_rows: list[list[str]]
    detail_lines: list[str] = field(default_factory=list)
 
 
# ── Tiny OpenRouter client (same pattern as cleaning_model) ───────────────
 
class _OpenRouterClient:
    def __init__(self) -> None:
        self._cooldown_until: float = 0.0
 
    def call(self, prompt: str, max_tokens: int = 300) -> str | None:
        api_key = OPENROUTER_API_KEY
        if not api_key:
            print("[OpenRouter/query] API key not configured.")
            return None
 
        now = time.time()
        if now < self._cooldown_until:
            print(f"[OpenRouter/query] Cooldown active — {int(self._cooldown_until - now)}s remaining.")
            return None
 
        payload = json.dumps({
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": "Return only valid JSON when asked for structured output."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.0,
            "max_tokens": max_tokens,
        }).encode("utf-8")
 
        url = "https://openrouter.ai/api/v1/chat/completions"
        for attempt in range(OPENROUTER_RETRIES + 1):
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "http://localhost",
                    "X-Title": "NeatNode Synchronocity",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=OPENROUTER_TIMEOUT) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
                text = (
                    body.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                ).strip()
                if text:
                    print(f"[OpenRouter/query] OK via {OPENROUTER_MODEL}: {text[:200]}")
                    return text
                print("[OpenRouter/query] Empty response.")
                return None
            except urllib.error.HTTPError as err:
                if err.code == 429:
                    if attempt < OPENROUTER_RETRIES:
                        time.sleep(OPENROUTER_BACKOFF * (attempt + 1))
                        continue
                    self._cooldown_until = time.time() + OPENROUTER_COOLDOWN
                    print("[OpenRouter/query] 429 — cooldown set.")
                    return None
                print(f"[OpenRouter/query] HTTP {err.code}")
                return None
            except Exception as exc:
                print(f"[OpenRouter/query] Error: {exc}")
                return None
        return None
 
 
_openrouter = _OpenRouterClient()
 
 
def _parse_json(raw: str | None) -> dict | None:
    if not raw:
        return None
    text = re.sub(r"```(?:json)?|```", "", raw).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    return None
 
 
# ── Main assistant ────────────────────────────────────────────────────────
 
class DataQueryAssistant:
 
    def answer(
        self,
        question: str,
        headers: list[str],
        rows: list[list[str]],
        preview_rows: list[list[str]] | None = None,
        cleaning_prompt: str | None = None,
        summary_notes: list[str] | None = None,
    ) -> QueryResult:
        question     = (question or "").strip()
        total        = len(rows)
        sample       = preview_rows or rows[:20]
        norm_q       = self._norm(question)
 
        if not question:
            return self._help_result(total)
 
        # ── 1. Try cheap local patterns first ─────────────────────────────────
        local = self._local_answer(question, norm_q, headers, rows, sample, total)
        if local:
            return local
 
        # ── 2. Call OpenRouter ONCE to get SQL ────────────────────────────────
        sql = self._openrouter_sql(question, headers, sample, cleaning_prompt, summary_notes)
 
        if not sql:
            return self._preview_result(question, headers, sample, total,
                                        "Could not generate SQL. Showing a data preview instead.")
 
        try:
            result_headers, result_rows = self._run_sql(sql, headers, rows)
        except Exception as exc:
            return self._preview_result(
                question, headers, sample, total,
                f"SQL execution failed: {exc}  |  SQL was: {sql}",
            )
 
        return QueryResult(
            question          = question,
            intent            = "openrouter_sql",
            title             = "Query result",
            summary           = f"Found {len(result_rows)} row(s).",
            sql_like          = sql,
            matched_row_count = len(result_rows),
            total_row_count   = total,
            table_headers     = result_headers,
            table_rows        = result_rows,
            detail_lines      = [
                f"SQL: {sql}",
                f"Input rows: {total}  |  Output rows: {len(result_rows)}",
            ],
        )
 
    # ── OpenRouter SQL generation ─────────────────────────────────────────────
 
    def _openrouter_sql(
        self,
        question: str,
        headers: list[str],
        preview_rows: list[list[str]],
        cleaning_prompt: str | None,
        summary_notes: list[str] | None,
    ) -> str | None:
        """
        Ask OpenRouter to turn the user's plain-English question into ONE SQLite
        SELECT statement against the table `cleaned_data`.
 
        We send:
          - exact column names
          - up to 20 sample rows (so the model can infer data shapes)
          - the cleaning prompt (context on what was cleaned)
        """
        sample_dicts = [
            dict(zip(headers, (row + [""] * len(headers))[:len(headers)]))
            for row in preview_rows[:20]
        ]
 
        system_block = (
            "You are a precise SQLite SQL generator for a data chatbot.\n\n"
            "RULES:\n"
            "- Output JSON ONLY with keys: sql, title, summary. No markdown.\n"
            "- `sql` must be a single read-only SELECT (or WITH…SELECT) statement.\n"
            "- The table name is always `cleaned_data`.\n"
            "- Column names must be taken EXACTLY from the 'Available columns' list.\n"
            "- Always quote column names with double quotes: \"column_name\".\n"
            "- NEVER use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, PRAGMA, ATTACH.\n"
            "- If the question asks for unique values, use SELECT DISTINCT.\n"
            "- If the question asks for a count, use COUNT(*).\n"
            "- If the question asks for averages / sums / min / max, use the matching aggregate.\n"
            "- For numeric comparisons cast the column: CAST(\"col\" AS REAL).\n"
            "- For vague questions like 'show data' or 'status', use: "
            "  SELECT * FROM cleaned_data LIMIT 20\n\n"
            "Examples:\n"
            "  'how many rows' → {\"sql\":\"SELECT COUNT(*) AS row_count FROM cleaned_data\","
            "\"title\":\"Row count\",\"summary\":\"Total rows.\"}\n"
            "  'show unique gender' → {\"sql\":\"SELECT DISTINCT \\\"gender\\\" FROM cleaned_data\","
            "\"title\":\"Unique gender values\",\"summary\":\"Distinct values.\"}\n"
            "  'average age' → {\"sql\":\"SELECT AVG(CAST(\\\"age\\\" AS REAL)) AS avg_age FROM cleaned_data\","
            "\"title\":\"Average age\",\"summary\":\"Mean value.\"}\n"
            "  'rows where age > 30' → {\"sql\":\"SELECT * FROM cleaned_data "
            "WHERE CAST(\\\"age\\\" AS REAL) > 30 LIMIT 50\","
            "\"title\":\"Age > 30\",\"summary\":\"Filtered rows.\"}"
        )
 
        context_bits = [
            f"Available columns: {json.dumps(headers)}",
            f"Sample rows (first {len(sample_dicts)}): {json.dumps(sample_dicts)}",
        ]
        if cleaning_prompt:
            context_bits.append(f"Cleaning prompt used: {cleaning_prompt}")
        if summary_notes:
            context_bits.append(f"Cleaning notes: {json.dumps(summary_notes[:3])}")
 
        full_prompt = (
            f"{system_block}\n\n"
            + "\n".join(context_bits)
            + f"\n\nUser question: {question}"
        )
 
        print(f"[_openrouter_sql] Sending question to OpenRouter: {question[:120]}")
        raw    = _openrouter.call(full_prompt, max_tokens=300)
        parsed = _parse_json(raw)
        if not parsed:
            return None
 
        sql = str(parsed.get("sql") or "").strip()
        print(f"[_openrouter_sql] Generated SQL: {sql}")
        return sql or None
 
    # ── Local fast-path answers (no API call) ─────────────────────────────────
 
    def _local_answer(
        self,
        question: str,
        norm_q: str,
        headers: list[str],
        rows: list[list[str]],
        sample: list[list[str]],
        total: int,
    ) -> QueryResult | None:
 
        # preview / show data
        if re.search(r"\b(preview|sample|show\s+data|show\s+rows|first\s+rows?|display)\b", norm_q):
            return self._preview_result(question, headers, sample, total, "Sample rows from cleaned data.")

        # arithmetic transform preview (e.g. 'increase age by 1')
        arith = self._parse_arithmetic_prompt(question, headers)
        if arith:
            transformed_sample = [self._apply_arithmetic_preview(row, headers, arith) for row in sample]
            op_label = arith["operation"]
            value_label = arith["value"]
            return QueryResult(
                question=question,
                intent="local_transform_preview",
                title="Transformed preview",
                summary=f"Applied {arith['column']} {op_label} {value_label} to the preview rows.",
                sql_like=FALLBACK_SQL,
                matched_row_count=len(transformed_sample),
                total_row_count=total,
                table_headers=headers,
                table_rows=transformed_sample,
                detail_lines=[
                    "Answered locally — no SQL needed.",
                    f"Preview shows {arith['column']} updated in the output rows.",
                ],
            )
 
        # row count
        if re.search(r"\b(count|how many|number of rows?|row count|total rows?)\b", norm_q):
            sql = "SELECT COUNT(*) AS row_count FROM cleaned_data"
            h, r = self._run_sql(sql, headers, rows)
            return QueryResult(
                question=question, intent="count_rows",
                title="Row count",
                summary=f"{r[0][0] if r else 0} rows in dataset.",
                sql_like=sql, matched_row_count=1, total_row_count=total,
                table_headers=h, table_rows=r,
                detail_lines=["Answered locally — no API call needed."],
            )
 
        # schema / columns
        if re.search(r"\b(columns?|headers?|schema|fields?)\b", norm_q):
            return QueryResult(
                question=question, intent="schema",
                title="Column names",
                summary=f"{len(headers)} columns: {', '.join(headers)}",
                sql_like=FALLBACK_SQL, matched_row_count=0, total_row_count=total,
                table_headers=["column"], table_rows=[[h] for h in headers],
                detail_lines=["Answered locally — no API call needed."],
            )
 
        return None
 
    # ── SQL runner ────────────────────────────────────────────────────────────
 
    def _run_sql(self, sql: str, headers: list[str], rows: list[list[str]]) -> tuple[list[str], list[list[str]]]:
        sql = self._validate_sql(sql)
        conn = sqlite3.connect(":memory:")
        try:
            safe_cols = [h.replace('"', '""') for h in headers]
            col_defs  = ", ".join(f'"{c}" TEXT' for c in safe_cols)
            conn.execute(f"CREATE TABLE cleaned_data ({col_defs})")
            width = len(headers)
            norm_rows = [
                [("" if v is None else str(v)) for v in (list(r[:width]) + [""] * max(0, width - len(r)))]
                for r in rows
            ]
            conn.executemany(
                f"INSERT INTO cleaned_data VALUES ({','.join('?' * width)})",
                norm_rows,
            )
            conn.commit()
            cur  = conn.execute(sql)
            desc = cur.description or []
            return (
                [str(c[0]) for c in desc],
                [["" if v is None else str(v) for v in row] for row in cur.fetchall()],
            )
        finally:
            conn.close()
 
    def _validate_sql(self, sql: str) -> str:
        s = (sql or "").strip().rstrip(";").strip()
        if not s:
            raise ValueError("SQL is empty.")
        low = s.lower()
        if not (low.startswith("select") or low.startswith("with")):
            raise ValueError("Only SELECT queries are allowed.")
        blocked = [" insert ", " update ", " delete ", " drop ", " alter ",
                   " create ", " pragma ", " attach ", " detach ", " truncate "]
        padded = f" {low} "
        for b in blocked:
            if b in padded:
                raise ValueError(f"Blocked SQL keyword: {b.strip()}")
        if ";" in s:
            raise ValueError("Only single statements allowed.")
        return s
 
    # ── Result builders ───────────────────────────────────────────────────────
 
    def _preview_result(self, q, headers, sample, total, summary) -> QueryResult:
        return QueryResult(
            question=q, intent="preview", title="Data preview",
            summary=summary, sql_like=FALLBACK_SQL,
            matched_row_count=len(sample), total_row_count=total,
            table_headers=headers, table_rows=sample,
            detail_lines=["Preview generated locally."],
        )
 
    def _help_result(self, total) -> QueryResult:
        return QueryResult(
            question="", intent="help", title="Ask a data question",
            summary="Type a question about your cleaned CSV.",
            sql_like=FALLBACK_SQL, matched_row_count=0, total_row_count=total,
            table_headers=["Example question"],
            table_rows=[
                ["How many rows are in the dataset?"],
                ["Show unique values in gender"],
                ["Show rows where age > 30"],
                ["What is the average age?"],
                ["Show rows where full_name contains Smith"],
            ],
        )
 
    # ── Util ──────────────────────────────────────────────────────────────────
 
    @staticmethod
    def _norm(text: str) -> str:
        return re.sub(r"[^a-z0-9 ]+", " ", text.lower()).strip()

    def _parse_arithmetic_prompt(self, question: str, headers: list[str]) -> dict | None:
        text = self._norm(question)
        header_lookup = {self._norm(h): h for h in headers}

        patterns = [
            (r"\b(?:increase|increment|add)\s+([a-z0-9_ ]+?)\s+by\s+([+-]?\d+(?:\.\d+)?)\b", "+"),
            (r"\b(?:decrease|decrement|subtract)\s+([a-z0-9_ ]+?)\s+by\s+([+-]?\d+(?:\.\d+)?)\b", "-"),
            (r"\b([a-z0-9_ ]+?)\s*([+\-*/])\s*([+-]?\d+(?:\.\d+)?)\b", None),
        ]

        for pattern, fixed_op in patterns:
            m = re.search(pattern, text)
            if not m:
                continue

            if fixed_op is None:
                col_term, op, value_text = m.group(1), m.group(2), m.group(3)
            else:
                col_term, value_text, op = m.group(1), m.group(2), fixed_op

            col_term = col_term.strip()
            if not col_term or col_term in {"all", "the", "a", "of", "in", "for", "to", "by"}:
                continue

            matched_column = None
            norm_term = self._norm(col_term)
            if norm_term in header_lookup:
                matched_column = header_lookup[norm_term]
            else:
                for norm_header, original in header_lookup.items():
                    if norm_term == norm_header or norm_term in norm_header or norm_header in norm_term:
                        matched_column = original
                        break

            if not matched_column:
                continue

            try:
                value = float(value_text)
            except ValueError:
                continue

            return {
                "column": matched_column,
                "operation": op,
                "value": value,
            }

        return None

    def _apply_arithmetic_preview(self, row: list[str], headers: list[str], spec: dict) -> list[str]:
        row = list(row)
        column = spec["column"]
        operation = spec["operation"]
        value = float(spec["value"])

        try:
            idx = headers.index(column)
        except ValueError:
            return row

        current = row[idx]
        try:
            current_value = float(current)
        except (TypeError, ValueError):
            return row

        if operation == "+":
            result = current_value + value
        elif operation == "-":
            result = current_value - value
        elif operation == "*":
            result = current_value * value
        elif operation == "/":
            result = current_value / value if value else current_value
        else:
            return row

        if result.is_integer():
            row[idx] = str(int(result))
        else:
            row[idx] = f"{result:.6f}".rstrip("0").rstrip(".")
        return row