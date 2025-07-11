from flask import Flask, request, jsonify
from flask_cors import CORS
import tempfile
import os
import openai

openai.api_key = os.environ["OPENAI_API_KEY"]

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "API médica activa"})

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
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        text = "\n".join([page.extract_text() or "" for page in reader.pages])

        # Nuevo prompt con salida HTML directamente
        prompt = f"""
Eres un nutricionista y entrenador personal que trabaja en Colombia.

Con base en este examen médico, responde únicamente con el código HTML de dos tablas, sin ningún texto adicional ni encabezado:

1. Tabla de alimentación: columnas → Comida | Platillo recomendado | Motivo
2. Tabla de actividad física: columnas → Tipo de actividad | Frecuencia | Duración | Motivo

No incluyas explicaciones. Solo el código HTML de ambas tablas.

Texto del examen médico:
{text[:3000]}
        """

        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )

        html_tablas = completion.choices[0].message['content']
        os.remove(pdf_path)

        return jsonify({"recomendaciones": html_tablas})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
