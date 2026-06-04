from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from backend.exceptions import ValidationError
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
        try:
            payload = request.get_json(silent=True) or {}
            student_id = str(payload.get("student_id", "")).strip() or "UNKNOWN"
            num_questions = int(payload.get("num_questions", 10))

            # Validate input
            if num_questions < 1 or num_questions > 50:
                return jsonify({"error": "Número de questões deve estar entre 1 e 50"}), 400

            output_file = OUTPUT_DIR / f"sheet_{secure_filename(student_id)}.pdf"
            path = generate_answer_sheet(output_file, student_id=student_id, num_questions=num_questions)
            # Return only the filename, not the full path
            filename = Path(path).name
            return jsonify({"file": filename, "url": f"/api/download/{filename}"})
        except ValidationError as e:
            error_msg = e.get_user_message()
            return jsonify({"error": error_msg}), 400
        except Exception:
            return jsonify({"error": "Erro ao gerar folha de respostas"}), 500

    @app.get("/api/download/<filename>")
    def download_file(filename):
        try:
            # Validate filename to prevent directory traversal
            filename = secure_filename(filename)
            if not filename:
                return jsonify({"error": "Nome de arquivo inválido"}), 400

            file_path = OUTPUT_DIR / filename
            if not file_path.exists():
                return jsonify({"error": "Arquivo não encontrado"}), 404

            return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)
        except Exception:
            return jsonify({"error": "Erro ao baixar arquivo"}), 500

    @app.post("/api/process-image")
    def process_image():
        try:
            image = request.files.get("image")
            if image is None or not image.filename:
                return jsonify({"error": "Imagem não enviada."}), 400

            num_questions = int(request.form.get("num_questions", 10))

            # Validate input
            if num_questions < 1 or num_questions > 50:
                return jsonify({"error": "Número de questões deve estar entre 1 e 50"}), 400

            # Use secure_filename to prevent path traversal
            filename = secure_filename(image.filename)
            if not filename:
                filename = "upload.jpg"

            saved_path = UPLOAD_DIR / filename
            image.save(saved_path)

            answers = detect_answers(saved_path, num_questions=num_questions)
            return jsonify({"answers": answers, "image": filename})
        except RuntimeError:
            # ArUco detection failed or other runtime error
            return jsonify({"error": "Erro ao detectar marcadores ou respostas"}), 400
        except FileNotFoundError:
            return jsonify({"error": "Imagem não encontrada"}), 400
        except Exception:
            return jsonify({"error": "Erro ao processar imagem"}), 500

    @app.get("/")
    def root():
        return send_from_directory(FRONTEND_DIR, "index.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000)
