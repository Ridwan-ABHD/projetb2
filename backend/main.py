import asyncio
import json
import logging
import os
import threading
from contextlib import asynccontextmanager
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import get_db_connection
from mqtt_client import start_mqtt_subscriber
from routers import alerts, chat, diagnosis, hives, push, settings

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("main")


# ---------------------------------------------------------------------------
# DB init
# ---------------------------------------------------------------------------

def _seed_mesures(conn):
    import random
    from datetime import timedelta

    hives_seed = [
        {"id": "CF003", "base_freq": 230, "base_temp": 34.0, "base_poids": 28.0},
        {"id": "CJ001", "base_freq": 245, "base_temp": 33.5, "base_poids": 32.0},
        {"id": "H1",    "base_freq": 280, "base_temp": 36.0, "base_poids": 25.0},
    ]
    rows = []
    now = datetime.now()
    for i in range(100):
        ts = (now - timedelta(hours=100 - i)).strftime("%Y-%m-%d %H:%M:%S")
        for h in hives_seed:
            rows.append((
                h["id"], ts,
                round(h["base_temp"] + random.uniform(-2, 4), 2),
                round(h["base_poids"] + random.uniform(-0.5, 0.5), 2),
                round(h["base_freq"] + random.uniform(-5, 30), 1),
                round(60 + random.uniform(-10, 15), 1),
            ))
    conn.executemany(
        "INSERT INTO mesures (id_ruche, timestamp, temperature, poids, frequence_moyenne, humidite) VALUES (?,?,?,?,?,?)",
        rows,
    )
    logger.info("300 mesures de démo insérées (100h × 3 ruches)")


