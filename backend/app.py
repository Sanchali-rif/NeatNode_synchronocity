import csv
import io
import json
from io import BytesIO
from typing import Any
from uuid import uuid4

from flask_cors import CORS
from flask import Flask, flash, jsonify, redirect, render_template, request, send_file, url_for

from cleaning_model import CSVCleaningModel
from query_assistant import DataQueryAssistant


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app, origins=["http://localhost:5173", "http://localhost:5174", "https://neatnode.onrender.com", "https://neat-node.vercel.app", "*"])
    app.secret_key = "dev-secret-key"
    cleaner = CSVCleaningModel()
    assistant = DataQueryAssistant()
    cleaned_dataset_cache: dict[str, dict[str, Any]] = {}

    @app.get("/download-cleaned/<token>")
    def download_cleaned(token: str):
        dataset = cleaned_dataset_cache.get(token)
        if dataset is None:
            flash("The cleaned file is no longer available. Please upload the CSV again.", "error")
            return redirect(url_for("home"))

        cleaned_csv_text = dataset["cleaning_result"].cleaned_csv_text
        export_format = (request.args.get("format") or "csv").strip().lower()
        export_bytes, mimetype, download_name = build_export_file(cleaned_csv_text, export_format)

        return send_file(
            BytesIO(export_bytes),
            mimetype=mimetype,
            as_attachment=True,
            download_name=download_name,
        )

    @app.get("/api/download-cleaned/<token>")
    def api_download_cleaned(token: str):
        dataset = cleaned_dataset_cache.get(token)
        if dataset is None:
            return jsonify({"error": "File no longer available"}), 404
        cleaned_csv_text = dataset["cleaning_result"].cleaned_csv_text
        export_format = (request.args.get("format") or "csv").strip().lower()
        export_bytes, mimetype, download_name = build_export_file(cleaned_csv_text, export_format)
        return send_file(BytesIO(export_bytes), mimetype=mimetype, as_attachment=True, download_name=download_name)

    def build_visualization_data(cleaning_result):
        row_base = max(cleaning_result.raw_row_count, 1)
        column_base = max(cleaning_result.raw_column_count, 1)
        row_retained_percent = round((cleaning_result.cleaned_row_count / row_base) * 100, 1)
        column_retained_percent = round((cleaning_result.cleaned_column_count / column_base) * 100, 1)

        action_values = [
            cleaning_result.removed_empty_rows,
            cleaning_result.removed_duplicate_rows,
            cleaning_result.removed_outlier_rows,
        ]
        action_base = max(action_values + [1])

        imputation_base = 1
        if cleaning_result.imputation_summary:
            imputation_base = max(int(item.get("filled_count", 0)) for item in cleaning_result.imputation_summary) or 1

        return {
            "row_retained_percent": row_retained_percent,
            "row_removed_percent": round(100 - row_retained_percent, 1),
            "column_retained_percent": column_retained_percent,
            "column_removed_percent": round(100 - column_retained_percent, 1),
            "action_cards": [
                {
                    "label": "Empty rows removed",
                    "value": cleaning_result.removed_empty_rows,
                    "width": round((cleaning_result.removed_empty_rows / action_base) * 100, 1),
                },
                {
                    "label": "Duplicate rows removed",
                    "value": cleaning_result.removed_duplicate_rows,
                    "width": round((cleaning_result.removed_duplicate_rows / action_base) * 100, 1),
                },
                {
                    "label": "Outlier rows removed",
                    "value": cleaning_result.removed_outlier_rows,
                    "width": round((cleaning_result.removed_outlier_rows / action_base) * 100, 1),
                },
            ],
            "imputation_cards": [
                {
                    "label": item["column"],
                    "value": item["filled_count"],
                    "width": round((int(item["filled_count"]) / imputation_base) * 100, 1),
                    "strategy": item["strategy"],
                    "fill_value": item["fill_value"],
                }
                for item in cleaning_result.imputation_summary[:4]
            ],
        }

    def render_result_page(*, cleaning_result, download_token, assistant_response=None, assistant_question="", chat_history=None):
        return render_template(
            "index.html",
            features=[
                {
                    "title": "Rule-based cleaning model",
                    "description": "Best for messy CSVs because it is deterministic, explainable, and easy to extend.",
                },
                {
                    "title": "Header normalization",
                    "description": "Whitespace, casing, and symbols get normalized into stable column names.",
                },
                {
                    "title": "Row hygiene",
                    "description": "Empty rows, duplicate rows, and noisy cell values are cleaned automatically.",
                },
            ],
            stats=[
                {"label": "Model type", "value": "Deterministic"},
                {"label": "Cleaning", "value": "Headers + rows"},
                {"label": "Output", "value": "Normalized CSV"},
            ],
            cleaning_result=cleaning_result,
            visualization_data=build_visualization_data(cleaning_result) if cleaning_result else None,
            download_token=download_token,
            cleaning_prompt="",
            assistant_response=assistant_response,
            assistant_question=assistant_question,
            chat_history=chat_history or [],
        )

    def build_assistant_payload(assistant_response, assistant_question: str, chat_history: list[dict[str, str]]) -> dict[str, Any]:
        return {
            "question": assistant_question,
            "assistant": {
                "title": assistant_response.title,
                "summary": assistant_response.summary,
                "sql_like": assistant_response.sql_like,
                "matched_row_count": assistant_response.matched_row_count,
                "total_row_count": assistant_response.total_row_count,
                "table_headers": assistant_response.table_headers,
                "table_rows": assistant_response.table_rows,
                "detail_lines": assistant_response.detail_lines,
            },
            "chat_history": chat_history,
        }

    def build_export_file(cleaned_csv_text: str, export_format: str) -> tuple[bytes, str, str]:
        headers, rows = parse_cleaned_csv(cleaned_csv_text)

        if export_format == "json":
            payload = [dict(zip(headers, row)) for row in rows]
            return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"), "application/json", "cleaned_output.json"

        if export_format == "sql":
            return render_sql_script(headers, rows).encode("utf-8"), "text/plain; charset=utf-8", "cleaned_output.sql"

        if export_format == "python":
            return render_python_script(headers, rows).encode("utf-8"), "text/x-python; charset=utf-8", "cleaned_output.py"

        if export_format != "csv":
            flash("Unsupported export format. Downloaded the cleaned CSV instead.", "error")

        return cleaned_csv_text.encode("utf-8"), "text/csv; charset=utf-8", "cleaned_output.csv"

    def parse_cleaned_csv(cleaned_csv_text: str) -> tuple[list[str], list[list[str]]]:
        reader = csv.reader(io.StringIO(cleaned_csv_text))
        rows = list(reader)
        if not rows:
            return [], []
        return rows[0], rows[1:]

    def render_sql_script(headers: list[str], rows: list[list[str]]) -> str:
        def sql_value(value: str) -> str:
            if value == "":
                return "NULL"
            escaped = value.replace("'", "''")
            return f"'{escaped}'"

        column_list = ", ".join(f'"{header}"' for header in headers)
        lines = ["-- Generated SQL INSERT script", "INSERT INTO cleaned_data (" + column_list + ") VALUES"]

        values_lines = []
        for row in rows:
            padded_row = row + [""] * max(0, len(headers) - len(row))
            values_lines.append("(" + ", ".join(sql_value(cell) for cell in padded_row[: len(headers)]) + ")")

        if values_lines:
            lines.append(",\n".join(values_lines) + ";")
        else:
            lines.append(";")

        return "\n".join(lines)

    def render_python_script(headers: list[str], rows: list[list[str]]) -> str:
        script_headers = json.dumps(headers, ensure_ascii=False, indent=2)
        script_rows = json.dumps(rows, ensure_ascii=False, indent=2)
        return (
            "# Generated Python export\n"
            "import csv\n\n"
            f"headers = {script_headers}\n"
            f"rows = {script_rows}\n\n"
            "def rows_as_dicts():\n"
            "    return [dict(zip(headers, row)) for row in rows]\n\n"
            "if __name__ == '__main__':\n"
            "    for item in rows_as_dicts():\n"
            "        print(item)\n"
        )

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.route("/", methods=["GET", "POST"])
    def home() -> str:
        cleaning_result = None
        download_token = None
        cleaning_prompt = ""

        if request.method == "POST":
            uploaded_file = request.files.get("csv_file")
            cleaning_prompt = (request.form.get("cleaning_prompt") or "").strip()

            if not uploaded_file or uploaded_file.filename == "":
                flash("Please choose a CSV file before uploading.", "error")
            elif not uploaded_file.filename.lower().endswith(".csv"):
                flash("Only .csv files are supported.", "error")
            else:
                try:
                    cleaning_result = cleaner.clean_upload(uploaded_file, prompt=cleaning_prompt or None)
                    download_token = uuid4().hex
                    cleaned_dataset_cache[download_token] = {
                        "cleaning_result": cleaning_result,
                        "chat_history": [],
                    }
                    flash(f"{cleaning_result.filename} cleaned successfully.", "success")
                except (UnicodeDecodeError, ValueError) as error:
                    flash(str(error), "error")

        return render_result_page(
            cleaning_result=cleaning_result,
            download_token=download_token,
            assistant_response=None,
            assistant_question="",
            chat_history=[],
        )

    @app.post("/api/upload")
    def api_upload():
        uploaded_file = request.files.get("csv_file")
        cleaning_prompt = (request.form.get("cleaning_prompt") or "").strip()
        if not uploaded_file or uploaded_file.filename == "":
            return jsonify({"error": "No file uploaded"}), 400
        if not uploaded_file.filename.lower().endswith(".csv"):
            return jsonify({"error": "Only .csv files are supported"}), 400
        try:
            cleaning_result = cleaner.clean_upload(uploaded_file, prompt=cleaning_prompt or None)
            download_token = uuid4().hex
            cleaned_dataset_cache[download_token] = {
                "cleaning_result": cleaning_result,
                "chat_history": [],
            }
            return jsonify({
                "token": download_token,
                "filename": cleaning_result.filename,
                "raw_row_count": cleaning_result.raw_row_count,
                "cleaned_row_count": cleaning_result.cleaned_row_count,
                "raw_column_count": cleaning_result.raw_column_count,
                "cleaned_column_count": cleaning_result.cleaned_column_count,
                "removed_empty_rows": cleaning_result.removed_empty_rows,
                "removed_duplicate_rows": cleaning_result.removed_duplicate_rows,
                "removed_outlier_rows": cleaning_result.removed_outlier_rows,
                "cleaned_headers": cleaning_result.cleaned_headers,
                "preview_rows": cleaning_result.preview_rows,
                "ai_summary": cleaning_result.ai_summary,
                "prompt_used": cleaning_result.prompt_used,
                "imputation_summary": cleaning_result.imputation_summary,
                "summary_notes": cleaning_result.summary_notes,
                "visualization_data": build_visualization_data(cleaning_result),
            })
        except (UnicodeDecodeError, ValueError) as error:
            return jsonify({"error": str(error)}), 422

    @app.get("/api/result/<token>")
    def api_get_result(token: str):
        dataset = cleaned_dataset_cache.get(token)
        if dataset is None:
            return jsonify({"error": "dataset_expired"}), 404
        cleaning_result = dataset["cleaning_result"]
        return jsonify({
            "token": token,
            "filename": cleaning_result.filename,
            "raw_row_count": cleaning_result.raw_row_count,
            "cleaned_row_count": cleaning_result.cleaned_row_count,
            "raw_column_count": cleaning_result.raw_column_count,
            "cleaned_column_count": cleaning_result.cleaned_column_count,
            "removed_empty_rows": cleaning_result.removed_empty_rows,
            "removed_duplicate_rows": cleaning_result.removed_duplicate_rows,
            "removed_outlier_rows": cleaning_result.removed_outlier_rows,
            "cleaned_headers": cleaning_result.cleaned_headers,
            "preview_rows": cleaning_result.preview_rows,
            "ai_summary": cleaning_result.ai_summary,
            "prompt_used": cleaning_result.prompt_used,
            "imputation_summary": cleaning_result.imputation_summary,
            "summary_notes": cleaning_result.summary_notes,
            "visualization_data": build_visualization_data(cleaning_result),
            "chat_history": dataset.get("chat_history", []),
        })

    @app.post("/ask/<token>")
    def ask_dataset(token: str) -> str:
        dataset = cleaned_dataset_cache.get(token)
        if dataset is None:
            flash("The cleaned file is no longer available. Please upload the CSV again.", "error")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.best == "application/json":
                return jsonify({"error": "dataset_expired"}), 404
            return redirect(url_for("home"))

        cleaning_result = dataset["cleaning_result"]
        question = (request.form.get("data_question") or "").strip()
        if not question:
            flash("Ask a question about the cleaned CSV first.", "error")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.best == "application/json":
                return jsonify({"error": "empty_question"}), 400
            return render_result_page(
                cleaning_result=cleaning_result,
                download_token=token,
                assistant_response=None,
                assistant_question="",
                chat_history=dataset.get("chat_history", []),
            )

        assistant_response = assistant.answer(question, cleaning_result.cleaned_headers, cleaning_result.cleaned_rows)
        chat_history = dataset.setdefault("chat_history", [])
        chat_history.append({"role": "user", "content": question})
        chat_history.append({"role": "assistant", "content": assistant_response.summary})

        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.best == "application/json":
            return jsonify(build_assistant_payload(assistant_response, question, chat_history))

        return render_result_page(
            cleaning_result=cleaning_result,
            download_token=token,
            assistant_response=assistant_response,
            assistant_question=question,
            chat_history=chat_history,
        )

    @app.post("/api/ask/<token>")
    def api_ask_dataset(token: str):
        dataset = cleaned_dataset_cache.get(token)
        if dataset is None:
            return jsonify({"error": "dataset_expired"}), 404
        cleaning_result = dataset["cleaning_result"]
        question = (request.form.get("data_question") or "").strip()
        if not question:
            return jsonify({"error": "empty_question"}), 400
        assistant_response = assistant.answer(question, cleaning_result.cleaned_headers, cleaning_result.cleaned_rows)
        chat_history = dataset.setdefault("chat_history", [])
        chat_history.append({"role": "user", "content": question})
        chat_history.append({"role": "assistant", "content": assistant_response.summary})
        return jsonify(build_assistant_payload(assistant_response, question, chat_history))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)