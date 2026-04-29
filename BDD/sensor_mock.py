import hashlib
import hmac
import json
import logging
import os
import random
import time
import pandas as pd
from datetime import datetime, timezone
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("sensor_mock")

# Configuration
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
HMAC_SECRET = os.getenv("HMAC_SECRET", "dev_secret")
INTERVAL = int(os.getenv("MOCK_INTERVAL", 5))

# Tes ruches réelles (photo)
HIVES = [
    {"id": "CF003", "base_freq": 230},
    {"id": "CJ001", "base_freq": 245},
    {"id": "H1",    "base_freq": 280},
]

def _sign(data: dict) -> str:
    raw = json.dumps(data, sort_keys=True).encode()
    return hmac.new(HMAC_SECRET.encode(), raw, hashlib.sha256).hexdigest()

def main():
    # Chargement des fichiers sources
    try:
        df_temp = pd.read_csv('temperature_2017.csv')
        df_weight = pd.read_csv('weight_2017.csv')
    except Exception as e:
        logger.error(f"Erreur fichiers CSV : {e}")
        return

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    
    try:
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
        client.loop_start()
        logger.info(f"🚀 Simulateur IoT actif sur {MQTT_HOST}:{MQTT_PORT}")
    except Exception as e:
        logger.error(f"Impossible de se connecter au broker : {e}")
        return

    try:
        while True:
            for hive in HIVES:
                # On pioche une donnée réelle de 2017
                idx = random.randint(0, len(df_temp) - 1)
                
                # Simulation de la fréquence IA (basée sur l'état de la ruche)
                # Si c'est H1, on simule une fréquence haute pour déclencher des alertes
                freq_ia = hive["base_freq"] + random.uniform(-5, 30)

                payload = {
                    "hive_id": hive["id"],
                    "temperature_c": round(float(df_temp['temperature'].iloc[idx]), 2),
                    "weight_kg": round(float(df_weight['weight'].iloc[idx % len(df_weight)]), 2),
                    "ts": datetime.now(timezone.utc).isoformat(),
                }
                
                # Signature de sécurité
                payload["signature"] = _sign({k: v for k, v in payload.items()})
                
                # Publication
                topic = f"apicole/hive/{hive['id']}/sensors"
                client.publish(topic, json.dumps(payload))
                
                logger.info(f"📡 MQTT [Sent] | {hive['id']} | {payload['temperature_c']}°C | {payload['weight_kg']}kg")
            
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        client.loop_stop()

if __name__ == "__main__":
    main()