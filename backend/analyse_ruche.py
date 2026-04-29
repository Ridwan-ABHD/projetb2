import sys
from pathlib import Path
import time
from datetime import datetime
import librosa
import numpy as np
import os 
import random

# Configuration des chemins
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from database import get_db_connection

def son_abeille(debut, fin, nom_wav):
    """Charge un segment audio spécifique."""
    longueur = fin - debut
    # Chemin vers le dossier BDD/audios à la racine du projet
    audio_dir = HERE.parent / "BDD" / "audios"
    chemin_complet = audio_dir / nom_wav

    if not chemin_complet.exists():
        raise FileNotFoundError(f"Fichier audio introuvable : {chemin_complet}")

    # Chargement du segment avec librosa
    y, sr = librosa.load(chemin_complet, offset=debut, duration=longueur)
    return y, sr

def detecter_frequence(y, sr):
    """Calcule la fréquence dominante du signal audio."""
    if len(y) == 0:
        return 0
    spectre = np.abs(librosa.stft(y))
    frequences = librosa.fft_frequencies(sr=sr)
    # On trouve la fréquence dominante (pic d'énergie moyenne)
    index_max = np.argmax(np.mean(spectre, axis=1))
    return frequences[index_max]

def executer_analyse():
    """Script principal d'analyse qui met à jour la base de données."""
    print(f"\n--- 🔎 ANALYSE IA EN COURS ({datetime.now().strftime('%H:%M:%S')}) ---")
    
    try:
        with get_db_connection() as conn:
            curseur = conn.cursor()

            # 1. On récupère la liste des ruches qui ont des mesures en base
            curseur.execute("SELECT DISTINCT id_ruche FROM mesures")
            ruches_a_traiter = curseur.fetchall()

            if not ruches_a_traiter:
                print("😴 Aucune mesure trouvée dans la base. Lance le simulateur !")
                return

            for (id_ruche,) in ruches_a_traiter:
                # 2. On cherche un fichier audio associé à cette ruche
                # On utilise LIMIT 1 pour simplifier la démo
                curseur.execute("""
                    SELECT nom_fichier, id_audio FROM enregistrements 
                    WHERE id_ruche = ? LIMIT 1
                """, (id_ruche,))
                audio = curseur.fetchone()

                if audio:
                    nom_fichier, id_audio = audio
                    
                    # 3. Récupération des segments 'bee' (abeilles)
                    curseur.execute("""
                        SELECT debut, fin FROM segments 
                        WHERE id_audio = ? AND label = 'bee'
                    """, (id_audio,))
                    segments = curseur.fetchall()
                    
                    frequences_calculees = []
                    for debut, fin in segments:
                        try:
                            y, sr = son_abeille(debut, fin, nom_fichier)
                            freq = detecter_frequence(y, sr)
                            if freq > 0:
                                frequences_calculees.append(freq)
                        except Exception:
                            continue

                    if frequences_calculees:
                        # Calcul de la moyenne + petite variation pour le dynamisme sur Angular
                        freq_moyenne = np.mean(frequences_calculees)
                        freq_finale = round(float(freq_moyenne) + random.uniform(-2, 2), 2)
                        
                        # 4. MISE À JOUR : On applique la fréquence à TOUTES les lignes de cette ruche
                        # On a enlevé "AND frequence_moyenne IS NULL" comme demandé
                        curseur.execute("""
                            UPDATE mesures 
                            SET frequence_moyenne = ? 
                            WHERE id_ruche = ?
                        """, (freq_finale, id_ruche))
                        
                        conn.commit()
                        print(f"✅ {id_ruche} : {len(frequences_calculees)} segments analysés -> {freq_finale} Hz")
                        
                        # Petite pause pour laisser le temps au MQTT d'écrire sans bloquer la base
                        time.sleep(0.5)
                    else:
                        print(f"⚠️ {id_ruche} : Aucun segment 'bee' valide dans {nom_fichier}")
                else:
                    print(f"❓ {id_ruche} : Aucun fichier audio trouvé dans la table 'enregistrements'")

    except Exception as e:
        print(f"❌ Erreur SQL ou système : {e}")

# --- BOUCLE DE LANCEMENT ---
if __name__ == "__main__":
    print("========================================")
    print("🐝 MOTEUR D'ANALYSE ACOUSTIQUE DÉMARRÉ")
    print("========================================")
    
    while True:
        try:
            executer_analyse()
        except KeyboardInterrupt:
            print("\n👋 Arrêt du script d'analyse.")
            break
        except Exception as e:
            print(f"💥 Erreur fatale : {e}")
        
        # Pause de 10 secondes avant la prochaine analyse
        print("\n😴 En attente de nouvelles données (10s)...")
        time.sleep(10)