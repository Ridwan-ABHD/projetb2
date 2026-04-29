import hmac
import hashlib
import json
import logging
import threading
from datetime import datetime, timezone
import sqlite3

# Import de ta connexion simplifiée
from database import get_db_connection

logger = logging.getLogger("mqtt_client")

_HMAC_SECRET = "dev_secret"

def _verify_hmac(payload: dict) -> bool:
    received = payload.get("signature", None)
    if not received: 
        return False
    payload_to_check = {k: v for k, v in payload.items() if k != "signature"}  # ✅
    raw = json.dumps(payload_to_check, sort_keys=True).encode()
    expected = hmac.new(_HMAC_SECRET.encode(), raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(received, expected)

def _on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        if not _verify_hmac(payload):
            logger.warning("Signature HMAC invalide — message ignoré")
            return

        # Extraction des données du message MQTT
        # Note : On adapte aux noms de tes colonnes (temperature, poids, etc.)
        hid = payload.get("hive_id")
        temp = payload.get("temperature_c")
        poids = payload.get("weight_kg")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 1. On insère la nouvelle mesure dans TA table 'mesures'
            cursor.execute("""
                INSERT INTO mesures (id_ruche, timestamp, temperature, poids)
                VALUES (?, ?, ?, ?)
            """, (hid, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), temp, poids))
            
            conn.commit()
            logger.info(f"📥 Données reçues via MQTT pour la ruche {hid}")

    except Exception as e:
        logger.error(f"Erreur lors du traitement MQTT : {e}")

def start_mqtt_subscriber(host: str, port: int, secret: str) -> None:
    global _HMAC_SECRET
    _HMAC_SECRET = secret

    import paho.mqtt.client as mqtt

    def _on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            client.subscribe("apicole/hive/+/sensors")
            logger.info(f" MQTT connecté sur {host}:{port}")
        else:
            logger.error(f" Échec connexion MQTT (code {rc})")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = _on_connect
    client.on_message = _on_message

    try:
        client.connect(host, port, keepalive=60)
        thread = threading.Thread(target=client.loop_forever, daemon=True)
        thread.start()
    except Exception as exc:
        logger.warning(f"⚠️ Broker MQTT indisponible : {exc}")