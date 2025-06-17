from flask import Flask, request, jsonify
from flask_cors import CORS
import tempfile
import os
import requests
from PyPDF2 import PdfReader

app = Flask(__name__)
CORS(app)

HUGGINGFACE_API_TOKEN = os.environ.get("HUGGINGFACE_API_TOKEN")
HUGGINGFACE_MODEL = "tiiuae/falcon-7b-instruct"  # Puedes cambiar por otro modelo si lo deseas

headers = {
    "Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}",
    "Content-Type": "application/json"
}

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "API médica activa con HuggingFace"})

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

        prompt = f"""
Eres un nutricionista y entrenador personal que trabaja en Colombia.
Con base en este examen médico, genera una tabla con:
- Recomendaciones alimenticias en comida colombiana (desayuno, comida, cena)
- Actividad física adecuada (tipo, frecuencia y duración).
Texto del examen médico:
{text[:2000]}
        """

        payload = {
            "inputs": prompt
        }

        response = requests.post(
            f"https://api-inference.huggingface.co/models/{HUGGINGFACE_MODEL}",
            headers=headers,
            json=payload
        )

        if response.status_code != 200:
            return jsonify({"error": f"HuggingFace error: {response.text}"}), 500

        data = response.json()
        output = data[0]["generated_text"] if isinstance(data, list) and "generated_text" in data[0] else str(data)

        return jsonify({"recomendaciones": output})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
