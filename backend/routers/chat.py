import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db_connection
#from models import Alert, Hive, SensorReading

router = APIRouter(prefix="/chat", tags=["chatbot"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


def _hive_context() -> str:
    # On récupère une connexion directe à SQLite
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # On récupère les données de la table ruches (id_ruche, temperature, poids, etc.)
        cursor.execute("SELECT id_ruche, temperature, poids, frequence_moyenne FROM ruches")
        hives = cursor.fetchall()
    
    lines = []
    for hive in hives:
        id_r, temp, poids, freq = hive
        line = f"- Ruche {id_r} : "
        line += f"Température={temp if temp else 'N/A'}°C, "
        line += f"Poids={poids if poids else 'N/A'} kg, "
        line += f"Fréquence={freq if freq else 'N/A'} Hz"
        lines.append(line)

    return "\n".join(lines)

_SYSTEM_PROMPT = """\
Tu es un assistant expert en apiculture. Tu aides un apiculteur à surveiller ses ruches connectées.
Tu réponds en français, de manière concise et pratique, en t'appuyant sur les données des capteurs.
Si une fréquence est haute (>300Hz), l'essaimage est probable. Si elle est basse (<150Hz), la ruche est peut-être orpheline.

État actuel des ruches :
{context}
"""


@router.post("/", response_model=ChatResponse)
def chat(req: ChatRequest):
    endpoint    = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key     = os.getenv("AZURE_OPENAI_API_KEY")
    deployment  = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")

    if not endpoint or not api_key:
        raise HTTPException(
            status_code=503,
            detail="Azure OpenAI non configuré — renseigner AZURE_OPENAI_ENDPOINT et AZURE_OPENAI_API_KEY dans .env",
        )

    from openai import AzureOpenAI

    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
    )

    context = _hive_context()
    completion = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT.format(context=context)},
            {"role": "user",   "content": req.message},
        ],
        max_tokens=200,
        temperature=0.7,
    )

    return ChatResponse(response=completion.choices[0].message.content)
