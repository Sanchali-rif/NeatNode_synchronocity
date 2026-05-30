from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from statistics import mean, median
from typing import Any


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


@dataclass
class Condition:
    column: str
    operator: str
    value: str
    value_end: str | None = None


class DataQueryAssistant:
    STOPWORDS = {
        "a",
        "an",
        "and",
        "are",
        "be",
        "by",
        "for",
        "from",
        "give",
        "how",
        "in",
        "is",
        "list",
        "many",
        "me",
        "of",
        "on",
        "rows",
        "show",
        "the",
        "that",
        "this",
        "to",
        "top",
        "what",
        "where",
        "with",
        "which",
    }

    def answer(self, question: str, headers: list[str], rows: list[list[str]]) -> QueryResult:
        question = (question or "").strip()
        normalized_question = self._normalize(question).replace("_", " ")
        question_lower = question.lower()
        records = self._to_records(headers, rows)
        row_limit = self._extract_limit(question) 

        if not question:
            return QueryResult(
                question=question,
                intent="help",
                title="Ask a question about the cleaned CSV",
                summary="Type a natural-language query and I will apply it to the cleaned data.",
                sql_like="SELECT * FROM cleaned_data ;",
                matched_row_count=len(records),
                total_row_count=len(records),
                table_headers=["Tip", "Use a question like"],
                table_rows=[["Count rows", "How many rows are in the file?"], ["Filter rows", "Show rows where a column contains a value."]],
            )

        conditions = self._extract_conditions(question, headers)
        filter_sql = self._build_where_sql(conditions)
        filtered_records = self._apply_conditions(records, conditions)

        intent = self._detect_intent(question_lower)
        target_column = self._choose_target_column(question, headers, records)

        if intent == "count":
            matched = len(filtered_records)
            table_headers = ["Metric", "Value"]
            table_rows = [["Matching rows", str(matched)]]
            summary = f"Found {matched} matching row{'s' if matched != 1 else ''}."
            sql_like = f"SELECT COUNT(*) AS matching_rows FROM cleaned_data{filter_sql};"
            return QueryResult(
                question=question,
                intent=intent,
                title="Row count",
                summary=summary,
                sql_like=sql_like,
                matched_row_count=matched,
                total_row_count=len(records),
                table_headers=table_headers,
                table_rows=table_rows,
                detail_lines=self._detail_lines_for_filters(conditions),
            )

        if intent in {"average", "sum", "min", "max", "median"}:
            numeric_column = self._choose_numeric_column(question, headers, records, target_column)
            if not numeric_column:
                return self._fallback_answer(question, headers, records, filtered_records, row_limit)

            numeric_values = self._extract_numeric_values([row.get(numeric_column, "") for row in filtered_records])
            if not numeric_values:
                return self._fallback_answer(question, headers, records, filtered_records, row_limit)

            value, label = self._calculate_aggregate(intent, numeric_values)
            summary = f"{label} for {numeric_column} is {value}."
            sql_like = f"SELECT {label.upper()}(\"{numeric_column}\") AS result FROM cleaned_data{filter_sql};"
            return QueryResult(
                question=question,
                intent=intent,
                title=f"{label.title()} result",
                summary=summary,
                sql_like=sql_like,
                matched_row_count=len(filtered_records),
                total_row_count=len(records),
                table_headers=["Metric", "Value"],
                table_rows=[[f"{label.title()} {numeric_column}", value]],
                detail_lines=self._detail_lines_for_filters(conditions),
            )

        if intent == "distinct":
            distinct_column = self._choose_target_column(question, headers, records)
            if not distinct_column:
                return self._fallback_answer(question, headers, records, filtered_records, row_limit)

            unique_values = self._distinct_values(filtered_records, distinct_column, row_limit)
            summary = f"Found {len(unique_values)} unique value{'s' if len(unique_values) != 1 else ''} in {distinct_column}."
            sql_like = f"SELECT DISTINCT \"{distinct_column}\" FROM cleaned_data{filter_sql} LIMIT {row_limit};"
            return QueryResult(
                question=question,
                intent=intent,
                title=f"Distinct values in {distinct_column}",
                summary=summary,
                sql_like=sql_like,
                matched_row_count=len(filtered_records),
                total_row_count=len(records),
                table_headers=[distinct_column],
                table_rows=[[value] for value in unique_values],
                detail_lines=self._detail_lines_for_filters(conditions),
            )

        if intent == "rows" or conditions:
            result_rows = self._preview_rows(filtered_records, headers, row_limit)
            summary = f"Showing {len(result_rows)} row{'s' if len(result_rows) != 1 else ''} out of {len(filtered_records)} matched row{'s' if len(filtered_records) != 1 else ''}."
            sql_like = f"SELECT * FROM cleaned_data{filter_sql} LIMIT {row_limit};"
            return QueryResult(
                question=question,
                intent="rows",
                title="Filtered rows",
                summary=summary,
                sql_like=sql_like,
                matched_row_count=len(filtered_records),
                total_row_count=len(records),
                table_headers=headers,
                table_rows=result_rows,
                detail_lines=self._detail_lines_for_filters(conditions),
            )

        keyword_filtered = self._keyword_filter(records, question)
        if keyword_filtered:
            result_rows = self._preview_rows(keyword_filtered, headers, row_limit)
            matched_count = len(keyword_filtered)
            summary = f"I found {matched_count} row{'s' if matched_count != 1 else ''} that match the words in your question."
            sql_like = f"SELECT * FROM cleaned_data WHERE <keyword match> LIMIT {row_limit};"
            return QueryResult(
                question=question,
                intent="keyword",
                title="Keyword match",
                summary=summary,
                sql_like=sql_like,
                matched_row_count=matched_count,
                total_row_count=len(records),
                table_headers=headers,
                table_rows=result_rows,
                detail_lines=["No structured filter was detected, so I matched the important words across every column."],
            )

        return self._fallback_answer(question, headers, records, filtered_records, row_limit)

    def _fallback_answer(
        self,
        question: str,
        headers: list[str],
        records: list[dict[str, str]],
        filtered_records: list[dict[str, str]],
        row_limit: int,
    ) -> QueryResult:
        preview_rows = self._preview_rows(records, headers, row_limit)
        return QueryResult(
            question=question,
            intent="help",
            title="I need a clearer query",
            summary="I can count rows, calculate numeric summaries, list distinct values, and filter rows using any column name in the file.",
            sql_like="SELECT * FROM cleaned_data ;",
            matched_row_count=len(filtered_records) if filtered_records else len(records),
            total_row_count=len(records),
            table_headers=headers,
            table_rows=preview_rows,
            detail_lines=[f"Available columns: {', '.join(headers)}" if headers else "No columns detected."],
        )

    def _to_records(self, headers: list[str], rows: list[list[str]]) -> list[dict[str, str]]:
        records: list[dict[str, str]] = []
        for row in rows:
            padded_row = list(row) + [""] * max(0, len(headers) - len(row))
            records.append({header: padded_row[index] if index < len(padded_row) else "" for index, header in enumerate(headers)})
        return records

    def _extract_limit(self, question: str) -> int | None:
        match = re.search(r"\b(?:top|first|limit)\s+(\d+)\b", question.lower())
        if match:
            value = int(match.group(1))
            return value if value > 0 else None
        return None

    def _detect_intent(self, question_lower: str) -> str:
        if any(keyword in question_lower for keyword in ["how many", "count rows", "number of rows", "row count", "how much"]):
            return "count"
        if any(keyword in question_lower for keyword in ["average", "mean"]):
            return "average"
        if any(keyword in question_lower for keyword in ["sum", "total of", "total"]):
            return "sum"
        if any(keyword in question_lower for keyword in ["minimum", "lowest", "smallest", "min "]):
            return "min"
        if any(keyword in question_lower for keyword in ["maximum", "highest", "largest", "max "]):
            return "max"
        if any(keyword in question_lower for keyword in ["median"]):
            return "median"
        if any(keyword in question_lower for keyword in ["distinct", "unique", "different values"]):
            return "distinct"
        if any(keyword in question_lower for keyword in ["show", "display", "list", "rows where", "find rows", "filter", "where"]):
            return "rows"
        return "help" if not question_lower.strip() else "rows"

    def _choose_target_column(self, question: str, headers: list[str], records: list[dict[str, str]]) -> str | None:
        if not headers:
            return None

        lower_question = question.lower()
        direct_matches = [header for header in headers if self._header_matches_question(header, lower_question)]
        if direct_matches:
            return direct_matches[0]

        scored_headers = sorted(headers, key=lambda header: self._header_score(header, lower_question), reverse=True)
        best_header = scored_headers[0]
        if self._header_score(best_header, lower_question) >= 0.35:
            return best_header

        if len(self._numeric_columns(headers, records)) == 1:
            return self._numeric_columns(headers, records)[0]

        return None

    def _choose_numeric_column(self, question: str, headers: list[str], records: list[dict[str, str]], preferred: str | None = None) -> str | None:
        numeric_columns = self._numeric_columns(headers, records)
        if preferred and preferred in numeric_columns:
            return preferred

        if preferred:
            maybe = self._best_numeric_match(preferred, numeric_columns)
            if maybe:
                return maybe

        direct_matches = [header for header in numeric_columns if self._header_matches_question(header, question.lower())]
        if direct_matches:
            return direct_matches[0]

        if len(numeric_columns) == 1:
            return numeric_columns[0]

        if numeric_columns:
            return numeric_columns[0]

        return None

    def _best_numeric_match(self, preferred: str, numeric_columns: list[str]) -> str | None:
        preferred_norm = self._normalize(preferred)
        for column in numeric_columns:
            if self._normalize(column) == preferred_norm:
                return column
        return None

    def _numeric_columns(self, headers: list[str], records: list[dict[str, str]]) -> list[str]:
        numeric_columns: list[str] = []
        for header in headers:
            values = [row.get(header, "") for row in records if row.get(header, "") != ""]
            if not values:
                continue
            numeric_values = self._extract_numeric_values(values)
            if numeric_values and len(numeric_values) >= max(1, len(values) // 2):
                numeric_columns.append(header)
        return numeric_columns

    def _extract_conditions(self, question: str, headers: list[str]) -> list[Condition]:
        conditions: list[Condition] = []
        question_lower = question.lower()

        for header in headers:
            header_pattern = self._header_pattern(header)
            numeric_patterns = [
                (rf"{header_pattern}\s*(?:is\s*)?(?:>=|greater than or equal to|at least|no less than)\s*(-?\d+(?:\.\d+)?)", ">=", None),
                (rf"{header_pattern}\s*(?:is\s*)?(?:<=|less than or equal to|at most|no more than)\s*(-?\d+(?:\.\d+)?)", "<=", None),
                (rf"{header_pattern}\s*(?:is\s*)?(?:>|greater than|more than|above|over)\s*(-?\d+(?:\.\d+)?)", ">", None),
                (rf"{header_pattern}\s*(?:is\s*)?(?:<|less than|below|under)\s*(-?\d+(?:\.\d+)?)", "<", None),
                (rf"{header_pattern}\s*(?:is\s*)?between\s*(-?\d+(?:\.\d+)?)\s+and\s+(-?\d+(?:\.\d+)?)", "between", None),
                (rf"{header_pattern}\s*(?:is\s*)?(?:=|==|equals?|equal to)\s*(['\"]?)([^'\"\n,;]+?)\1(?=$|\s+(?:and|or|where|with|on|then|$))", "=", None),
            ]
            for pattern, operator, _ in numeric_patterns:
                for match in re.finditer(pattern, question_lower):
                    if operator == "between":
                        conditions.append(Condition(column=header, operator=operator, value=match.group(1), value_end=match.group(2)))
                    elif operator == "=":
                        conditions.append(Condition(column=header, operator=operator, value=match.group(2).strip()))
                    else:
                        conditions.append(Condition(column=header, operator=operator, value=match.group(1)))

            text_patterns = [
                (rf"{header_pattern}\s*(?:contains|includes|has)\s+([a-z0-9_\-\s]+?)(?=$|\s+(?:and|or|where|with|on|then|limit|top|first)\b|[.,;])", "contains"),
                (rf"{header_pattern}\s*(?:starts with|begins with)\s+([a-z0-9_\-\s]+?)(?=$|\s+(?:and|or|where|with|on|then|limit|top|first)\b|[.,;])", "startswith"),
                (rf"{header_pattern}\s*(?:ends with)\s+([a-z0-9_\-\s]+?)(?=$|\s+(?:and|or|where|with|on|then|limit|top|first)\b|[.,;])", "endswith"),
            ]
            for pattern, operator in text_patterns:
                for match in re.finditer(pattern, question_lower):
                    conditions.append(Condition(column=header, operator=operator, value=match.group(1).strip()))

        if not conditions:
            numeric_literal = re.search(r"-?\d+(?:\.\d+)?", question_lower)
            comparative_word = re.search(r"(?:greater than|more than|above|over|less than|below|under|at least|at most)", question_lower)
            if numeric_literal and comparative_word:
                best_column = None
                best_score = 0.0
                for header in headers:
                    score = self._header_score(header, question_lower)
                    if score > best_score:
                        best_column = header
                        best_score = score
                if best_column and best_score >= 0.3:
                    operator_map = {
                        "greater than": ">",
                        "more than": ">",
                        "above": ">",
                        "over": ">",
                        "less than": "<",
                        "below": "<",
                        "under": "<",
                        "at least": ">=",
                        "at most": "<=",
                    }
                    operator = next((symbol for phrase, symbol in operator_map.items() if phrase in question_lower), "=")
                    conditions.append(Condition(column=best_column, operator=operator, value=numeric_literal.group(0)))

        return conditions

    def _apply_conditions(self, records: list[dict[str, str]], conditions: list[Condition]) -> list[dict[str, str]]:
        if not conditions:
            return list(records)

        matched_records: list[dict[str, str]] = []
        for record in records:
            if all(self._matches_condition(record, condition) for condition in conditions):
                matched_records.append(record)
        return matched_records

    def _matches_condition(self, record: dict[str, str], condition: Condition) -> bool:
        value = record.get(condition.column, "")
        if condition.operator in {">", ">=", "<", "<=", "between"}:
            try:
                numeric_value = float(value)
            except ValueError:
                return False

            target = float(condition.value)
            if condition.operator == ">":
                return numeric_value > target
            if condition.operator == ">=":
                return numeric_value >= target
            if condition.operator == "<":
                return numeric_value < target
            if condition.operator == "<=":
                return numeric_value <= target
            if condition.operator == "between" and condition.value_end is not None:
                upper = float(condition.value_end)
                return target <= numeric_value <= upper

        haystack = value.lower()
        needle = condition.value.lower()
        if condition.operator == "contains":
            return needle in haystack
        if condition.operator == "startswith":
            return haystack.startswith(needle)
        if condition.operator == "endswith":
            return haystack.endswith(needle)
        if condition.operator == "=":
            return haystack == needle

        return False

    def _keyword_filter(self, records: list[dict[str, str]], question: str) -> list[dict[str, str]]:
        tokens = [token for token in self._normalize(question).split() if token and token not in self.STOPWORDS]
        if not tokens:
            return []

        matched_records: list[dict[str, str]] = []
        for record in records:
            haystack = " ".join(record.values()).lower()
            if all(token in haystack for token in tokens):
                matched_records.append(record)
        return matched_records

    def _distinct_values(self, records: list[dict[str, str]], column: str, limit: int) -> list[str]:
        seen: list[str] = []
        for record in records:
            value = record.get(column, "").strip()
            if value and value not in seen:
                seen.append(value)
            if len(seen) >= limit:
                break
        return seen

    def _preview_rows(self, records: list[dict[str, str]], headers: list[str], limit: int) -> list[list[str]]:
        rows: list[list[str]] = []
        for record in records[:limit]:
            rows.append([record.get(header, "") for header in headers])
        return rows

    def _calculate_aggregate(self, intent: str, values: list[float]) -> tuple[str, str]:
        if intent == "average":
            return self._format_number(mean(values)), "average"
        if intent == "sum":
            return self._format_number(sum(values)), "sum"
        if intent == "min":
            return self._format_number(min(values)), "minimum"
        if intent == "max":
            return self._format_number(max(values)), "maximum"
        if intent == "median":
            return self._format_number(median(values)), "median"
        return self._format_number(sum(values)), "sum"

    def _detail_lines_for_filters(self, conditions: list[Condition]) -> list[str]:
        if not conditions:
            return []

        details: list[str] = []
        for condition in conditions:
            if condition.operator == "between" and condition.value_end is not None:
                details.append(f"{condition.column} between {condition.value} and {condition.value_end}")
            elif condition.operator in {">", ">=", "<", "<=", "="}:
                details.append(f"{condition.column} {condition.operator} {condition.value}")
            else:
                details.append(f"{condition.column} {condition.operator} {condition.value}")
        return details

    def _build_where_sql(self, conditions: list[Condition]) -> str:
        if not conditions:
            return ""

        clauses: list[str] = []
        for condition in conditions:
            column_sql = f'"{condition.column}"'
            if condition.operator == "between" and condition.value_end is not None:
                clauses.append(f"{column_sql} BETWEEN {condition.value} AND {condition.value_end}")
            elif condition.operator in {">", ">=", "<", "<="}:
                clauses.append(f"{column_sql} {condition.operator} {condition.value}")
            elif condition.operator == "=":
                safe_value = condition.value.replace("'", "''")
                clauses.append(f"{column_sql} = '{safe_value}'")
            elif condition.operator == "contains":
                clauses.append(f"LOWER({column_sql}) LIKE '%{condition.value.lower()}%'")
            elif condition.operator == "startswith":
                clauses.append(f"LOWER({column_sql}) LIKE '{condition.value.lower()}%'")
            elif condition.operator == "endswith":
                clauses.append(f"LOWER({column_sql}) LIKE '%{condition.value.lower()}'")

        if not clauses:
            return ""
        return " WHERE " + " AND ".join(clauses)

    def _header_matches_question(self, header: str, question: str) -> bool:
        header_pattern = self._header_pattern(header)
        return bool(re.search(header_pattern, question))

    def _header_score(self, header: str, question: str) -> float:
        header_tokens = self._normalize(header).split("_")
        question_tokens = set(self._normalize(question).split("_") + self._normalize(question).split())
        if not header_tokens:
            return 0.0

        overlap = sum(1 for token in header_tokens if token and token in question_tokens)
        if overlap == len(header_tokens):
            return 1.0
        return overlap / len(header_tokens)

    def _header_pattern(self, header: str) -> str:
        normalized = self._normalize(header).replace("_", " ").strip()
        if not normalized:
            return r""
        return r"\b" + r"[\s_\-]+".join(re.escape(part) for part in normalized.split()) + r"\b"

    def _normalize(self, text: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")

    def _extract_numeric_values(self, values: list[str]) -> list[float]:
        numeric_values: list[float] = []
        for value in values:
            try:
                numeric_values.append(float(value))
            except ValueError:
                return []
        return numeric_values

    def _format_number(self, value: float) -> str:
        if value.is_integer():
            return str(int(value))
        return ("{:.6f}".format(value)).rstrip("0").rstrip(".")

    def _to_table_rows(self, result: QueryResult) -> list[list[str]]:
        return result.table_rows