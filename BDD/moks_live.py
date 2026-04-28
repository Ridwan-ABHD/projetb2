import sqlite3
import pandas as pd
import time
import random
from datetime import datetime

# --- CONFIGURATION ---
DB_NAME = 'RucheIA.db'
FICHIER_TEMP = 'temperature_2017.csv'
FICHIER_POIDS = 'weight_2017.csv'
DELAI_ENVOI = 5  # secondes entre chaque mesure

def simulation_live():
    # 1. Chargement des données sources (tes archives réelles)
    print("📂 Chargement des fichiers de données historiques...")
    try:
        df_temp = pd.read_csv(FICHIER_TEMP)
        df_weight = pd.read_csv(FICHIER_POIDS)
    except FileNotFoundError as e:
        print(f"❌ Erreur : Fichier introuvable. Vérifie les noms. {e}")
        return

    print("🚀 Lancement du simulateur (Appuie sur Ctrl+C pour arrêter)")
    print("-" * 50)

    try:
        while True:
            # 2. Connexion à la base de données
            # On utilise un timeout pour éviter les erreurs "database is locked"
            conn = sqlite3.connect(DB_NAME, timeout=10)
            curseur = conn.cursor()

            # 3. Récupération des ruches actives dans ta base
            curseur.execute("SELECT id_ruche FROM ruches")
            ruches = [r[0] for r in curseur.fetchall()]

            # 4. Pour chaque ruche, on envoie une donnée "Live"
            for id_ruche in ruches:
                # On pioche un index au hasard dans les fichiers
                idx = random.randint(0, len(df_temp) - 1)
                
                # Extraction des valeurs
                val_temp = round(float(df_temp['temperature'].iloc[idx]), 2)
                # On utilise modulo (%) au cas où le fichier poids n'a pas la même longueur
                val_poids = round(float(df_weight['weight'].iloc[idx % len(df_weight)]), 2)
                
                # Heure actuelle pour simuler le "maintenant"
                maintenant = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # 5. Insertion dans la table 'mesures'
                requete = """
                    INSERT INTO mesures (id_ruche, timestamp, temperature, poids) 
                    VALUES (?, ?, ?, ?)
                """
                curseur.execute(requete, (id_ruche, maintenant, val_temp, val_poids))
                
                print(f"📡 [{maintenant}] Ruche {id_ruche} -> {val_temp}°C | {val_poids}kg")

            # 6. Sauvegarde et fermeture de la connexion pour ce cycle
            conn.commit()
            conn.close()

            # 7. Pause avant la prochaine salve de données
            time.sleep(DELAI_ENVOI)

    except KeyboardInterrupt:
        print("\n🛑 Simulation arrêtée par l'utilisateur.")
    except Exception as e:
        print(f"\n⚠️ Une erreur est survenue : {e}")

# Lancement du programme
if __name__ == "__main__":
    simulation_live()