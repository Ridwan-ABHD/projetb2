import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_db_connection

router = APIRouter(prefix="/chat", tags=["chatbot"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


def _hive_context() -> str:
    with get_db_connection() as conn:
        rows = conn.execute("""
            SELECT r.id_ruche, m.temperature, m.poids, m.frequence_moyenne
            FROM ruches r
            LEFT JOIN (
                SELECT id_ruche, temperature, poids, frequence_moyenne
                FROM mesures
                WHERE id_mesure IN (SELECT MAX(id_mesure) FROM mesures GROUP BY id_ruche)
            ) m ON m.id_ruche = r.id_ruche
        """).fetchall()

    lines = []
    for row in rows:
        temp = row["temperature"]
        poids = row["poids"]
        freq  = row["frequence_moyenne"]
        lines.append(
            f"- Ruche {row['id_ruche']} : "
            f"Température={f'{temp:.1f}' if temp else 'N/A'}°C, "
            f"Poids={f'{poids:.1f}' if poids else 'N/A'} kg, "
            f"Fréquence={f'{freq:.0f}' if freq else 'N/A'} Hz"
        )
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