def _init_db():
    with get_db_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS ruches (
                id_ruche   TEXT PRIMARY KEY,
                id_site    TEXT,
                type_ruche TEXT DEFAULT 'normal'
            );
            CREATE TABLE IF NOT EXISTS mesures (
                id_mesure         INTEGER PRIMARY KEY AUTOINCREMENT,
                id_ruche          TEXT NOT NULL,
                timestamp         TEXT NOT NULL,
                temperature       REAL,
                poids             REAL,
                frequence_moyenne REAL,
                humidite          REAL
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
            CREATE TABLE IF NOT EXISTS settings (
                id                    INTEGER PRIMARY KEY CHECK (id = 1),
                freq_warning          REAL DEFAULT 260,
                freq_critical         REAL DEFAULT 280,
                temp_warning          REAL DEFAULT 36,
                temp_critical         REAL DEFAULT 38,
                humidity_min          REAL DEFAULT 50,
                humidity_max          REAL DEFAULT 80,
                weight_drop_threshold REAL DEFAULT 2
            );
            CREATE TABLE IF NOT EXISTS enregistrements (
                id_audio    INTEGER PRIMARY KEY AUTOINCREMENT,
                id_ruche    TEXT NOT NULL,
                nom_fichier TEXT NOT NULL,
                date_enreg  TEXT
            );
            CREATE TABLE IF NOT EXISTS segments (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                id_audio INTEGER NOT NULL,
                label    TEXT,
                debut    REAL,
                fin      REAL
            );
            CREATE TABLE IF NOT EXISTS regles_alerte (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                id_ruche    TEXT,
                type_alerte TEXT,
                seuil_min   REAL,
                seuil_max   REAL,
                active      INTEGER DEFAULT 1
            );
        """)

        if conn.execute("SELECT COUNT(*) FROM ruches").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO ruches (id_ruche, id_site, type_ruche) VALUES (?, ?, ?)",
                [
                    ("CF003", "La Clairière", "normal"),
                    ("CJ001", "Le Jardin",   "normal"),
                    ("H1",    "La Forêt",    "normal"),
                ],
            )
            logger.info("3 ruches par défaut insérées")

        if conn.execute("SELECT COUNT(*) FROM mesures").fetchone()[0] == 0:
            _seed_mesures(conn)

        conn.execute(
            "INSERT OR IGNORE INTO settings (id) VALUES (1)"
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Push helper (partagé avec mqtt_client)
# ---------------------------------------------------------------------------

def _send_push(hive_id: str, message: str):
    vapid_private_key = os.getenv("VAPID_PRIVATE_KEY")
    vapid_email = os.getenv("VAPID_EMAIL", "mailto:admin@surveillance-apicole.fr")
    if not vapid_private_key:
        return
    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        return

    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT id, endpoint, subscription_json FROM push_subscriptions"
        ).fetchall()
    if not rows:
        return

    data = json.dumps({
        "title": f"Alerte — Ruche {hive_id}",
        "body":  message,
        "icon":  "/icons/icon-192.png",
        "url":   "/",
    })
    stale = []
    for row in rows:
        try:
            webpush(
                subscription_info=json.loads(row["subscription_json"]),
                data=data,
                vapid_private_key=vapid_private_key,
                vapid_claims={"sub": vapid_email},
            )
        except Exception as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status in (404, 410):
                stale.append(row["id"])
            else:
                logger.warning("Push échoué : %s", exc)
    if stale:
        with get_db_connection() as conn:
            for sid in stale:
                conn.execute("DELETE FROM push_subscriptions WHERE id = ?", (sid,))
            conn.commit()


# ---------------------------------------------------------------------------
# Tâche background : génération d'alertes + push
# ---------------------------------------------------------------------------

async def _alert_checker():
    """Toutes les 15 s : compare les dernières mesures aux seuils et crée des alertes."""
    await asyncio.sleep(10)  # laisse le temps au backend de démarrer
    while True:
        try:
            with get_db_connection() as conn:
                s = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
                if not s:
                    await asyncio.sleep(15)
                    continue

                temp_warn = s["temp_warning"]
                temp_crit = s["temp_critical"]
                freq_warn = s["freq_warning"]
                freq_crit = s["freq_critical"]

                ruches = conn.execute("SELECT id_ruche FROM ruches").fetchall()
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                for (hive_id,) in ruches:
                    last = conn.execute("""
                        SELECT temperature, frequence_moyenne FROM mesures
                        WHERE id_ruche = ? ORDER BY timestamp DESC LIMIT 1
                    """, (hive_id,)).fetchone()
                    if not last:
                        continue

                    temp = last["temperature"]
                    freq = last["frequence_moyenne"]
                    to_create = []

                    # --- Température ---
                    if temp is not None:
                        if temp >= temp_crit:
                            if not conn.execute(
                                "SELECT 1 FROM alertes WHERE id_ruche=? AND type='temperature_critique' AND is_resolved=0",
                                (hive_id,)
                            ).fetchone():
                                to_create.append(("temperature_critique",
                                    f"Température critique : {temp:.1f}°C", "critical"))
                        elif temp >= temp_warn:
                            if not conn.execute(
                                "SELECT 1 FROM alertes WHERE id_ruche=? AND type='temperature_warning' AND is_resolved=0",
                                (hive_id,)
                            ).fetchone():
                                to_create.append(("temperature_warning",
                                    f"Température élevée : {temp:.1f}°C", "warning"))
                        else:
                            conn.execute("""
                                UPDATE alertes SET is_resolved=1 WHERE id_ruche=?
                                AND type IN ('temperature_critique','temperature_warning') AND is_resolved=0
                            """, (hive_id,))

                    # --- Fréquence ---
                    if freq is not None:
                        if freq >= freq_crit:
                            if not conn.execute(
                                "SELECT 1 FROM alertes WHERE id_ruche=? AND type='frequence_critique' AND is_resolved=0",
                                (hive_id,)
                            ).fetchone():
                                to_create.append(("frequence_critique",
                                    f"Fréquence critique : {freq:.0f} Hz — Risque d'essaimage", "critical"))
                        elif freq >= freq_warn:
                            if not conn.execute(
                                "SELECT 1 FROM alertes WHERE id_ruche=? AND type='frequence_warning' AND is_resolved=0",
                                (hive_id,)
                            ).fetchone():
                                to_create.append(("frequence_warning",
                                    f"Fréquence élevée : {freq:.0f} Hz", "warning"))
                        else:
                            conn.execute("""
                                UPDATE alertes SET is_resolved=1 WHERE id_ruche=?
                                AND type IN ('frequence_critique','frequence_warning') AND is_resolved=0
                            """, (hive_id,))

                    for (type_, msg, sev) in to_create:
                        conn.execute(
                            "INSERT INTO alertes (id_ruche, timestamp, type, message, severite) VALUES (?,?,?,?,?)",
                            (hive_id, now, type_, msg, sev),
                        )
                        if sev == "critical":
                            threading.Thread(
                                target=_send_push, args=(hive_id, msg), daemon=True
                            ).start()

                    if to_create:
                        conn.commit()
                        logger.info("Alertes créées pour %s : %s", hive_id, [t[0] for t in to_create])

        except Exception as exc:
            logger.error("Erreur alert_checker : %s", exc)

        await asyncio.sleep(15)


# ---------------------------------------------------------------------------
# Application FastAPI
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    _init_db()

    mqtt_host   = os.getenv("MQTT_HOST", "localhost")
    mqtt_port   = int(os.getenv("MQTT_PORT", 1883))
    hmac_secret = os.getenv("HMAC_SECRET", "dev_secret")
    start_mqtt_subscriber(host=mqtt_host, port=mqtt_port, secret=hmac_secret)

    task = asyncio.create_task(_alert_checker())
    logger.info("Moteur d'alertes démarré")
    yield
    task.cancel()
    logger.info("Arrêt de l'API")


app = FastAPI(
    title="Surveillance Apicole API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hives.router)
app.include_router(alerts.router)
app.include_router(settings.router)
app.include_router(diagnosis.router)
app.include_router(chat.router)
app.include_router(push.router)


@app.get("/")
def read_root():
    return {"message": "Surveillance Apicole API", "docs": "/docs"}


@app.get("/health", tags=["infra"])
def health():
    return {"status": "ok", "database": "RucheIA.db"}
