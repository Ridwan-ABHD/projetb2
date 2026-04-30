import hashlib
import hmac
import json
import logging
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import librosa
import numpy as np
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# --- Chemin vers database.py (dans le même dossier BDD/) ---
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from database import get_db_connection

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("analyse_ruche")

# --- CONFIGURATION (identique à sensor_mock.py) ---
MQTT_HOST   = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT   = int(os.getenv("MQTT_PORT", 1883))
HMAC_SECRET = os.getenv("HMAC_SECRET", "dev_secret")
INTERVAL    = 10  # secondes entre chaque analyse


# --- SIGNATURE HMAC (identique à sensor_mock.py) ---
def _sign(data: dict) -> str:
    raw = json.dumps(data, sort_keys=True).encode()
    return hmac.new(HMAC_SECRET.encode(), raw, hashlib.sha256).hexdigest()


# --- ANALYSE AUDIO ---
def son_abeille(debut, fin, nom_wav):
    longueur = fin - debut
    audio_dir = HERE.parent / "BDD" / "audios"
    chemin_complet = audio_dir / nom_wav
    if not chemin_complet.exists():
        raise FileNotFoundError(f"Fichier audio introuvable : {chemin_complet}")
    y, sr = librosa.load(str(chemin_complet), offset=debut, duration=longueur)
    return y, sr


def detecter_frequence(y, sr):
    if len(y) == 0:
        return 0
    spectre = np.abs(librosa.stft(y))
    frequences = librosa.fft_frequencies(sr=sr)
    index_max = np.argmax(np.mean(spectre, axis=1))
    return frequences[index_max]


# --- ANALYSE + ENVOI MQTT ---
def executer_analyse(client: mqtt.Client):
    logger.info(f"🔎 Analyse acoustique en cours ({datetime.now().strftime('%H:%M:%S')})")

    try:
        with get_db_connection() as conn:
            curseur = conn.cursor()

            # 1. Ruches qui ont des enregistrements audio avec segments 'bee'
            curseur.execute("""
                SELECT DISTINCT e.id_audio, e.id_ruche, e.nom_fichier
                FROM enregistrements e
                JOIN segments s ON s.id_audio = e.id_audio
                WHERE s.label = 'bee'
            """)
            enregistrements = curseur.fetchall()

            if not enregistrements:
                logger.warning("Aucun enregistrement 'bee' trouvé. Lance lab.py d'abord !")
                return

            for id_audio, id_ruche, nom_fichier in enregistrements:
                # 2. Segments 'bee' pour cet audio
                curseur.execute("""
                    SELECT debut, fin FROM segments
                    WHERE id_audio = ? AND label = 'bee'
                """, (id_audio,))
                segments = curseur.fetchall()

                frequences = []
                for debut, fin in segments:
                    try:
                        y, sr = son_abeille(debut, fin, nom_fichier)
                        freq = detecter_frequence(y, sr)
                        if freq > 0:
                            frequences.append(freq)
                    except Exception as e:
                        logger.warning(f"Segment [{debut:.2f}s-{fin:.2f}s] ignoré : {e}")

                if frequences:
                    # Petite variation pour dynamisme
                    freq_finale = round(float(np.mean(frequences)) + random.uniform(-2, 2), 2)

                    # 3. On publie sur MQTT au lieu d'écrire directement en BDD
                    payload = {
                        "hive_id":      id_ruche,
                        "frequency_hz": freq_finale,
                        "ts":           datetime.now(timezone.utc).isoformat(),
                    }
                    payload["signature"] = _sign({k: v for k, v in payload.items()})

                    topic = f"apicole/hive/{id_ruche}/frequency"
                    client.publish(topic, json.dumps(payload))

                    logger.info(f"📡 MQTT [Freq] | {id_ruche} | {freq_finale} Hz")
                else:
                    logger.warning(f"Aucune fréquence calculée pour {nom_fichier}")

    except Exception as e:
        logger.error(f"Erreur analyse : {e}")


# --- PROGRAMME PRINCIPAL ---
def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    try:
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
        client.loop_start()
        logger.info(f"🚀 Moteur acoustique actif sur {MQTT_HOST}:{MQTT_PORT}")
    except Exception as e:
        logger.error(f"Impossible de se connecter au broker MQTT : {e}")
        return

    try:
        while True:
            executer_analyse(client)
            logger.info(f"😴 Prochaine analyse dans {INTERVAL}s...")
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        client.loop_stop()
        logger.info("👋 Arrêt du moteur acoustique.")


if __name__ == "__main__":
    main()