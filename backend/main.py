import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# On ne garde QUE tes routers nettoyés et ta connexion
from database import get_db_connection
from mqtt_client import start_mqtt_subscriber
from routers import alerts, chat, diagnosis, hives, push, settings

load_dotenv()

# Configuration du logging (plus propre)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger("main")

def _init_db():
    with get_db_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS ruches (
                id_ruche    TEXT PRIMARY KEY,
                nom         TEXT,
                localisation TEXT,
                statut      TEXT DEFAULT 'normal'
            );
            CREATE TABLE IF NOT EXISTS mesures (
                id_mesure        INTEGER PRIMARY KEY AUTOINCREMENT,
                id_ruche         TEXT NOT NULL,
                timestamp        TEXT NOT NULL,
                temperature      REAL,
                poids            REAL,
                frequence_moyenne REAL,
                humidite         REAL
            );
            CREATE TABLE IF NOT EXISTS regles_alerte (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                id_ruche        TEXT,
                type_alerte     TEXT,
                seuil_min       REAL,
                seuil_max       REAL,
                active          INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS alertes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                id_ruche    TEXT NOT NULL,
                timestamp   TEXT NOT NULL,
                type        TEXT,
                message     TEXT,
                severite    TEXT DEFAULT 'warning',
                is_resolved INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS push_subscriptions (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint          TEXT UNIQUE NOT NULL,
                subscription_json TEXT NOT NULL,
                created_at        TEXT DEFAULT (datetime('now'))
            );
        """)
        existing = conn.execute("SELECT COUNT(*) FROM ruches").fetchone()[0]
        if existing == 0:
            conn.executemany(
                "INSERT INTO ruches (id_ruche, nom, localisation, statut) VALUES (?, ?, ?, ?)",
                [
                    ("CF003", "Ruche CF003", "La Clairière", "normal"),
                    ("CJ001", "Ruche CJ001", "Le Jardin",   "normal"),
                    ("H1",    "Ruche H1",    "La Forêt",    "normal"),
                ],
            )
            logger.info("Base de données initialisée avec les 3 ruches par défaut")
        conn.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _init_db()

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
app.include_router(push.router)

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