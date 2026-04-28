import sqlite3
import pandas as pd

def peupler_monde_reel():
    conn = sqlite3.connect('RucheIA.db', timeout=10)
    cur = conn.cursor()
    
    # 1. Nettoyage
    cur.execute("DELETE FROM mesures")
    print(" Table 'mesures' vidée.")

    # 2. Chargement des fichiers avec les bons noms
    df_temp = pd.read_csv('temperature_2017.csv')
    df_weight = pd.read_csv('weight_2017.csv') # Le nom exact de ton fichier

    # 3. Récupération de tes ruches
    cur.execute("SELECT id_ruche FROM ruches")
    liste_ruches = [r[0] for r in cur.fetchall()]

    print(f" Injection des données réelles pour : {liste_ruches}...")
    
    # On va insérer les 500 premières lignes pour l'exemple
    for i in range(500):
        for ruche in liste_ruches:
            # Correction ici : on utilise 'weight' au lieu de 'poids'
            val_temp = float(df_temp['temperature'].iloc[i % len(df_temp)])
            val_poids = float(df_weight['weight'].iloc[i % len(df_weight)])
            
            cur.execute("""
                INSERT INTO mesures (id_ruche, temperature, poids) 
                VALUES (?, ?, ?)
            """, (ruche, round(val_temp, 2), round(val_poids, 2)))

    conn.commit()
    conn.close()
    print(" Félicitations ! Ton monde virtuel est prêt avec des données 100% réelles.")

# Lance-le (en fermant DB Browser avant)
peupler_monde_reel()