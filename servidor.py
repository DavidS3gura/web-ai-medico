from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import openai
import os

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # O específica si lo prefieres
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configura tu API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.post("/analizar_pdf")
async def analizar_pdf(file: UploadFile = File(...)):
    # Leer archivo (en caso de procesar texto del PDF real)
    contents = await file.read()
    texto_pdf = "Resultados médicos extraídos..."  # simulado o parseado

    # PROMPT optimizado: respuesta directa en HTML de 2 tablas
    prompt = f"""
Eres un nutricionista y entrenador personal en Colombia.

Con base en el siguiente examen médico:

\"\"\"{texto_pdf}\"\"\"

Responde exclusivamente con el **código HTML de dos tablas**, sin explicaciones ni texto adicional. 

1. Primera tabla (alimentación): columnas → Comida | Platillo recomendado | Motivo
2. Segunda tabla (actividad física): columnas → Tipo de actividad | Frecuencia semanal | Duración por sesión | Motivo médico

Ejemplo del formato:

<table>
  <thead><tr><th>Comida</th><th>Platillo recomendado</th><th>Motivo</th></tr></thead>
  <tbody>
    <tr><td>Desayuno</td><td>Arepa con huevo</td><td>Aumentar hemoglobina</td></tr>
    ...
  </tbody>
</table>

Utiliza etiquetas HTML válidas.
"""

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un nutricionista experto que responde en HTML limpio y semántico."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        html_response = completion.choices[0].message.content.strip()

        # Añade clase "styled-table" a cada tabla automáticamente
        html_response = html_response.replace("<table>", '<table class="styled-table">')

        return JSONResponse(content={"recomendaciones": html_response})

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
