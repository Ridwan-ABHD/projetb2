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

# --- CONFIGURATION ---
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
HMAC_SECRET = os.getenv("HMAC_SECRET", "dev_secret")
INTERVAL = int(os.getenv("MOCK_INTERVAL", 5))

# Tes ruches réelles
HIVES = [
    {"id": "CF003", "base_freq": 230},
    {"id": "CJ001", "base_freq": 245},
    {"id": "H1",    "base_freq": 280},
]

def _sign(data: dict) -> str:
    """Génère la signature de sécurité pour le backend."""
    raw = json.dumps(data, sort_keys=True).encode()
    return hmac.new(HMAC_SECRET.encode(), raw, hashlib.sha256).hexdigest()

def main():
    try:
        # On charge les fichiers CSV
        df_temp = pd.read_csv('temperature_2017.csv')
        df_weight = pd.read_csv('weight_2017.csv')
        total_rows = min(len(df_temp), len(df_weight))
        logger.info(f"📊 Mode Séquentiel activé : {total_rows} lignes à traiter.")
    except Exception as e:
        logger.error(f"Erreur fichiers CSV : {e}")
        return

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    
    try:
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
        client.loop_start()
        logger.info(f"🚀 Simulateur IoT actif sur {MQTT_HOST}:{MQTT_PORT}")
    except Exception as e:
        logger.error(f"Erreur connexion MQTT : {e}")
        return

    current_idx = 0

    try:
        while True:
            # On prend la ligne correspondant à l'index actuel
            val_temp = round(float(df_temp['temperature'].iloc[current_idx]), 2)
            val_weight = round(float(df_weight['weight'].iloc[current_idx]), 2)

            for hive in HIVES:
                # On prépare le message SANS fréquence (l'IA le remplira plus tard)
                payload = {
                    "hive_id": hive["id"],
                    "temperature_c": val_temp,
                    "weight_kg": val_weight,
                    "ts": datetime.now(timezone.utc).isoformat(),
                }
                
                # Signature HMAC pour que le backend accepte le message
                payload["signature"] = _sign({k: v for k, v in payload.items()})
                
                topic = f"apicole/hive/{hive['id']}/sensors"
                client.publish(topic, json.dumps(payload))
                
                logger.info(f"📡 Index {current_idx} | Ruche {hive['id']} | {val_temp}°C | {val_weight}kg")
            
            # Incrémentation de l'index pour la prochaine boucle
            current_idx = (current_idx + 1) % total_rows
            
            time.sleep(INTERVAL)
            
    except KeyboardInterrupt:
        client.loop_stop()
        logger.info("Arrêt du simulateur.")

if __name__ == "__main__":
    main()