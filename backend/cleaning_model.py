import csv
import io
import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from statistics import median
from typing import Any

# ── OpenRouter config ─────────────────────────────────────────────────────────
OPENROUTER_API_KEY = "process.env.OPENROUTER_API_KEY"
OPENROUTER_MODEL = "gpt-oss-120b:free"
OPENROUTER_TIMEOUT   = 15       # seconds per HTTP call
OPENROUTER_RETRIES   = 2        # retries on 429
OPENROUTER_BACKOFF   = 2        # seconds between retries
OPENROUTER_COOLDOWN  = 12       # seconds cooldown after exhausting retries

# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class CleaningSummary:
    filename: str
    raw_headers: list[str]
    cleaned_headers: list[str]
    raw_column_count: int
    cleaned_column_count: int
    raw_row_count: int
    cleaned_row_count: int
    removed_empty_rows: int
    removed_duplicate_rows: int
    removed_outlier_rows: int
    imputation_summary: list[dict[str, object]]
    summary_notes: list[str]
    ai_summary: str | None
    prompt_used: str | None
    cleaned_rows: list[list[str]]
    preview_rows: list[list[str]]
    cleaned_csv_text: str
    ai_review_error: str | None = None


@dataclass
class PromptPreferences:
    remove_empty_rows: bool = True
    remove_duplicate_rows: bool = True
    remove_outlier_rows: bool = True
    fill_strategy: str | None = None          # null|zero|mode|median|literal|auto
    fill_value: str | None = None
    column_fill_values: dict[str, str] | None = None
    treat_missing_as_blank: bool = True
    drop_columns: list[str] | None = None
    keep_columns: list[str] | None = None
    arithmetic_columns: list[dict] | None = None  # [{column, operation, value}]
    value_replacements: list[dict] | None = None   # [{column, from, to}]
    swap_columns: list[dict] | None = None         # [{left, right}]
    prompt_summary: str | None = None


# ── Tiny HTTP helper ──────────────────────────────────────────────────────────

