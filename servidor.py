
from flask import Flask, request, jsonify
from flask_cors import CORS
import tempfile
import os
import requests
from PyPDF2 import PdfReader

app = Flask(__name__)
CORS(app)

HUGGINGFACE_API_TOKEN = os.environ.get("HUGGINGFACE_API_TOKEN")
HUGGINGFACE_MODEL = "google/flan-t5-large"

headers = {
    "Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}",
    "Content-Type": "application/json"
}

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "API médica activa con FLAN-T5"})

@app.route("/analizar_pdf", methods=["POST"])
def analizar_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No se envió ningún archivo"}), 400

    pdf_file = request.files['file']
    if not pdf_file or not pdf_file.mimetype == 'application/pdf':
        return jsonify({"error": "El archivo no es un PDF"}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_file.read())
        pdf_path = tmp.name

    try:
        reader = PdfReader(pdf_path)
        text = "\n".join([page.extract_text() or "" for page in reader.pages])
        os.remove(pdf_path)

        prompt = f"Recomienda dieta saludable para este paciente colombiano con base en este informe médico:\n{text[:800]}"

        payload = {
            "inputs": prompt,
            "options": {
                "wait_for_model": True
            }
        }

        response = requests.post(
            f"https://api-inference.huggingface.co/models/{HUGGINGFACE_MODEL}",
            headers=headers,
            json=payload
        )

        if response.status_code != 200:
            return jsonify({"error": f"HuggingFace error: {response.text}"}), 500

        try:
            data = response.json()
            if isinstance(data, list):
                output = data[0].get("generated_text", "Sin respuesta generada.")
            elif isinstance(data, dict):
                output = data.get("generated_text") or str(data)
            else:
                output = str(data)
        except Exception as e:
            return jsonify({"error": f"Error al interpretar respuesta: {str(e)}"}), 500

        return jsonify({"recomendaciones": output})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
