import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# On ne garde QUE tes routers nettoyés et ta connexion
from database import get_db_connection
from mqtt_client import start_mqtt_subscriber
from routers import alerts, chat, diagnosis, hives, settings

load_dotenv()

# Configuration du logging (plus propre)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    mqtt_host   = os.getenv("MQTT_HOST", "localhost")
    mqtt_port   = int(os.getenv("MQTT_PORT", 1883))
    hmac_secret = os.getenv("HMAC_SECRET", "dev_secret")
 
    logger.info(f"🔌 Démarrage du subscriber MQTT sur {mqtt_host}:{mqtt_port}")
    start_mqtt_subscriber(host=mqtt_host, port=mqtt_port, secret=hmac_secret)
    yield
    logger.info("🛑 Arrêt de l'API")

app = FastAPI(
    title="Surveillance Apicole API - RucheIA",
    description="API connectée à la base de données réelle RucheIA.db",
    version="2.0.0",
    lifespan=lifespan,
)

# Configuration CORS pour que ton dashboard puisse lire l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# On inclut tes routers (que nous avons simplifiés en SQL pur)
app.include_router(hives.router)
app.include_router(alerts.router)
app.include_router(settings.router)
app.include_router(diagnosis.router)
app.include_router(chat.router)

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API de Surveillance Apicole RucheIA", "docs": "/docs"}

@app.get("/health", tags=["infra"])
def health():
    return {
        "status": "ok", 
        "service": "Surveillance Apicole API",
        "database": "RucheIA.db connectée"
    }