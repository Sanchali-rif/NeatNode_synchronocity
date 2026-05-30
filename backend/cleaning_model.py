import csv
import io
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from statistics import median
from typing import Any


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


@dataclass
class PromptPreferences:
    remove_empty_rows: bool = True
    remove_duplicate_rows: bool = True
    remove_outlier_rows: bool = True
    fill_strategy: str | None = None
    fill_value: str | None = None
    treat_missing_as_blank: bool = True
    drop_columns: list[str] | None = None
    keep_columns: list[str] | None = None
    prompt_summary: str | None = None


class CSVCleaningModel:
    EMPTY_MARKERS = {"", "na", "n/a", "null", "none", "-", "--"}

    def clean_upload(self, file_storage, prompt: str | None = None) -> CleaningSummary:
        stream = io.TextIOWrapper(file_storage.stream, encoding="utf-8-sig", newline="")
        reader = csv.reader(stream)
        rows = list(reader)

        if not rows:
            raise ValueError("CSV file is empty.")

        raw_headers = [header.strip() for header in rows[0]]
        data_rows = rows[1:] if len(rows) > 1 else []

        column_count = max([len(rows[0])] + [len(row) for row in data_rows])
        padded_headers = self._pad_row(raw_headers, column_count)
        cleaned_headers = self._normalize_headers(padded_headers)

        preferences = self._parse_prompt_preferences(prompt, raw_headers, cleaned_headers)

        drop_requests = list(preferences.drop_columns or [])
        keep_requests = list(preferences.keep_columns or [])
        drop_indices, dropped_headers = self._resolve_drop_columns(raw_headers, cleaned_headers, drop_requests)
        protected_drop_indices, _ = self._resolve_drop_columns(raw_headers, cleaned_headers, keep_requests)
        if protected_drop_indices:
            drop_indices = [index for index in drop_indices if index not in protected_drop_indices]
        kept_indices = [index for index in range(column_count) if index not in drop_indices]
        filtered_raw_headers = [raw_headers[index] for index in kept_indices]
        filtered_cleaned_headers = [cleaned_headers[index] for index in kept_indices]
        dropped_headers = [cleaned_headers[index] for index in drop_indices]

        column_profiles = self._build_column_profiles(filtered_cleaned_headers, data_rows, kept_indices)

        cleaned_rows: list[list[str]] = []
        seen_rows: set[tuple[str, ...]] = set()
        removed_empty_rows = 0
        removed_duplicate_rows = 0
        removed_outlier_rows = 0

        imputation_summary: list[dict[str, object]] = []

        for row in data_rows:
            padded_row = self._pad_row(row, column_count)
            cleaned_row = [self._clean_cell(padded_row[index], preferences=preferences) for index in kept_indices]

            if preferences.remove_empty_rows and all(cell == "" for cell in cleaned_row):
                removed_empty_rows += 1
                continue

            for index, value in enumerate(cleaned_row):
                current_header = filtered_cleaned_headers[index]
                if self._is_protected_column(current_header, preferences):
                    continue
                if value == "":
                    cleaned_row[index] = self._resolve_fill_value(column_profiles[index], preferences)
                    column_profiles[index]["filled_count"] = int(column_profiles[index]["filled_count"]) + 1

            outlier_columns = self._find_outlier_columns(cleaned_row, column_profiles)
            if preferences.remove_outlier_rows and outlier_columns:
                removed_outlier_rows += 1
                for column_name in outlier_columns:
                    for profile in column_profiles:
                        if profile["column_name"] == column_name:
                            profile["outlier_count"] = int(profile["outlier_count"]) + 1
                            break
                continue

            row_key = tuple(cleaned_row)
            if preferences.remove_duplicate_rows and row_key in seen_rows:
                removed_duplicate_rows += 1
                continue

            seen_rows.add(row_key)
            cleaned_rows.append(cleaned_row)

        for profile in column_profiles:
            if profile["filled_count"] > 0:
                imputation_summary.append(
                    {
                        "column": profile["column_name"],
                        "strategy": profile["strategy"],
                        "fill_value": profile["fill_value"],
                        "filled_count": profile["filled_count"],
                    }
                )

        summary_notes = self._build_summary_notes(
            removed_empty_rows=removed_empty_rows,
            removed_duplicate_rows=removed_duplicate_rows,
            removed_outlier_rows=removed_outlier_rows,
            column_profiles=column_profiles,
            prompt=prompt,
            preferences=preferences,
            dropped_headers=dropped_headers,
        )

        ai_summary = None
        ai_notes = self._get_gemini_review(
            filename=file_storage.filename,
            prompt=prompt,
            raw_headers=filtered_raw_headers,
            cleaned_headers=filtered_cleaned_headers,
            column_profiles=column_profiles,
            summary_notes=summary_notes,
            preview_rows=cleaned_rows[:3],
        )
        if ai_notes:
            ai_summary = ai_notes.get("headline")
            for note in ai_notes.get("notes", []):
                if note and note not in summary_notes:
                    summary_notes.append(note)
            for note in ai_notes.get("next_steps", []):
                if note and note not in summary_notes:
                    summary_notes.append(f"Next step: {note}")
        if not ai_summary:
            action_bits: list[str] = []
            if removed_outlier_rows:
                action_bits.append(f"removed {removed_outlier_rows} outlier row{'s' if removed_outlier_rows != 1 else ''}")
            if removed_duplicate_rows:
                action_bits.append(f"deduplicated {removed_duplicate_rows} row{'s' if removed_duplicate_rows != 1 else ''}")
            if removed_empty_rows:
                action_bits.append(f"dropped {removed_empty_rows} empty row{'s' if removed_empty_rows != 1 else ''}")
            if not action_bits:
                action_bits.append("normalized headers")
            ai_summary = f"Built-in review: {', '.join(action_bits)} and prepared the cleaned CSV."

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(filtered_cleaned_headers)
        writer.writerows(cleaned_rows)

        return CleaningSummary(
            filename=file_storage.filename,
            raw_headers=filtered_raw_headers,
            cleaned_headers=filtered_cleaned_headers,
            raw_column_count=len(rows[0]),
            cleaned_column_count=len(filtered_cleaned_headers),
            raw_row_count=len(data_rows),
            cleaned_row_count=len(cleaned_rows),
            removed_empty_rows=removed_empty_rows,
            removed_duplicate_rows=removed_duplicate_rows,
            removed_outlier_rows=removed_outlier_rows,
            imputation_summary=imputation_summary,
            summary_notes=summary_notes,
            ai_summary=ai_summary,
            prompt_used=prompt or None,
            cleaned_rows=cleaned_rows,
            preview_rows=cleaned_rows[:3],
            cleaned_csv_text=output.getvalue(),
        )

    def _pad_row(self, row: list[str], target_length: int) -> list[str]:
        padded_row = list(row[:target_length])
        if len(padded_row) < target_length:
            padded_row.extend([""] * (target_length - len(padded_row)))
        return padded_row

    def _normalize_headers(self, headers: list[str]) -> list[str]:
        normalized_headers: list[str] = []
        seen_counts: dict[str, int] = {}

        for index, header in enumerate(headers, start=1):
            candidate = re.sub(r"[^a-z0-9]+", "_", header.strip().lower()).strip("_")
            if not candidate:
                candidate = f"column_{index}"

            count = seen_counts.get(candidate, 0)
            seen_counts[candidate] = count + 1
            if count:
                candidate = f"{candidate}_{count + 1}"

            normalized_headers.append(candidate)

        return normalized_headers

    def _clean_cell(self, value: str, preferences: PromptPreferences | None = None) -> str:
        cleaned_value = re.sub(r"\s+", " ", value.strip())
        if cleaned_value.lower() in self.EMPTY_MARKERS:
            return ""
        return cleaned_value

    def _is_protected_column(self, column_name: str, preferences: PromptPreferences) -> bool:
        protected_columns = list(preferences.keep_columns or [])
        normalized_column = self._normalize_prompt_text(column_name)
        for protected in protected_columns:
            normalized_protected = self._normalize_prompt_text(protected)
            if normalized_protected and (normalized_protected == normalized_column or normalized_protected in normalized_column or normalized_column in normalized_protected):
                return True
        return False

    def _parse_prompt_preferences(self, prompt: str | None, raw_headers: list[str] | None = None, cleaned_headers: list[str] | None = None) -> PromptPreferences:
        preferences = PromptPreferences()
        if not prompt:
            return preferences

        ai_preferences = self._interpret_prompt_with_gemini(prompt)
        if ai_preferences:
            preferences = ai_preferences

        text = prompt.lower()
        keep_terms = self._extract_keep_column_terms(text)
        drop_terms = self._extract_drop_column_terms(text)
        if raw_headers and cleaned_headers:
            drop_terms.extend(self._extract_headers_from_prompt(prompt, raw_headers, cleaned_headers))
        if drop_terms:
            existing_drop_columns = list(preferences.drop_columns or [])
            existing_drop_columns.extend(drop_terms)
            preferences.drop_columns = list(dict.fromkeys(existing_drop_columns))
        if keep_terms:
            existing_keep_columns = list(preferences.keep_columns or [])
            existing_keep_columns.extend(keep_terms)
            preferences.keep_columns = list(dict.fromkeys(existing_keep_columns))
        if any(phrase in text for phrase in ["keep duplicates", "do not remove duplicates", "don't remove duplicates", "preserve duplicates"]):
            preferences.remove_duplicate_rows = False
        if any(phrase in text for phrase in ["keep outlier", "do not remove outliers", "don't remove outliers", "preserve outliers"]):
            preferences.remove_outlier_rows = False
        if any(phrase in text for phrase in ["keep empty rows", "do not remove empty rows", "don't remove empty rows", "preserve empty rows"]):
            preferences.remove_empty_rows = False

        if any(
            phrase in text
            for phrase in [
                "fill with zero",
                "use zero",
                "replace missing with 0",
                "fill with 0",
                "fill null with 0",
                "fill nulls with 0",
                "fill the null value with 0",
                "fill the null values with 0",
                "fill all null value with 0",
                "fill all null values with 0",
                "fill all the null value with 0",
                "fill all the null values with 0",
                "replace null with 0",
                "replace nulls with 0",
                "set null to 0",
            ]
        ):
            preferences.fill_strategy = "zero"
            preferences.fill_value = "0"
        elif any(phrase in text for phrase in ["use mode", "fill with mode", "mode for missing"]):
            preferences.fill_strategy = "mode"
        elif any(phrase in text for phrase in ["use median", "fill with median", "median for missing"]):
            preferences.fill_strategy = "median"

        explicit_fill = re.search(
            r"(?:fill|replace|set)[\s\w]*?(?:null|missing|blank|na|n/a)[\s\w]*?(?:with|to)\s+([a-z0-9_.-]+)",
            text,
        )
        if explicit_fill:
            preferences.fill_strategy = "literal"
            preferences.fill_value = explicit_fill.group(1)

        if any(phrase in text for phrase in ["keep blanks", "leave blanks", "do not fill missing", "don't fill missing", "keep nulls", "leave nulls"]):
            preferences.treat_missing_as_blank = False

        if preferences.keep_columns:
            preferences.treat_missing_as_blank = True

        if preferences.prompt_summary:
            preferences.prompt_summary = preferences.prompt_summary.strip()

        return preferences

    def _interpret_prompt_with_gemini(self, prompt: str) -> PromptPreferences | None:
        api_key = "AIzaSyBGgy_bd1yFo424PiDwcnycjJzaX3bv1wE"
        if not api_key:
            return None

        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        instruction = (
            "Convert the user's data-cleaning request into strict JSON only. "
            "Return keys: remove_empty_rows (bool), remove_duplicate_rows (bool), remove_outlier_rows (bool), "
            "fill_strategy (one of: null, zero, mode, median, literal, auto), fill_value (string or null), "
            "drop_columns (array of exact column names or phrases), and prompt_summary (short string). "
            "If the request says to remove a column, include it in drop_columns. "
            "If it says to fill missing values with a specific value, set fill_strategy to literal and put that value in fill_value. "
            "If it says to fill missing values with zero, set fill_strategy to zero and fill_value to 0. "
            "If it says to use the best approach, choose auto. "
            "If it says to keep something, set the relevant remove_* flag to false. "
            "Do not include markdown or extra commentary.\n\n"
            f"User request: {prompt}"
        )

        payload = {
            "contents": [{"role": "user", "parts": [{"text": instruction}]}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 256,
                "responseMimeType": "application/json",
            },
        }

        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
            return None

        candidates = response_payload.get("candidates", [])
        if not candidates:
            return None

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
        if not text:
            return None

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                return None
            try:
                parsed = json.loads(match.group(0))
            except json.JSONDecodeError:
                return None

        preferences = PromptPreferences()
        preferences.remove_empty_rows = bool(parsed.get("remove_empty_rows", True))
        preferences.remove_duplicate_rows = bool(parsed.get("remove_duplicate_rows", True))
        preferences.remove_outlier_rows = bool(parsed.get("remove_outlier_rows", True))
        fill_strategy = parsed.get("fill_strategy")
        if fill_strategy in {"zero", "mode", "median", "literal", "auto"}:
            preferences.fill_strategy = str(fill_strategy)
        fill_value = parsed.get("fill_value")
        if isinstance(fill_value, str) and fill_value.strip():
            preferences.fill_value = fill_value.strip()
        drop_columns = parsed.get("drop_columns")
        if isinstance(drop_columns, list):
            preferences.drop_columns = [str(item) for item in drop_columns if str(item).strip()]
        preferences.prompt_summary = str(parsed.get("prompt_summary") or prompt[:120]).strip() or None
        return preferences

    def _extract_headers_from_prompt(self, prompt: str, raw_headers: list[str], cleaned_headers: list[str]) -> list[str]:
        prompt_text = self._normalize_prompt_text(prompt)
        requested_headers: list[str] = []

        for header in list(raw_headers) + list(cleaned_headers):
            normalized_header = self._normalize_prompt_text(header)
            if not normalized_header:
                continue

            if normalized_header in prompt_text:
                requested_headers.append(header)

        return list(dict.fromkeys(requested_headers))

    def _extract_keep_column_terms(self, prompt_text: str) -> list[str]:
        column_terms: list[str] = []
        keep_patterns = [
            r"(?:don'?t\s+remove|do\s+not\s+remove|dont\s+remove|keep|preserve|remain\s+unchanged|leave)\s+(?:the\s+)?([a-z0-9_\- ,&/]+?)\s*(?:column|columns|col|cols|field|fields|unchanged|intact|as\s+is|remain|stay|please|plz|do\s+not\s+fill|don'?t\s+fill|dont\s+fill)?(?:$|[.,;])",
            r"(?:do\s+not\s+fill|don'?t\s+fill|dont\s+fill|leave)\s+(?:the\s+)?([a-z0-9_\- ,&/]+?)\s*(?:column|columns|col|cols|field|fields|blank|empty|unchanged|intact|as\s+is|please|plz)?(?:$|[.,;])",
        ]

        for pattern in keep_patterns:
            for match in re.finditer(pattern, prompt_text):
                phrase = match.group(1)
                phrase = re.sub(r"\b(column|columns|col|cols|field|fields|from|the|a|an|and|please|plz|anything|anything\s+to)\b", " ", phrase)
                for term in re.split(r"[,/&]+|\band\b", phrase):
                    candidate = re.sub(r"[^a-z0-9]+", " ", term).strip()
                    if candidate:
                        column_terms.append(candidate)

        return list(dict.fromkeys(column_terms))

    def _normalize_prompt_text(self, text: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()

    def _extract_drop_column_terms(self, prompt_text: str) -> list[str]:
        column_terms: list[str] = []
        for match in re.finditer(r"(?:remove|drop|delete|exclude|ignore|eliminate)\s+(?:the\s+)?([a-z0-9_\- ,&/]+)", prompt_text):
            phrase = match.group(1)
            phrase = re.sub(r"\b(column|columns|col|cols|field|fields|from|the|a|an|and|please)\b", " ", phrase)
            for term in re.split(r"[,/&]+|\band\b", phrase):
                candidate = re.sub(r"[^a-z0-9]+", " ", term).strip()
                if candidate:
                    column_terms.append(candidate)

        return list(dict.fromkeys(column_terms))

    def _resolve_drop_columns(self, raw_headers: list[str], cleaned_headers: list[str], requested_terms: list[str]) -> tuple[list[int], list[str]]:
        if not requested_terms:
            return [], []

        drop_indices: list[int] = []
        dropped_headers: list[str] = []
        normalized_raw = [re.sub(r"[^a-z0-9]+", " ", header.lower()).strip() for header in raw_headers]
        normalized_clean = [re.sub(r"[^a-z0-9]+", " ", header.lower()).strip() for header in cleaned_headers]

        for index, (raw_name, clean_name) in enumerate(zip(normalized_raw, normalized_clean)):
            for term in requested_terms:
                normalized_term = re.sub(r"[^a-z0-9]+", " ", term.lower()).strip()
                if not normalized_term:
                    continue
                if (
                    normalized_term == raw_name
                    or normalized_term == clean_name
                    or normalized_term in raw_name
                    or normalized_term in clean_name
                    or raw_name in normalized_term
                    or clean_name in normalized_term
                ):
                    if index not in drop_indices:
                        drop_indices.append(index)
                        dropped_headers.append(cleaned_headers[index])
                    break

        return drop_indices, dropped_headers

    def _resolve_fill_value(self, profile: dict[str, object], preferences: PromptPreferences) -> str:
        if not preferences.treat_missing_as_blank:
            return ""

        if preferences.fill_strategy == "literal" and preferences.fill_value is not None:
            return preferences.fill_value

        strategy = preferences.fill_strategy or str(profile["strategy"])
        if strategy == "zero":
            return "0"
        if strategy == "auto":
            strategy = str(profile["strategy"])
        if strategy == "mode":
            return self._mode(list(profile.get("sample_values", []))) or "Unknown"
        if strategy == "median" and profile.get("is_numeric"):
            sample_values = list(profile.get("sample_values", []))
            numeric_values = self._extract_numeric_values(sample_values)
            if numeric_values:
                return self._format_number(median(numeric_values))
        return str(profile["fill_value"])

    def _build_column_profiles(self, cleaned_headers: list[str], data_rows: list[list[str]], kept_indices: list[int]) -> list[dict[str, object]]:
        profiles: list[dict[str, object]] = []

        for profile_index, source_index in enumerate(kept_indices):
            values: list[str] = []
            for row in data_rows:
                padded_row = self._pad_row(row, max(kept_indices) + 1 if kept_indices else 0)
                cleaned_value = self._clean_cell(padded_row[source_index])
                if cleaned_value != "":
                    values.append(cleaned_value)

            numeric_values = self._extract_numeric_values(values)
            is_numeric = bool(numeric_values) and len(numeric_values) == len(values)
            if numeric_values and len(numeric_values) == len(values):
                fill_value = self._format_number(median(numeric_values)) if numeric_values else "0"
                strategy = "median"
                outlier_min, outlier_max = self._calculate_outlier_bounds(numeric_values)
            else:
                fill_value = self._mode(values) or "Unknown"
                strategy = "mode"
                outlier_min = None
                outlier_max = None

            profiles.append(
                {
                    "column_name": cleaned_headers[profile_index],
                    "strategy": strategy,
                    "fill_value": fill_value,
                    "filled_count": 0,
                    "is_numeric": is_numeric,
                    "outlier_min": outlier_min,
                    "outlier_max": outlier_max,
                    "outlier_count": 0,
                    "non_empty_count": len(values),
                    "sample_values": values[:5],
                }
            )

        return profiles

    def _calculate_outlier_bounds(self, numeric_values: list[float]) -> tuple[float | None, float | None]:
        if len(numeric_values) < 4:
            return None, None

        ordered = sorted(numeric_values)
        midpoint = len(ordered) // 2
        if len(ordered) % 2 == 0:
            lower_half = ordered[:midpoint]
            upper_half = ordered[midpoint:]
        else:
            lower_half = ordered[:midpoint]
            upper_half = ordered[midpoint + 1 :]

        if not lower_half or not upper_half:
            return None, None

        q1 = median(lower_half)
        q3 = median(upper_half)
        iqr = q3 - q1
        if iqr <= 0:
            return None, None

        return q1 - 1.5 * iqr, q3 + 1.5 * iqr

    def _find_outlier_columns(self, row: list[str], column_profiles: list[dict[str, object]]) -> list[str]:
        outlier_columns: list[str] = []

        for index, profile in enumerate(column_profiles):
            lower = profile.get("outlier_min")
            upper = profile.get("outlier_max")
            if lower is None or upper is None:
                continue

            try:
                value = float(row[index])
            except (ValueError, TypeError):
                continue

            if value < float(lower) or value > float(upper):
                outlier_columns.append(str(profile["column_name"]))

        return outlier_columns

    def _build_summary_notes(
        self,
        *,
        removed_empty_rows: int,
        removed_duplicate_rows: int,
        removed_outlier_rows: int,
        column_profiles: list[dict[str, object]],
        prompt: str | None,
        preferences: PromptPreferences,
        dropped_headers: list[str],
    ) -> list[str]:
        notes: list[str] = []

        preference_notes: list[str] = []
        if prompt:
            preference_notes.append(f"Prompt received: {prompt}")
        if preferences.prompt_summary:
            preference_notes.append(f"Interpreted prompt: {preferences.prompt_summary}.")
        if not preferences.remove_duplicate_rows:
            preference_notes.append("Prompt kept duplicate rows in the cleaned output.")
        if not preferences.remove_outlier_rows:
            preference_notes.append("Prompt kept numeric outliers in the cleaned output.")
        if not preferences.remove_empty_rows:
            preference_notes.append("Prompt kept empty rows in the cleaned output.")
        if preferences.fill_strategy:
            preference_notes.append(f"Prompt requested {preferences.fill_strategy} for missing-value handling.")
        if dropped_headers:
            preference_notes.append(f"Prompt removed columns: {', '.join(dropped_headers)}.")

        notes.extend(preference_notes)

        if removed_empty_rows:
            notes.append(f"Removed {removed_empty_rows} empty row{'s' if removed_empty_rows != 1 else ''}.")

        if removed_duplicate_rows:
            notes.append(f"Removed {removed_duplicate_rows} duplicate row{'s' if removed_duplicate_rows != 1 else ''}.")

        if removed_outlier_rows:
            notes.append(f"Removed {removed_outlier_rows} row{'s' if removed_outlier_rows != 1 else ''} with numeric outliers.")

        filled_columns = [profile for profile in column_profiles if int(profile["filled_count"]) > 0]
        if filled_columns:
            filled_text = ", ".join(str(profile["column_name"]) for profile in filled_columns[:4])
            if len(filled_columns) > 4:
                filled_text = f"{filled_text}, and {len(filled_columns) - 4} more"
            notes.append(f"Filled missing values in {filled_text} using column-specific median or mode strategies.")

        if not notes:
            notes.append("No cleaning issues were detected beyond header normalization.")

        return notes

    def _get_gemini_review(
        self,
        *,
        filename: str | None,
        prompt: str | None,
        raw_headers: list[str],
        cleaned_headers: list[str],
        column_profiles: list[dict[str, object]],
        summary_notes: list[str],
        preview_rows: list[list[str]],
    ) -> dict[str, Any] | None:
        api_key = "AIzaSyBGgy_bd1yFo424PiDwcnycjJzaX3bv1wE"
        if not api_key:
            return None

        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        profile_payload = {
            "filename": filename,
            "raw_headers": raw_headers,
            "cleaned_headers": cleaned_headers,
            "columns": [
                {
                    "name": profile["column_name"],
                    "strategy": profile["strategy"],
                    "fill_value": profile["fill_value"],
                    "filled_count": profile["filled_count"],
                    "outlier_count": profile["outlier_count"],
                    "sample_values": profile["sample_values"],
                }
                for profile in column_profiles
            ],
            "summary_notes": summary_notes,
            "preview_rows": preview_rows,
        }

        user_prompt = prompt.strip() if prompt else ""
        instruction = (
            "You are a senior data cleaning assistant. Review the dataset profile and the cleaning actions already applied. "
            "The user prompt is optional; if it exists, prioritize it. Return strict JSON only with these keys: "
            "headline (short sentence), notes (array of 3 to 6 concise notes), and next_steps (array of 0 to 3 short suggestions). "
            "Make sure the notes mention missing values, outliers, duplicates, and header normalization when relevant. "
            "Do not include markdown, code fences, or commentary outside the JSON object.\n\n"
            f"User prompt: {user_prompt or 'No user prompt was provided.'}\n\n"
            f"Dataset profile: {json.dumps(profile_payload, ensure_ascii=False, indent=2)}"
        )

        payload = {
            "contents": [{"role": "user", "parts": [{"text": instruction}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 512,
                "responseMimeType": "application/json",
            },
        }

        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
            return None

        candidates = response_payload.get("candidates", [])
        if not candidates:
            return None

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
        if not text:
            return None

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                return None
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None

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

    def _mode(self, values: list[str]) -> str | None:
        if not values:
            return None

        counts: dict[str, int] = {}
        order: list[str] = []
        for value in values:
            if value not in counts:
                order.append(value)
            counts[value] = counts.get(value, 0) + 1

        best_value = order[0]
        best_count = counts[best_value]
        for value in order[1:]:
            if counts[value] > best_count:
                best_value = value
                best_count = counts[value]

        return best_value