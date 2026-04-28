import hmac
import hashlib
import json
import logging
import threading
from datetime import datetime, timezone

from database import SessionLocal
from models import Alert, Hive, SensorReading, Threshold

logger = logging.getLogger("mqtt_client")

_HMAC_SECRET = "dev_secret"

_THRESHOLD_DEFAULTS = {
    "freq_warning": 260.0,
    "freq_critical": 280.0,
    "temp_warning": 36.0,
    "temp_critical": 38.0,
    "weight_drop_threshold": 2.0,
}


def _verify_hmac(payload: dict) -> bool:
    received = payload.pop("signature", None)
    if not received:
        return False
    raw = json.dumps(payload, sort_keys=True).encode()
    expected = hmac.new(_HMAC_SECRET.encode(), raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(received, expected)


def _load_thresholds(db) -> dict:
    result = dict(_THRESHOLD_DEFAULTS)
    for row in db.query(Threshold).all():
        result[row.key] = row.value
    return result


def _evaluate_and_alert(db, hive: Hive, reading: SensorReading, thresholds: dict):
    new_status = "normal"

    if reading.frequency_hz >= thresholds["freq_critical"]:
        db.add(Alert(
            hive_id=hive.id,
            type="SWARMING",
            message=f"Fréquence critique : {reading.frequency_hz:.0f} Hz — Risque d'essaimage élevé",
            severity="critical",
        ))
        new_status = "critical"
    elif reading.frequency_hz >= thresholds["freq_warning"]:
        db.add(Alert(
            hive_id=hive.id,
            type="SWARMING",
            message=f"Fréquence élevée : {reading.frequency_hz:.0f} Hz — À surveiller",
            severity="warning",
        ))
        if new_status == "normal":
            new_status = "warning"

    if reading.temperature_c >= thresholds["temp_critical"]:
        db.add(Alert(
            hive_id=hive.id,
            type="THERMAL_STRESS",
            message=f"Température critique : {reading.temperature_c:.1f}°C",
            severity="critical",
        ))
        new_status = "critical"
    elif reading.temperature_c >= thresholds["temp_warning"]:
        db.add(Alert(
            hive_id=hive.id,
            type="THERMAL_STRESS",
            message=f"Température élevée : {reading.temperature_c:.1f}°C",
            severity="warning",
        ))
        if new_status == "normal":
            new_status = "warning"

    hive.status = new_status
    db.commit()


def _on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        if not _verify_hmac(payload):
            logger.warning("Signature HMAC invalide — message ignoré (%s)", msg.topic)
            return

        hive_id = payload.get("hive_id")
        db = SessionLocal()
        try:
            hive = db.get(Hive, hive_id)
            if not hive:
                logger.warning("Ruche %s inconnue — données ignorées", hive_id)
                return

            reading = SensorReading(
                hive_id=hive_id,
                timestamp=datetime.now(timezone.utc),
                frequency_hz=payload["frequency_hz"],
                temperature_c=payload["temperature_c"],
                humidity_pct=payload["humidity_pct"],
                weight_kg=payload["weight_kg"],
            )
            db.add(reading)
            db.flush()

            thresholds = _load_thresholds(db)
            _evaluate_and_alert(db, hive, reading, thresholds)
        finally:
            db.close()

    except Exception:
        logger.exception("Erreur lors du traitement du message MQTT")


def start_mqtt_subscriber(host: str, port: int, secret: str) -> None:
    global _HMAC_SECRET
    _HMAC_SECRET = secret

    import paho.mqtt.client as mqtt

    def _on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            client.subscribe("apicole/hive/+/sensors")
            logger.info("MQTT connecté — abonné à apicole/hive/+/sensors")
        else:
            logger.error("MQTT connexion refusée (code %s)", rc)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = _on_connect
    client.on_message = _on_message

    try:
        client.connect(host, port, keepalive=60)
        thread = threading.Thread(target=client.loop_forever, daemon=True, name="mqtt-subscriber")
        thread.start()
        logger.info("MQTT subscriber démarré sur %s:%s", host, port)
    except Exception as exc:
        logger.warning("Broker MQTT non disponible (%s) — mode hors-ligne", exc)