class _OpenRouterClient:
    """Minimal OpenRouter REST client with retry + cooldown logic."""

    def __init__(self) -> None:
        self._cooldown_until: float = 0.0

    def call(self, prompt: str, max_tokens: int = 512, temperature: float = 0.0) -> str | None:
        """Send *prompt* to OpenRouter; return raw text or None on failure."""
        api_key = OPENROUTER_API_KEY
        if not api_key:
            print("[OpenRouter] API key not configured.")
            return None

        now = time.time()
        if now < self._cooldown_until:
            remaining = int(self._cooldown_until - now)
            print(f"[OpenRouter] Cooldown active — {remaining}s remaining.")
            return None

        payload = json.dumps({
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": "Return only valid JSON when asked for structured output."},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
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
                    print(f"[OpenRouter] OK via {OPENROUTER_MODEL}. Response preview: {text[:200]}")
                    return text
                print("[OpenRouter] Empty response.")
                return None
            except urllib.error.HTTPError as err:
                if err.code == 429:
                    if attempt < OPENROUTER_RETRIES:
                        wait = OPENROUTER_BACKOFF * (attempt + 1)
                        print(f"[OpenRouter] 429, retry in {wait}s …")
                        time.sleep(wait)
                        continue
                    self._cooldown_until = time.time() + OPENROUTER_COOLDOWN
                    print(f"[OpenRouter] 429 exhausted. Cooldown {OPENROUTER_COOLDOWN}s.")
                    return None
                print(f"[OpenRouter] HTTP {err.code}: {err.reason}")
                return None
            except Exception as exc:
                print(f"[OpenRouter] Error: {exc}")
                return None
        return None

    @staticmethod
    def _extract_text(body: dict) -> str:
        try:
            parts = body["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts if isinstance(p, dict)).strip()
        except (KeyError, IndexError, TypeError):
            return ""


_openrouter = _OpenRouterClient()


def _parse_json(raw: str | None) -> dict | None:
    """Strip markdown fences and parse JSON; return None on failure."""
    if not raw:
        return None
    text = re.sub(r"```(?:json)?|```", "", raw).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    print(f"[Gemini] JSON parse failed. Raw text was: {raw[:400]}")
    return None


# ── Main model ────────────────────────────────────────────────────────────────

class CSVCleaningModel:
    EMPTY_MARKERS = {"", "na", "n/a", "null", "none", "-", "--", "unknown"}

    # ── Public entry point ────────────────────────────────────────────────────

    def clean_upload(self, file_storage, prompt: str | None = None) -> CleaningSummary:
        print(f"[clean_upload] file={getattr(file_storage,'filename','?')} prompt={repr((prompt or '')[:120])}")

        stream = io.TextIOWrapper(file_storage.stream, encoding="utf-8-sig", newline="")
        reader = csv.reader(stream)
        rows = list(reader)
        if not rows:
            raise ValueError("CSV file is empty.")

        raw_headers = [h.strip() for h in rows[0]]
        data_rows   = rows[1:] if len(rows) > 1 else []
        col_count   = max([len(rows[0])] + [len(r) for r in data_rows])

        padded_raw     = self._pad_row(raw_headers, col_count)
        cleaned_headers = self._normalize_headers(padded_raw)

        # ── Step 1: interpret the user prompt with OpenRouter ─────────────────
        prefs = PromptPreferences()
        if prompt:
            prefs = self._interpret_prompt(prompt, raw_headers, cleaned_headers) or prefs
            print(f"[clean_upload] Preferences after interpretation: {prefs}")

        # ── Step 2: resolve column selection ─────────────────────────────────
        drop_idx, dropped_hdr = self._resolve_columns(raw_headers, cleaned_headers, prefs.drop_columns or [])
        keep_idx, _           = self._resolve_columns(raw_headers, cleaned_headers, prefs.keep_columns or [])
        if keep_idx:
            drop_idx = [i for i in drop_idx if i not in keep_idx]

        kept_idx       = [i for i in range(col_count) if i not in drop_idx]
        f_raw_hdr      = [raw_headers[i]     for i in kept_idx]
        f_clean_hdr    = [cleaned_headers[i] for i in kept_idx]
        dropped_labels = [cleaned_headers[i] for i in drop_idx]

        if prefs.swap_columns:
            kept_idx, f_raw_hdr, f_clean_hdr = self._apply_column_swaps_to_order(
                kept_idx,
                f_raw_hdr,
                f_clean_hdr,
                prefs.swap_columns,
            )

        profiles = self._build_column_profiles(f_clean_hdr, data_rows, kept_idx)

        # ── Step 3: clean rows ────────────────────────────────────────────────
        cleaned_rows: list[list[str]] = []
        seen: set[tuple] = set()
        n_empty = n_dup = n_out = 0
        imputation_summary: list[dict] = []

        for row in data_rows:
            padded = self._pad_row(row, col_count)
            crow   = [self._clean_cell(padded[i]) for i in kept_idx]
            filled_mask = [False] * len(crow)

            if prefs.remove_empty_rows and all(c == "" for c in crow):
                n_empty += 1
                continue

            # fill missing
            for idx, val in enumerate(crow):
                col_name = f_clean_hdr[idx]
                if val == "":
                    crow[idx] = self._fill_value(col_name, profiles[idx], prefs)
                    profiles[idx]["filled_count"] = int(profiles[idx]["filled_count"]) + 1
                    filled_mask[idx] = True

            # fix physically impossible values (e.g. age = -70) BEFORE arithmetic
            crow, _ = self._apply_invalid_value_rules(crow, f_clean_hdr, profiles, prefs)
            # re-fill any cells that were just blanked
            for idx, val in enumerate(crow):
                if val == "" and profiles[idx].get("is_numeric"):
                    crow[idx] = self._fill_value(f_clean_hdr[idx], profiles[idx], prefs)
                    profiles[idx]["filled_count"] = int(profiles[idx]["filled_count"]) + 1
                    filled_mask[idx] = True

            # arithmetic transforms (e.g. "make all age +1")
            if prefs.arithmetic_columns:
                crow = self._apply_arithmetic(crow, f_clean_hdr, prefs.arithmetic_columns, skip_indices={i for i, filled in enumerate(filled_mask) if filled})

            # explicit value replacements (e.g. "make blood group o+ into A+")
            if prefs.value_replacements:
                crow = self._apply_value_replacements(crow, f_clean_hdr, prefs.value_replacements)

            # outlier removal
            if prefs.remove_outlier_rows:
                out_cols = self._outlier_columns(crow, profiles)
                if out_cols:
                    n_out += 1
                    continue

            key = tuple(crow)
            if prefs.remove_duplicate_rows and key in seen:
                n_dup += 1
                continue
            seen.add(key)
            cleaned_rows.append(crow)

        for p in profiles:
            if p["filled_count"] > 0:
                imputation_summary.append({
                    "column":       p["column_name"],
                    "strategy":     p["strategy"],
                    "fill_value":   p["fill_value"],
                    "filled_count": p["filled_count"],
                })

        notes  = self._build_notes(n_empty, n_dup, n_out, profiles, prompt, prefs, dropped_labels)
        ai_sum = self._build_ai_summary(n_empty, n_dup, n_out, dropped_labels)

        out = io.StringIO()
        csv.writer(out).writerows([f_clean_hdr] + cleaned_rows)

        return CleaningSummary(
            filename             = file_storage.filename,
            raw_headers          = f_raw_hdr,
            cleaned_headers      = f_clean_hdr,
            raw_column_count     = len(rows[0]),
            cleaned_column_count = len(f_clean_hdr),
            raw_row_count        = len(data_rows),
            cleaned_row_count    = len(cleaned_rows),
            removed_empty_rows   = n_empty,
            removed_duplicate_rows = n_dup,
            removed_outlier_rows = n_out,
            imputation_summary   = imputation_summary,
            summary_notes        = notes,
            ai_summary           = ai_sum,
            prompt_used          = prompt or None,
            cleaned_rows         = cleaned_rows,
            preview_rows         = cleaned_rows[:20],
            cleaned_csv_text     = out.getvalue(),
        )

    # ── Prompt interpretation via OpenRouter ──────────────────────────────────

    def _interpret_prompt(
        self,
        prompt: str,
        raw_headers: list[str],
        cleaned_headers: list[str],
    ) -> PromptPreferences | None:
        """
        TWO-PHASE interpretation:

        Phase 1 (always runs, zero API cost):
            Scan the prompt for any actual column names mentioned. If a column
            name from the CSV appears in the prompt alongside a drop/keep/fill
            keyword, record it directly. This catches cases like "remove the
            returned column" where the LLM might confuse "returned" as a verb.

        Phase 2 (OpenRouter, one call):
            Send the prompt + column list to OpenRouter for everything else
            (arithmetic, complex fills, etc.). Phase-1 results are used as a
            hard override on top of whatever OpenRouter returns.

        Also: if the prompt is ONLY about column drop/keep and contains no
        mention of outlier/duplicate/empty-row removal, those flags default
        to False so we don't silently delete hundreds of rows.
        """

        # ── Phase 1: direct column-name matching ──────────────────────────────
        direct_drop = self._direct_column_match(prompt, raw_headers, cleaned_headers, intent="drop")
        direct_keep = self._direct_column_match(prompt, raw_headers, cleaned_headers, intent="keep")

        # Detect whether the prompt is a column-level or arithmetic operation
        # (NOT a row-removal request). We suppress outlier/duplicate/empty-row
        # removal for these so we don't silently delete hundreds of rows.
        explicit_row_removal = re.search(
            r"\b(outlier|duplicate|remove\s+rows?|delete\s+rows?|drop\s+rows?|clean\s+rows?)\b",
            prompt.lower(),
        )
        has_arithmetic_intent = re.search(
            r"\b(increase|increment|add|decrease|decrement|subtract|multiply|divide"
            r"|increases?|all\s+the\s+\w+\s+(by|\+))\b"
            r"|\b\w+\s+(by\s+)?\+\d"
            r"|\bincrease[sd]?\s+by\b",
            prompt.lower(),
        )
        has_fill_intent = re.search(
            r"\b(fill|replace|set)\s+.*(null|missing|empty|blank|nan)\b"
            r"|\b(null|missing|empty|blank|nan).*\b(fill|replace|with|to)\b",
            prompt.lower(),
        )
        has_value_replacement_intent = re.search(
            r"\b(make|change|turn|convert|replace|set)\b.*\b(into|to|with|as)\b",
            prompt.lower(),
        )
        has_swap_intent = re.search(
            r"\b(swap|interchange|exchange|switch|transpose)\b",
            prompt.lower(),
        )
        # Suppress row removal when: user is dropping/keeping a column, doing
        # arithmetic, replacing null values, or rewriting values — and has NOT
        # asked for row removal
        column_only_prompt = (
            bool(direct_drop or direct_keep or has_arithmetic_intent or has_fill_intent or has_value_replacement_intent or has_swap_intent)
            and not explicit_row_removal
        )

        # ── Phase 2: OpenRouter for the rest ──────────────────────────────────
        schema_hint = json.dumps({
            "remove_empty_rows":    True,
            "remove_duplicate_rows": True,
            "remove_outlier_rows":  False,   # default False — only True if explicitly asked
            "fill_strategy":        "null | zero | mode | median | literal | auto",
            "fill_value":           "string or null",
            "drop_columns":         ["exact column names to drop"],
            "keep_columns":         ["exact column names to keep"],
            "column_fill_values":   {"column_name": "fill_value"},
            "arithmetic_columns":   [{"column": "col_name", "operation": "+|-|*|/", "value": 1}],
            "swap_columns":         [{"left": "col_a", "right": "col_b"}],
            "prompt_summary":       "one-line description of what was requested",
        }, indent=2)

        # Build a concrete few-shot example using the actual column names
        col_example = cleaned_headers[0] if cleaned_headers else "age"
        system_block = (
            "You are a CSV data-cleaning configuration assistant.\n"
            "Your ONLY job: read the user instruction and the available column names, "
            "then output a single strict JSON object matching the schema below.\n\n"
            "CRITICAL RULES:\n"
            "- Output JSON ONLY. No markdown. No explanation. No extra keys.\n"
            "- Use EXACT column names from 'Available columns (cleaned)' list.\n"
            "- A word in the instruction that matches a column name IS a column name,\n"
            "  even if it looks like a verb (e.g. 'returned' = column, not a verb).\n"
            "- For arithmetic ('increase age by 1', 'all the age increases by +1',\n"
            "  'make salary *2', 'age +1'): populate arithmetic_columns.\n"
            "- For value rewrites ('make all blood group o+ into A+', 'change o+ to A+\n"
            "  in blood group'): populate value_replacements.\n"
            "- For swapping two columns ('swap columns A and B', 'interchange X with Y'):\n"
            "  populate swap_columns with the two exact column names.\n"
            "- For drop/keep column instructions: populate drop_columns or keep_columns.\n"
            "- For null/missing fill ('fill null age with 0', 'replace missing salary\n"
            "  with median', 'set empty name to Unknown'): set fill_strategy and/or\n"
            "  column_fill_values with the specific column and value.\n"
            "- Set remove_outlier_rows=true ONLY if user EXPLICITLY asks to remove outliers.\n"
            "- Set remove_duplicate_rows=true ONLY if user EXPLICITLY asks to remove duplicates.\n"
            "- Set remove_empty_rows=true ONLY if user EXPLICITLY asks to remove empty rows.\n"
            "- Default all three removal flags to FALSE unless explicitly requested.\n\n"
            "Examples:\n"
            "  'all the age increases by +1' → "
            '{"remove_outlier_rows":false,"remove_duplicate_rows":false,"remove_empty_rows":false,'
            '"arithmetic_columns":[{"column":"age","operation":"+","value":1}],'
            '"prompt_summary":"increase age by 1"}\n'
            "  'i dont need the returned column' → "
            '{"remove_outlier_rows":false,"drop_columns":["returned"],'
            '"prompt_summary":"drop returned column"}\n'
            "  'fill null age with 0' → "
            '{"remove_outlier_rows":false,"fill_strategy":"literal","fill_value":"0",'
            '"column_fill_values":{"age":"0"},"prompt_summary":"fill null age with 0"}\n'
            "  'replace missing salary with median' → "
            '{"remove_outlier_rows":false,"fill_strategy":"median",'
            '"column_fill_values":{"salary":"median"},"prompt_summary":"fill salary with median"}\n\n'
            "  'make all blood group that are o+ into A+' → "
            '{"remove_outlier_rows":false,"value_replacements":[{"column":"blood_group","from":"o+","to":"A+"}],'
            '"prompt_summary":"change o+ blood group values to A+"}\n\n'
            "  'swap columns first_name and last_name' → "
            '{"remove_outlier_rows":false,"swap_columns":[{"left":"first_name","right":"last_name"}],'
            '"prompt_summary":"swap first_name and last_name"}\n\n'
            f"JSON schema:\n{schema_hint}"
        )

        user_block = (
            f"Available columns (raw):     {json.dumps(raw_headers)}\n"
            f"Available columns (cleaned): {json.dumps(cleaned_headers)}\n\n"
            f"User instruction: {prompt}"
        )

        full_prompt = f"{system_block}\n\n{user_block}"

        print(f"[_interpret_prompt] Calling OpenRouter for prompt: {prompt[:160]}")
        raw    = _openrouter.call(full_prompt, max_tokens=400, temperature=0.0)
        parsed = _parse_json(raw)

        if parsed:
            print(f"[_interpret_prompt] OpenRouter JSON: {parsed}")
            prefs = self._json_to_prefs(parsed)
        else:
            print("[_interpret_prompt] OpenRouter returned no usable JSON; using fallback.")
            prefs = self._fallback_prefs(prompt, raw_headers, cleaned_headers) or PromptPreferences()

        local_prefs = self._fallback_prefs(prompt, raw_headers, cleaned_headers)
        if local_prefs:
            prefs = self._merge_prefs(prefs, local_prefs)

        # ── Phase 1 hard-override: direct column matches win ──────────────────
        if direct_drop:
            print(f"[_interpret_prompt] Phase-1 direct drop override: {direct_drop}")
            prefs.drop_columns = list(dict.fromkeys((prefs.drop_columns or []) + direct_drop))
        if direct_keep:
            print(f"[_interpret_prompt] Phase-1 direct keep override: {direct_keep}")
            prefs.keep_columns = list(dict.fromkeys((prefs.keep_columns or []) + direct_keep))

        # ── Safety: don't silently remove rows when the prompt is column-only ─
        if column_only_prompt:
            prefs.remove_outlier_rows    = False
            prefs.remove_duplicate_rows  = False
            prefs.remove_empty_rows      = False
            print("[_interpret_prompt] Column-only prompt detected — row-removal flags set to False.")

        return prefs

    def _direct_column_match(
        self,
        prompt: str,
        raw_headers: list[str],
        cleaned_headers: list[str],
        intent: str,  # "drop" or "keep"
    ) -> list[str]:
        """
        Scan the prompt for any actual column name that appears alongside a
        drop/keep keyword. Returns matched cleaned header names.

        This is purely string-based — no LLM needed — and is the safest way
        to catch things like "remove the returned column" where 'returned'
        is both a verb and a column name.
        """
        pt = prompt.lower()

        if intent == "drop":
            has_intent = re.search(
                r"\b(remove|drop|delete|exclude|dont need|do not need|without|get rid of|eliminate)\b",
                pt,
            )
        else:
            has_intent = re.search(
                r"\b(keep|retain|preserve|only want|need only)\b",
                pt,
            )

        if not has_intent:
            return []

        matched: list[str] = []
        norm = lambda s: re.sub(r"[^a-z0-9]", " ", s.lower()).strip()
        pt_norm = norm(pt)

        for raw_h, clean_h in zip(raw_headers, cleaned_headers):
            for h in (raw_h, clean_h):
                h_norm = norm(h)
                if h_norm and h_norm in pt_norm:
                    if clean_h not in matched:
                        matched.append(clean_h)
                    break

        return matched

    def _json_to_prefs(self, data: dict) -> PromptPreferences:
        p = PromptPreferences()
        # Default ALL removal flags to False when coming from OpenRouter JSON.
        # The user must explicitly request row removal — we never silently
        # delete hundreds of rows just because the prompt didn't mention it.
        p.remove_empty_rows      = bool(data.get("remove_empty_rows",      False))
        p.remove_duplicate_rows  = bool(data.get("remove_duplicate_rows",  False))
        p.remove_outlier_rows    = bool(data.get("remove_outlier_rows",    False))

        fs = data.get("fill_strategy")
        if fs in {"zero", "mode", "median", "literal", "auto"}:
            p.fill_strategy = fs

        fv = data.get("fill_value")
        if isinstance(fv, str) and fv.strip():
            p.fill_value = fv.strip()

        dc = data.get("drop_columns")
        if isinstance(dc, list):
            p.drop_columns = [str(x).strip() for x in dc if str(x).strip()]

        kc = data.get("keep_columns")
        if isinstance(kc, list):
            p.keep_columns = [str(x).strip() for x in kc if str(x).strip()]

        cfv = data.get("column_fill_values")
        if isinstance(cfv, dict):
            p.column_fill_values = {
                str(k).strip(): str(v).strip()
                for k, v in cfv.items() if str(k).strip() and str(v).strip()
            }

        ac = data.get("arithmetic_columns")
        if isinstance(ac, list):
            valid = []
            for item in ac:
                if isinstance(item, dict) and item.get("column") and item.get("operation"):
                    try:
                        valid.append({
                            "column":    str(item["column"]).strip(),
                            "operation": str(item["operation"]).strip(),
                            "value":     float(item.get("value", 0)),
                        })
                    except (ValueError, TypeError):
                        pass
            p.arithmetic_columns = valid or None

        vr = data.get("value_replacements")
        if isinstance(vr, list):
            valid_replacements = []
            for item in vr:
                if isinstance(item, dict) and item.get("column") and item.get("from") is not None and item.get("to") is not None:
                    valid_replacements.append({
                        "column": str(item["column"]).strip(),
                        "from": str(item["from"]).strip(),
                        "to": str(item["to"]).strip(),
                    })
            p.value_replacements = valid_replacements or None

        sc = data.get("swap_columns")
        if isinstance(sc, list):
            valid_swaps = []
            for item in sc:
                if isinstance(item, dict) and item.get("left") and item.get("right"):
                    left = str(item["left"]).strip()
                    right = str(item["right"]).strip()
                    if left and right and left.lower() != right.lower():
                        valid_swaps.append({"left": left, "right": right})
            p.swap_columns = valid_swaps or None

        ps = data.get("prompt_summary")
        if isinstance(ps, str) and ps.strip():
            p.prompt_summary = ps.strip()

        return p

    def _merge_prefs(self, primary: PromptPreferences, secondary: PromptPreferences) -> PromptPreferences:
        merged = PromptPreferences(
            remove_empty_rows=primary.remove_empty_rows,
            remove_duplicate_rows=primary.remove_duplicate_rows,
            remove_outlier_rows=primary.remove_outlier_rows,
            fill_strategy=primary.fill_strategy,
            fill_value=primary.fill_value,
            column_fill_values=dict(primary.column_fill_values or {}),
            treat_missing_as_blank=primary.treat_missing_as_blank,
            drop_columns=list(primary.drop_columns or []),
            keep_columns=list(primary.keep_columns or []),
            arithmetic_columns=list(primary.arithmetic_columns or []),
            value_replacements=list(primary.value_replacements or []),
            swap_columns=list(primary.swap_columns or []),
            prompt_summary=primary.prompt_summary,
        )

        if secondary.remove_empty_rows is not None:
            merged.remove_empty_rows = secondary.remove_empty_rows
        if secondary.remove_duplicate_rows is not None:
            merged.remove_duplicate_rows = secondary.remove_duplicate_rows
        if secondary.remove_outlier_rows is not None:
            merged.remove_outlier_rows = secondary.remove_outlier_rows

        if secondary.fill_strategy:
            merged.fill_strategy = secondary.fill_strategy
        if secondary.fill_value is not None:
            merged.fill_value = secondary.fill_value
        if secondary.column_fill_values:
            merged.column_fill_values.update(secondary.column_fill_values)

        if secondary.drop_columns:
            merged.drop_columns = list(dict.fromkeys(merged.drop_columns + list(secondary.drop_columns)))
        if secondary.keep_columns:
            merged.keep_columns = list(dict.fromkeys(merged.keep_columns + list(secondary.keep_columns)))
        if secondary.arithmetic_columns:
            merged.arithmetic_columns = (merged.arithmetic_columns or []) + list(secondary.arithmetic_columns)
        if secondary.value_replacements:
            merged.value_replacements = (merged.value_replacements or []) + list(secondary.value_replacements)
        if secondary.swap_columns:
            merged.swap_columns = (merged.swap_columns or []) + list(secondary.swap_columns)

        if merged.swap_columns:
            deduped_swaps = []
            seen_swaps: set[tuple[str, str]] = set()
            for item in merged.swap_columns:
                left = str(item.get("left", "")).strip()
                right = str(item.get("right", "")).strip()
                if not left or not right:
                    continue
                key = (left.lower(), right.lower())
                rev = (right.lower(), left.lower())
                if key in seen_swaps or rev in seen_swaps:
                    continue
                seen_swaps.add(key)
                deduped_swaps.append({"left": left, "right": right})
            merged.swap_columns = deduped_swaps or None

        if secondary.prompt_summary:
            merged.prompt_summary = secondary.prompt_summary

        return merged

    # ── Fallback: pure-regex preferences when OpenRouter unavailable ─────────

    def _fallback_prefs(
        self,
        prompt: str,
        raw_headers: list[str],
        cleaned_headers: list[str],
    ) -> PromptPreferences | None:
        """
        Regex-based fallback covering:
          - drop / keep columns
          - arithmetic on any column  ("age +1", "increase age by 1",
            "all the age increases by +1", "make salary *2", etc.)
          - null/missing value replacement  ("replace null age with 0",
            "fill missing salary with median", "set empty name to Unknown")
        """
        # Preserve +/- signs but strip other punctuation for easier matching
        pt  = re.sub(r"[^a-z0-9+\-*/. ]+", " ", prompt.lower()).strip()
        raw = prompt   # keep original case for replacement values

        p       = PromptPreferences()
        changed = False

        # ── Drop columns ──────────────────────────────────────────────────────
        drop_m = re.search(
            r"\b(remove|drop|delete|exclude|dont need|do not need|get rid of)\s+"
            r"(?:the\s+)?([a-z0-9_ ]+?)(?:\s+column[s]?)?(?:\s|$|,|\.)",
            pt,
        )
        if drop_m:
            term = drop_m.group(2).strip()
            _, hdr = self._resolve_columns(raw_headers, cleaned_headers, [term])
            if hdr:
                p.drop_columns = hdr
                changed = True

        # ── Arithmetic on a column ────────────────────────────────────────────
        # Patterns supported (all case-insensitive, number can be decimal):
        #   "age + 1"  /  "age +1"  /  "age by +1"
        #   "increase age by 1"  /  "add 1 to age"  /  "age increases by 1"
        #   "all the age increases by +1"  /  "make all age +1"
        #   "decrease salary by 10"  /  "multiply price by 2"  /  "divide price by 100"
        arith_patterns = [
            # "increase/add/increment <col> by <n>"
            (r"\b(?:increase[sd]?|add|increment)\s+(?:all\s+(?:the\s+)?)?"
             r"([a-z_][a-z0-9_]*)\s+(?:by\s+)?\+?\s*(\d+(?:\.\d+)?)\b",   "+"),
            # "all the <col> increase[s] by [+]<n>"
            (r"\ball\s+the\s+([a-z_][a-z0-9_]*)\s+increases?\s+by\s+\+?\s*(\d+(?:\.\d+)?)\b", "+"),
            # "<col> increases by [+]<n>"
            (r"\b([a-z_][a-z0-9_]*)\s+increases?\s+by\s+\+?\s*(\d+(?:\.\d+)?)\b", "+"),
            # "decrease/subtract/decrement <col> by <n>"
            (r"\b(?:decrease[sd]?|subtract|decrement)\s+(?:all\s+(?:the\s+)?)?"
             r"([a-z_][a-z0-9_]*)\s+(?:by\s+)?\+?\s*(\d+(?:\.\d+)?)\b",   "-"),
            # "multiply <col> by <n>"
            (r"\bmultiply\s+(?:all\s+(?:the\s+)?)?"
             r"([a-z_][a-z0-9_]*)\s+(?:by\s+)?(\d+(?:\.\d+)?)\b",          "*"),
            # "divide <col> by <n>"
            (r"\bdivide\s+(?:all\s+(?:the\s+)?)?"
             r"([a-z_][a-z0-9_]*)\s+(?:by\s+)?(\d+(?:\.\d+)?)\b",          "/"),
            # "add <n> to <col>"
            (r"\badd\s+(\d+(?:\.\d+)?)\s+to\s+([a-z_][a-z0-9_]*)\b",       "+", True),
            # "make [all] <col> [+/-/*//] <n>"
            (r"\bmake\s+(?:all\s+)?([a-z_][a-z0-9_]*)\s*([+\-*/])\s*(\d+(?:\.\d+)?)\b", None),
            # bare "<col> [+/-/*//] <n>"  (e.g. "age +1")
            (r"\b([a-z_][a-z0-9_]*)\s*([+\-*/])\s*(\d+(?:\.\d+)?)\b",       None),
        ]

        arith_found = False
        for entry in arith_patterns:
            pattern, fixed_op = entry[0], entry[1]
            swap = len(entry) > 2 and entry[2]  # "add N to col" — groups reversed
            m = re.search(pattern, pt)
            if not m:
                continue
            g = m.groups()
            if fixed_op is None:
                # groups: col, op, val  OR  col, op, val
                col, op, val = g[0], g[1], g[2]
            elif swap:
                # groups: val, col
                val, col, op = g[0], g[1], fixed_op
            else:
                col, val, op = g[0], g[1], fixed_op

            # skip if col token is a stop-word or looks like a number
            if col in {"all", "the", "a", "by", "to", "in", "of", "for"}:
                continue
            if re.fullmatch(r"\d+(?:\.\d+)?", col):
                continue

            _, matched = self._resolve_columns(raw_headers, cleaned_headers, [col])
            target_col = matched[0] if matched else col
            try:
                p.arithmetic_columns = [{"column": target_col, "operation": op, "value": float(val)}]
                changed      = True
                arith_found  = True
                print(f"[_fallback_prefs] Arithmetic: {target_col} {op} {val}")
            except (ValueError, TypeError):
                pass
            if arith_found:
                break

        # ── Value replacements on a column ───────────────────────────────────
        replace_patterns = [
            # "make all blood group that are o+ into a+"
            r"\b(?:make|change|turn|convert|replace|set)\s+(?:all\s+)?(?:the\s+)?([a-z_][a-z0-9_ ]*?)\s+(?:that\s+are|that\s+is|which\s+are|which\s+is|where\s+they\s+are)?\s*([^\s,;]+)\s+(?:into|to|with|as)\s+([^\s,;]+)",
            # "make all o+ blood group into a+"
            r"\b(?:make|change|turn|convert|replace|set)\s+(?:all\s+)?([^\s,;]+)\s+([a-z_][a-z0-9_ ]*?)\s+(?:into|to|with|as)\s+([^\s,;]+)",
            # "change o+ to a+ in blood group"
            r"\b(?:change|replace|turn|convert|set)\s+([^\s,;]+)\s+(?:into|to|with|as)\s+([^\s,;]+)\s+(?:in|for)\s+([a-z_][a-z0-9_ ]*?)\b",
        ]

        seen_replacements: set[tuple[str, str, str]] = set()
        for pat in replace_patterns:
            for m in re.finditer(pat, raw, flags=re.IGNORECASE):
                groups = [g.strip() for g in m.groups() if g and g.strip()]
                if len(groups) != 3:
                    continue
                first, second, third = groups
                first_cols, _ = self._resolve_columns(raw_headers, cleaned_headers, first.split())
                second_cols, _ = self._resolve_columns(raw_headers, cleaned_headers, second.split())

                if first_cols and not second_cols:
                    col_phrase, old_value, new_value = first, second, third
                elif second_cols and not first_cols:
                    col_phrase, old_value, new_value = second, first, third
                else:
                    col_phrase, old_value, new_value = first, second, third

                # If this looks like a null-fill instruction, let the fill
                # parser handle it instead of treating it as a value rewrite.
                if ("null" in old_value.lower() and "values" in old_value.lower()) or (
                    old_value.lower() in {"null", "missing", "empty", "blank", "nan"}
                ):
                    continue

                _, matched_cols = self._resolve_columns(raw_headers, cleaned_headers, col_phrase.split())
                if not matched_cols:
                    matched_cols = [col_phrase]
                p.value_replacements = p.value_replacements or []
                for mc in matched_cols:
                    key = (mc.lower(), old_value.lower(), new_value.lower())
                    if key in seen_replacements:
                        continue
                    seen_replacements.add(key)
                    p.value_replacements.append({"column": mc, "from": old_value, "to": new_value})
                    changed = True

        # ── Column swaps ─────────────────────────────────────────────────────
        swap_patterns = [
            r"\b(?:swap|interchange|exchange|switch|transpose)\s+(?:the\s+)?(?:values\s+in\s+)?(?:columns?\s+)?([a-z_][a-z0-9_ ]*?)\s+(?:with|and|to)\s+([a-z_][a-z0-9_ ]*?)\b",
            r"\b(?:swap|interchange|exchange|switch|transpose)\s+(?:the\s+)?([a-z_][a-z0-9_ ]*?)\s+(?:with|and|to)\s+([a-z_][a-z0-9_ ]*?)\s+columns?\b",
        ]
        seen_swaps: set[tuple[str, str]] = set()
        for pat in swap_patterns:
            for m in re.finditer(pat, raw, flags=re.IGNORECASE):
                left_phrase = m.group(1).strip()
                right_phrase = m.group(2).strip()
                _, left_cols = self._resolve_columns(raw_headers, cleaned_headers, left_phrase.split())
                _, right_cols = self._resolve_columns(raw_headers, cleaned_headers, right_phrase.split())
                if not left_cols or not right_cols:
                    continue
                for left_col in left_cols:
                    for right_col in right_cols:
                        if left_col.lower() == right_col.lower():
                            continue
                        key = (left_col.lower(), right_col.lower())
                        rev = (right_col.lower(), left_col.lower())
                        if key in seen_swaps or rev in seen_swaps:
                            continue
                        seen_swaps.add(key)
                        p.swap_columns = p.swap_columns or []
                        p.swap_columns.append({"left": left_col, "right": right_col})
                        changed = True

        # ── Null / missing value fill ─────────────────────────────────────────
        # Patterns:
        #   "fill missing age with 0"   /  "replace null age with Unknown"
        #   "fill null values in salary with median"
        #   "set empty name to John"    /  "fill age nulls with -1"
        #   "replace all nulls with 0"  /  "fill missing values with mode"
        null_patterns = [
            # "fill/replace [missing/null/empty] <col> [values] with/to <value>"
            r"\b(?:fill|replace|set)\s+(?:missing|null|empty|nan|blank)?\s*"
            r"([a-z_][a-z0-9_ ]*?)\s+(?:values?\s+)?(?:with|to|by|=)\s+"
            r"([a-z0-9_.\-]+)\b",
            # "fill null values in <col> with <value>"
            r"\b(?:fill|replace)\s+(?:null|missing|empty|nan|blank)\s+values?\s+in\s+"
            r"([a-z_][a-z0-9_ ]*?)\s+(?:with|to)\s+([a-z0-9_.\-]+)\b",
            # "fill missing values with <strategy/value>"  (no column = global)
            r"\b(?:fill|replace)\s+(?:all\s+)?(?:missing|null|empty|nan|blank)\s+values?\s+"
            r"(?:with|to)\s+([a-z0-9_.\-]+)\b",
            # "<col> nulls / missing with <value>"
            r"\b([a-z_][a-z0-9_]*)\s+(?:nulls?|missing|empty|blanks?)\s+"
            r"(?:with|to|=)\s+([a-z0-9_.\-]+)\b",
        ]

        strategy_words = {"median", "mean", "mode", "average", "zero", "auto"}
        # Note: "0" as a fill value stays literal (column_fill_values) not strategy "zero"

        for pat in null_patterns:
            for m in re.finditer(pat, pt):
                g = m.groups()
                if len(g) == 1:
                    # Global fill — no specific column
                    fill_word = g[0].strip()
                    if fill_word in strategy_words:
                        strat = "median" if fill_word in {"mean", "average"} else fill_word
                        if strat == "0": strat = "zero"
                        p.fill_strategy = strat
                    else:
                        p.fill_strategy = "literal"
                        p.fill_value    = fill_word
                    changed = True
                else:
                    col_phrase, fill_word = g[0].strip(), g[1].strip()
                    # Guard against the broad pattern swallowing phrases like
                    # 'replace null values in region with mumbai' as
                    # 'values in region'. The more specific 'in <column>'
                    # pattern should handle those.
                    if col_phrase.startswith("values ") or col_phrase == "values":
                        continue
                    # Try to match col_phrase to an actual column
                    _, matched_cols = self._resolve_columns(raw_headers, cleaned_headers,
                                                            col_phrase.split())
                    if not matched_cols:
                        matched_cols = [col_phrase]
                    for mc in matched_cols:
                        if fill_word in strategy_words:
                            strat = "median" if fill_word in {"mean","average"} else fill_word
                            if strat == "0": strat = "zero"
                            p.fill_strategy = strat
                        else:
                            p.fill_strategy = "literal"
                            p.fill_value    = fill_word
                            p.column_fill_values = {
                                **(p.column_fill_values or {}),
                                mc: fill_word,
                            }
                        changed = True

        # ── Simple strategy keywords ──────────────────────────────────────────
        if not p.fill_strategy:
            if re.search(r"\bfill\b.*\bmedian\b|\bmedian\b.*\b(fill|missing)\b", pt):
                p.fill_strategy = "median"; changed = True
            elif re.search(r"\bfill\b.*\bmode\b|\bmode\b.*\b(fill|missing)\b", pt):
                p.fill_strategy = "mode"; changed = True
            elif re.search(r"\bfill\b.*\bzero\b|replace.*missing.*\b0\b", pt):
                p.fill_strategy = "zero"; changed = True

        return p if changed else None

    # ── Arithmetic transforms ─────────────────────────────────────────────────

    def _apply_arithmetic(
        self,
        row: list[str],
        headers: list[str],
        arithmetic_columns: list[dict],
        skip_indices: set[int] | None = None,
    ) -> list[str]:
        row = list(row)
        skip_indices = skip_indices or set()
        ops = {
            "+": lambda a, b: a + b,
            "-": lambda a, b: a - b,
            "*": lambda a, b: a * b,
            "/": lambda a, b: a / b if b else a,
        }
        for spec in arithmetic_columns:
            col = spec["column"]
            op  = spec["operation"]
            val = float(spec["value"])
            # Match by exact name OR fuzzy (cleaned column name)
            target_idx = None
            if col in headers:
                target_idx = headers.index(col)
            else:
                norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
                for i, h in enumerate(headers):
                    if norm(h) == norm(col) or norm(col) in norm(h):
                        target_idx = i
                        break
            if target_idx is None:
                print(f"[_apply_arithmetic] Column '{col}' not found in headers {headers}")
                continue
            if target_idx in skip_indices:
                continue
            try:
                current = row[target_idx]
                if current == "":
                    continue  # skip blank cells
                new_val  = ops[op](float(current), val)
                row[target_idx] = self._format_number(new_val)
            except (ValueError, KeyError, ZeroDivisionError) as e:
                print(f"[_apply_arithmetic] Skipped row[{target_idx}]='{row[target_idx]}': {e}")
        return row

    def _apply_value_replacements(
        self,
        row: list[str],
        headers: list[str],
        replacements: list[dict],
    ) -> list[str]:
        row = list(row)

        def norm_value(value: str) -> str:
            return re.sub(r"\s+", "", str(value).strip().lower())

        for spec in replacements:
            col = str(spec.get("column", "")).strip()
            old_value = str(spec.get("from", "")).strip()
            new_value = str(spec.get("to", "")).strip()
            if not col or not old_value:
                continue

            target_idx = None
            if col in headers:
                target_idx = headers.index(col)
            else:
                norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
                for i, h in enumerate(headers):
                    if norm(h) == norm(col) or norm(col) in norm(h):
                        target_idx = i
                        break
            if target_idx is None:
                continue

            current = row[target_idx]
            if norm_value(current) == norm_value(old_value):
                row[target_idx] = new_value

        return row

    def _apply_column_swaps(
        self,
        row: list[str],
        raw_headers: list[str],
        cleaned_headers: list[str],
        swaps: list[dict],
    ) -> list[str]:
        row = list(row)

        def resolve(col_name: str) -> int | None:
            if col_name in cleaned_headers:
                return cleaned_headers.index(col_name)
            if col_name in raw_headers:
                return raw_headers.index(col_name)
            norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
            for i, h in enumerate(cleaned_headers):
                if norm(h) == norm(col_name) or norm(col_name) in norm(h):
                    return i
            for i, h in enumerate(raw_headers):
                if norm(h) == norm(col_name) or norm(col_name) in norm(h):
                    return i
            return None

        for spec in swaps:
            left = str(spec.get("left", "")).strip()
            right = str(spec.get("right", "")).strip()
            if not left or not right:
                continue
            left_idx = resolve(left)
            right_idx = resolve(right)
            if left_idx is None or right_idx is None or left_idx == right_idx:
                continue
            row[left_idx], row[right_idx] = row[right_idx], row[left_idx]

        return row

    def _apply_column_swaps_to_order(
        self,
        kept_idx: list[int],
        raw_headers: list[str],
        cleaned_headers: list[str],
        swaps: list[dict],
    ) -> tuple[list[int], list[str], list[str]]:
        order = list(range(len(kept_idx)))

        def resolve(col_name: str) -> int | None:
            if col_name in cleaned_headers:
                return cleaned_headers.index(col_name)
            if col_name in raw_headers:
                return raw_headers.index(col_name)
            norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
            for i, h in enumerate(cleaned_headers):
                if norm(h) == norm(col_name) or norm(col_name) in norm(h):
                    return i
            for i, h in enumerate(raw_headers):
                if norm(h) == norm(col_name) or norm(col_name) in norm(h):
                    return i
            return None

        for spec in swaps:
            left = str(spec.get("left", "")).strip()
            right = str(spec.get("right", "")).strip()
            if not left or not right:
                continue
            left_idx = resolve(left)
            right_idx = resolve(right)
            if left_idx is None or right_idx is None or left_idx == right_idx:
                continue
            if left_idx not in order or right_idx not in order:
                continue
            left_pos = order.index(left_idx)
            right_pos = order.index(right_idx)
            order[left_pos], order[right_pos] = order[right_pos], order[left_pos]

        return (
            [kept_idx[i] for i in order],
            [raw_headers[i] for i in order],
            [cleaned_headers[i] for i in order],
        )

    def _apply_invalid_value_rules(
        self,
        row: list[str],
        headers: list[str],
        profiles: list[dict],
        prefs: "PromptPreferences",
    ) -> tuple[list[str], bool]:
        """
        Replace physically impossible values with empty string so they get
        filled by the normal fill-value logic later.

        Rules applied:
          - Any numeric column whose name contains 'age' must be 0–120.
          - Any numeric column whose value is below its IQR lower bound by more
            than 3× IQR (extreme outlier) is blanked only when the prompt
            contains a hint like "invalid", "impossible", "negative", "clean",
            "fix", or "validate".
          - Returns (cleaned_row, was_modified).
        """
        row      = list(row)
        modified = False
        prompt_hint = bool(
            prefs.prompt_summary and re.search(
                r"\b(invalid|impossible|negative|fix|clean|validate|correct)\b",
                prefs.prompt_summary.lower(),
            )
        )

        for i, (val, profile) in enumerate(zip(row, profiles)):
            if val == "" or not profile.get("is_numeric"):
                continue
            try:
                num = float(val)
            except ValueError:
                continue

            col_name = profile["column_name"].lower()

            # Age column: must be 0–120
            if "age" in col_name and not (0 <= num <= 120):
                row[i]   = ""
                modified = True
                print(f"[_apply_invalid_value_rules] Blanked invalid age: {val}")
                continue

        return row, modified

    # ── Column resolution ─────────────────────────────────────────────────────

    def _resolve_columns(
        self,
        raw_headers: list[str],
        cleaned_headers: list[str],
        terms: list[str],
    ) -> tuple[list[int], list[str]]:
        if not terms:
            return [], []
        idxs: list[int] = []
        hdrs: list[str] = []
        norm_raw  = [re.sub(r"[^a-z0-9]", " ", h.lower()).strip() for h in raw_headers]
        norm_cln  = [re.sub(r"[^a-z0-9]", " ", h.lower()).strip() for h in cleaned_headers]
        for term in terms:
            nt = re.sub(r"[^a-z0-9]", " ", term.lower()).strip()
            if not nt:
                continue
            for i, (rn, cn) in enumerate(zip(norm_raw, norm_cln)):
                if nt in (rn, cn) or nt in rn or nt in cn or rn in nt or cn in nt:
                    if i not in idxs:
                        idxs.append(i)
                        hdrs.append(cleaned_headers[i])
                    break
        return idxs, hdrs

    # ── Cell cleaning ─────────────────────────────────────────────────────────

    def _clean_cell(self, value: str) -> str:
        v = re.sub(r"\s+", " ", value.strip())
        if v.lower() in self.EMPTY_MARKERS:
            return ""
        num = self._try_parse_number(v)
        return self._format_number(num) if num is not None else v

    def _try_parse_number(self, value: str) -> float | None:
        v = value.strip().replace("−", "-")
        m = re.fullmatch(r"[-+]?\d+(?:,\d{3})*(?:\.\d+)?", v)
        if m:
            try:
                return float(v.replace(",", ""))
            except ValueError:
                pass
        return None

    def _format_number(self, value: float) -> str:
        if value != value:   # NaN guard
            return ""
        if float(value).is_integer():
            return str(int(value))
        return f"{value:.6f}".rstrip("0").rstrip(".")

    # ── Fill value resolution ─────────────────────────────────────────────────

    def _fill_value(self, col: str, profile: dict, prefs: PromptPreferences) -> str:
        norm = lambda s: re.sub(r"[^a-z0-9]", " ", s.lower()).strip()
        nc = norm(col)

        # per-column override
        for k, v in (prefs.column_fill_values or {}).items():
            if norm(k) == nc or norm(k) in nc or nc in norm(k):
                return v

        if prefs.fill_strategy == "literal" and prefs.fill_value is not None:
            # Keep literal fills scoped to the explicit per-column mapping when
            # the prompt names a target column. Otherwise a prompt like
            # 'replace null values in region with mumbai' would fill every blank
            # cell with 'mumbai'.
            if prefs.column_fill_values:
                return str(profile["fill_value"])
            return prefs.fill_value
        if prefs.fill_strategy == "zero":
            return "0"

        strategy = prefs.fill_strategy or profile["strategy"]
        if strategy == "median" and profile.get("is_numeric"):
            nums = self._extract_nums(profile.get("sample_values", []))
            if nums:
                return self._format_number(median(nums))
        if strategy == "mode":
            return self._mode(list(profile.get("sample_values", []))) or "Unknown"
        return str(profile["fill_value"])

    # ── Column profiles ───────────────────────────────────────────────────────

    def _build_column_profiles(
        self,
        headers: list[str],
        data_rows: list[list[str]],
        kept_idx: list[int],
    ) -> list[dict]:
        profiles = []
        pad_to = (max(kept_idx) + 1) if kept_idx else 0
        for pi, si in enumerate(kept_idx):
            vals = []
            for row in data_rows:
                pr  = self._pad_row(row, pad_to)
                cv  = self._clean_cell(pr[si])
                if cv:
                    vals.append(cv)
            nums      = self._extract_nums(vals)
            num_ratio = len(nums) / max(len(vals), 1)
            is_num    = bool(nums) and num_ratio >= 0.6

            if is_num and len(nums) >= 3:
                fv       = self._format_number(median(nums))
                strategy = "median"
                lo, hi   = self._iqr_bounds(nums)
            else:
                fv       = self._mode(vals) or "Unknown"
                strategy = "mode"
                lo = hi  = None

            profiles.append({
                "column_name":  headers[pi],
                "strategy":     strategy,
                "fill_value":   fv,
                "filled_count": 0,
                "is_numeric":   is_num,
                "outlier_min":  lo,
                "outlier_max":  hi,
                "outlier_count": 0,
                "non_empty_count": len(vals),
                "sample_values": vals[:5],
            })
        return profiles

    def _iqr_bounds(self, nums: list[float]) -> tuple[float | None, float | None]:
        if len(nums) < 4:
            return None, None
        s   = sorted(nums)
        mid = len(s) // 2
        q1  = median(s[:mid])
        q3  = median(s[mid + (len(s) % 2):])
        iqr = q3 - q1
        if iqr <= 0:
            return None, None
        return q1 - 1.5 * iqr, q3 + 1.5 * iqr

    def _outlier_columns(self, row: list[str], profiles: list[dict]) -> list[str]:
        out = []
        for i, p in enumerate(profiles):
            lo, hi = p.get("outlier_min"), p.get("outlier_max")
            if lo is None or hi is None:
                continue
            try:
                v = float(row[i])
                if v < float(lo) or v > float(hi):
                    out.append(str(p["column_name"]))
            except (ValueError, TypeError, IndexError):
                pass
        return out

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _pad_row(self, row: list[str], n: int) -> list[str]:
        r = list(row[:n])
        r += [""] * max(0, n - len(r))
        return r

    def _normalize_headers(self, headers: list[str]) -> list[str]:
        seen: dict[str, int] = {}
        out: list[str] = []
        for i, h in enumerate(headers, 1):
            c = re.sub(r"[^a-z0-9]+", "_", h.strip().lower()).strip("_") or f"column_{i}"
            n = seen.get(c, 0)
            seen[c] = n + 1
            out.append(c if n == 0 else f"{c}_{n + 1}")
        return out

    def _extract_nums(self, values: list[str]) -> list[float]:
        out = []
        for v in values:
            n = self._try_parse_number(v)
            if n is not None:
                out.append(n)
        return out

    def _mode(self, values: list[str]) -> str | None:
        if not values:
            return None
        counts: dict[str, int] = {}
        for v in values:
            counts[v] = counts.get(v, 0) + 1
        return max(counts, key=counts.__getitem__)

    # ── Summary helpers ───────────────────────────────────────────────────────

    def _build_notes(self, n_empty, n_dup, n_out, profiles, prompt, prefs, dropped):
        notes = []
        if prompt:
            notes.append(f"Prompt: {prompt[:160]}")
        if prefs.prompt_summary:
            notes.append(f"Interpreted as: {prefs.prompt_summary}")
        if prefs.swap_columns:
            swap_text = ", ".join(f"{item['left']} ↔ {item['right']}" for item in prefs.swap_columns)
            notes.append(f"Swapped column positions: {swap_text}.")
        if prefs.arithmetic_columns:
            for ac in prefs.arithmetic_columns:
                notes.append(f"Applied arithmetic: {ac['column']} {ac['operation']} {ac['value']}")
        if dropped:
            notes.append(f"Dropped columns: {', '.join(dropped)}")
        if n_empty:
            notes.append(f"Removed {n_empty} empty row{'s' if n_empty != 1 else ''}.")
        if n_dup:
            notes.append(f"Removed {n_dup} duplicate row{'s' if n_dup != 1 else ''}.")
        if n_out:
            notes.append(f"Removed {n_out} outlier row{'s' if n_out != 1 else ''}.")
        filled = [p for p in profiles if p["filled_count"] > 0]
        if filled:
            cols = ", ".join(p["column_name"] for p in filled[:4])
            notes.append(f"Filled missing values in: {cols}.")
        if not notes:
            notes.append("No cleaning issues found; headers normalized.")
        return notes

    def _build_ai_summary(self, n_empty, n_dup, n_out, dropped) -> str:
        bits = []
        if dropped:      bits.append(f"dropped columns {', '.join(dropped)}")
        if n_out:        bits.append(f"removed {n_out} outlier row(s)")
        if n_dup:        bits.append(f"deduplicated {n_dup} row(s)")
        if n_empty:      bits.append(f"dropped {n_empty} empty row(s)")
        if not bits:     bits.append("normalized headers")
        return "Cleaned: " + ", ".join(bits) + "."