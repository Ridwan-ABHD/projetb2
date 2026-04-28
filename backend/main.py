import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import SessionLocal, engine
from models import Base, Hive
from mqtt_client import start_mqtt_subscriber
from routers import alerts, chat, diagnosis, hives, settings

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

_HIVES_SEED = [
    {"id": 1, "name": "Ruche n°1", "location": "La Clairière"},
    {"id": 2, "name": "Ruche n°2", "location": "Verger Sud"},
    {"id": 3, "name": "Ruche n°3", "location": "Prairie Est"},
    {"id": 4, "name": "Ruche n°4", "location": "Lisière Nord"},
    {"id": 5, "name": "Ruche n°5", "location": "Pommeraie"},
    {"id": 6, "name": "Ruche n°6", "location": "Bord de l'étang"},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for data in _HIVES_SEED:
            if not db.get(Hive, data["id"]):
                db.add(Hive(**data))
        db.commit()
    finally:
        db.close()

    start_mqtt_subscriber(
        host=os.getenv("MQTT_HOST", "localhost"),
        port=int(os.getenv("MQTT_PORT", 1883)),
        secret=os.getenv("HMAC_SECRET", "dev_secret"),
    )

    yield


app = FastAPI(
    title="Surveillance Apicole API",
    description="API de surveillance de ruches connectées — analyse acoustique IA",
    version="1.0.0",
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


@app.get("/health", tags=["infra"])
def health():
    return {"status": "ok", "service": "Surveillance Apicole API"}
