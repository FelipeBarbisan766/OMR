from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from backend.models import DEFAULT_DB_PATH, initialize_db
from backend.omr import detect_answers
from backend.pdf_gen import generate_answer_sheet

ROOT_DIR = Path(__file__).resolve().parents[1]
UPLOAD_DIR = ROOT_DIR / "uploads"
OUTPUT_DIR = ROOT_DIR / "outputs"
FRONTEND_DIR = ROOT_DIR / "frontend"


def create_app() -> Flask:
    app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")

    initialize_db(DEFAULT_DB_PATH)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    @app.get("/api/health")
    def health_check():
        return jsonify({"status": "ok", "mode": "local-only"})

    @app.post("/api/generate-sheet")
    def generate_sheet():
        payload = request.get_json(silent=True) or {}
        student_id = str(payload.get("student_id", "")).strip() or "UNKNOWN"
        num_questions = int(payload.get("num_questions", 10))

        output_file = OUTPUT_DIR / f"sheet_{student_id}.pdf"
        path = generate_answer_sheet(output_file, student_id=student_id, num_questions=num_questions)
        return jsonify({"file": path})

    @app.post("/api/process-image")
    def process_image():
        image = request.files.get("image")
        if image is None or not image.filename:
            return jsonify({"error": "Imagem não enviada."}), 400

        num_questions = int(request.form.get("num_questions", 10))
        saved_path = UPLOAD_DIR / image.filename
        image.save(saved_path)

        answers = detect_answers(saved_path, num_questions=num_questions)
        return jsonify({"answers": answers, "image": str(saved_path)})

    @app.get("/")
    def root():
        return send_from_directory(FRONTEND_DIR, "index.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000)
