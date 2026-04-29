import hmac
import hashlib
import json
import logging
import os
import threading
from datetime import datetime

from database import get_db_connection

logger = logging.getLogger("mqtt_client")

_HMAC_SECRET = "dev_secret"

# Seuil de température pour déclencher un push critique
_TEMP_CRITICAL = 38.0


def _verify_hmac(payload: dict) -> bool:
    received = payload.get("signature", None)
    if not received:
        return False
    payload_to_check = {k: v for k, v in payload.items() if k != "signature"}
    raw = json.dumps(payload_to_check, sort_keys=True).encode()
    expected = hmac.new(_HMAC_SECRET.encode(), raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(received, expected)


def _send_push_notifications(hive_id, temp: float):
    vapid_private_key = os.getenv("VAPID_PRIVATE_KEY")
    vapid_email = os.getenv("VAPID_EMAIL", "mailto:admin@surveillance-apicole.fr")

    if not vapid_private_key:
        logger.warning("Clés VAPID non configurées — push ignoré")
        return

    try:
        from pywebpush import webpush, WebPushException  # type: ignore[import]
    except ImportError:
        logger.warning("pywebpush non installé — push ignoré")
        return

    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT id, endpoint, subscription_json FROM push_subscriptions"
        ).fetchall()

    if not rows:
        return

    data = json.dumps({
        "title": f"Alerte critique — Ruche {hive_id}",
        "body": f"Température critique : {temp:.1f}°C",
        "icon": "/icons/icon-192.png",
        "url": "/",
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
        except WebPushException as exc:
            status = getattr(exc.response, "status_code", None) if exc.response else None
            if status in (404, 410):
                stale.append(row["id"])
            else:
                logger.warning("Push échoué pour %s : %s", row["endpoint"][:40], exc)
        except Exception as exc:
            logger.warning("Erreur push : %s", exc)

    if stale:
        with get_db_connection() as conn:
            for sid in stale:
                conn.execute("DELETE FROM push_subscriptions WHERE id = ?", (sid,))
            conn.commit()


def _on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        if not _verify_hmac(payload):
            logger.warning("Signature HMAC invalide — message ignoré")
            return

        hid = payload.get("hive_id")
        temp = payload.get("temperature_c")
        poids = payload.get("weight_kg")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            # On insère uniquement les données physiques (l'IA fera l'UPDATE plus tard)
            cursor.execute("""
                INSERT INTO mesures (id_ruche, timestamp, temperature, poids)
                VALUES (?, ?, ?, ?)
            """, (
                hid,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                temp,
                poids,
            ))
            conn.commit()
            
            # LOG PROPRE : Plus de mention de fréquence ici !
            logger.info(f"📥 Données IoT reçues | Ruche: {hid} | Temp: {temp}°C | Poids: {poids}kg")

    except Exception as e:
        logger.error(f"Erreur lors du traitement MQTT : {e}")


def start_mqtt_subscriber(host: str, port: int, secret: str) -> None:
    global _HMAC_SECRET
    _HMAC_SECRET = secret

    import paho.mqtt.client as mqtt

    def _on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            client.subscribe("apicole/hive/+/sensors")
            logger.info(f"MQTT connecté sur {host}:{port}")
        else:
            logger.error(f"Échec connexion MQTT (code {rc})")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = _on_connect
    client.on_message = _on_message

    try:
        client.connect(host, port, keepalive=60)
        thread = threading.Thread(target=client.loop_forever, daemon=True)
        thread.start()
    except Exception as exc:
        logger.warning(f"⚠️ Broker MQTT indisponible : {exc}")
