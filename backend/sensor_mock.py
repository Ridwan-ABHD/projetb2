#!/usr/bin/env python3
"""
Simulateur de capteurs IoT — Surveillance Apicole
Simule 6 ruches et publie les données via MQTT avec signature HMAC-SHA256.

Usage:
    python sensor_mock.py

Variables d'environnement:
    MQTT_HOST       Adresse du broker (défaut: localhost)
    MQTT_PORT       Port du broker (défaut: 1883)
    HMAC_SECRET     Clé secrète partagée avec le backend
    MOCK_INTERVAL   Secondes entre chaque envoi (défaut: 5)
"""
import hashlib
import hmac
import json
import logging
import math
import os
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("sensor_mock")

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
HMAC_SECRET = os.getenv("HMAC_SECRET", "dev_secret")
INTERVAL = int(os.getenv("MOCK_INTERVAL", 5))

# Profil de chaque ruche : base_freq et anomaly pilotent la simulation
HIVES = [
    {"id": 1, "name": "La Clairière",      "base_freq": 230, "anomaly": None},
    {"id": 2, "name": "Verger Sud",        "base_freq": 245, "anomaly": "warning"},
    {"id": 3, "name": "Prairie Est",       "base_freq": 255, "anomaly": "critical"},
    {"id": 4, "name": "Lisière Nord",      "base_freq": 225, "anomaly": None},
    {"id": 5, "name": "Pommeraie",         "base_freq": 238, "anomaly": "disease"},
    {"id": 6, "name": "Bord de l'étang",  "base_freq": 220, "anomaly": None},
]

# Poids initial de chaque ruche (kg)
_weights: dict[int, float] = {h["id"]: 35.0 + random.uniform(-5, 5) for h in HIVES}


def _sign(data: dict) -> str:
    raw = json.dumps(data, sort_keys=True).encode()
    return hmac.new(HMAC_SECRET.encode(), raw, hashlib.sha256).hexdigest()


def _generate_reading(hive: dict) -> dict:
    hid = hive["id"]
    anomaly = hive["anomaly"]

    # Cycle circadien : température max en milieu de journée
    hour = datetime.now(timezone.utc).hour + datetime.now(timezone.utc).minute / 60
    temp_base = 34.0 + 1.5 * math.sin(math.pi * (hour - 6) / 12)

    if anomaly == "critical":
        freq = hive["base_freq"] + random.uniform(20, 40)   # 275–295 Hz
        temp = temp_base + random.uniform(2, 4)
    elif anomaly == "warning":
        freq = hive["base_freq"] + random.uniform(10, 20)   # 255–265 Hz
        temp = temp_base + random.uniform(1, 2)
    elif anomaly == "disease":
        freq = hive["base_freq"] + random.uniform(-10, 10)
        temp = temp_base + random.uniform(0.5, 1.5)
    else:
        freq = hive["base_freq"] + random.uniform(-15, 15)
        temp = temp_base + random.uniform(-0.5, 0.5)

    humidity = 62.0 + random.uniform(-8, 8)

    # Poids : augmentation lente (miellée), chute possible en cas d'essaimage critique
    if anomaly == "critical" and random.random() < 0.1:
        _weights[hid] -= random.uniform(1, 3)
    else:
        _weights[hid] += random.uniform(-0.05, 0.15)

    payload = {
        "hive_id": hid,
        "frequency_hz": round(freq, 2),
        "temperature_c": round(temp, 2),
        "humidity_pct": round(humidity, 2),
        "weight_kg": round(_weights[hid], 3),
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    payload["signature"] = _sign({k: v for k, v in payload.items()})
    return payload


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    def on_connect(c, userdata, flags, rc, properties=None):
        if rc == 0:
            logger.info("Connecté au broker MQTT %s:%s", MQTT_HOST, MQTT_PORT)
        else:
            logger.error("Connexion refusée (code %s)", rc)

    client.on_connect = on_connect
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()

    logger.info("Simulation démarrée — %d ruches · intervalle %ds", len(HIVES), INTERVAL)

    try:
        while True:
            for hive in HIVES:
                data = _generate_reading(hive)
                topic = f"apicole/hive/{hive['id']}/sensors"
                client.publish(topic, json.dumps(data))
                logger.info(
                    "Ruche %d · %-20s | %5.0f Hz | %4.1f°C | %3.0f%% | %5.2f kg",
                    hive["id"], hive["name"],
                    data["frequency_hz"], data["temperature_c"],
                    data["humidity_pct"], data["weight_kg"],
                )
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        logger.info("Simulation arrêtée.")
        client.loop_stop()


if __name__ == "__main__":
    main()
