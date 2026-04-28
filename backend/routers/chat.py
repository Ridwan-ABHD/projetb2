import os
import sqlite3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_db_connection
from dotenv import load_dotenv

load_dotenv()
router = APIRouter(prefix="/chat", tags=["chatbot"])

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

def _hive_context() -> str:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. On récupère les ruches (il n'y a que id_ruche selon ta photo)
        cursor.execute("SELECT id_ruche FROM ruches")
        hives = cursor.fetchall()

        lines = []
        for hive in hives:
            rid = hive['id_ruche'] 
            
            # 2. On récupère la toute dernière mesure
            cursor.execute("""
                SELECT temperature, poids, frequence_moyenne, timestamp 
                FROM mesures 
                WHERE id_ruche = ? 
                ORDER BY timestamp DESC LIMIT 1
            """, (rid,))
            last = cursor.fetchone()

            # 3. On récupère les alertes non résolues
            # Note : Assure-toi que ta table s'appelle 'alertes' ou 'regles_alerte'
            cursor.execute("SELECT nom_regle FROM regles_alerte WHERE id_ruche = ?", (rid,))
            active_alerts = cursor.fetchall()

            # Construction de la ligne de texte pour l'IA
            line = f"- Ruche {rid}"
            
            if last:
                # On utilise les noms de colonnes (grâce à row_factory = sqlite3.Row)
                line += (
                    f" : Température={last['temperature']:.1f}°C"
                    f", Poids={last['poids']:.1f}kg"
                    f", Fréquence={last['frequence_moyenne']:.0f}Hz"
                    f" (Relevé le {last['timestamp']})"
                )
            
            if active_alerts:
                alert_names = [a['nom_regle'] for a in active_alerts]
                line += f", Alertes actives: {', '.join(alert_names)}"
            
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
    endpoint   = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key    = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")

    if not endpoint or not api_key:
        raise HTTPException(
            status_code=503,
            detail="Azure OpenAI non configuré dans le .env",
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