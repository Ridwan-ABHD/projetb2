import sqlite3
import os

def importer_tout_proprement(fichiers_lab):
    conn = sqlite3.connect('RucheIA.db')
    curseur = conn.cursor()

    # NETTOYAGE : On vide tout pour repartir sur une base saine (sans les NULL)
    curseur.execute("DELETE FROM segments")
    curseur.execute("DELETE FROM enregistrements")
    
    fichiers = os.listdir(fichiers_lab)
    for fichier in fichiers:
        if fichier.endswith('.lab'):
            chemin_complet = os.path.join(fichiers_lab, fichier)
            nom_wav = fichier.replace(".lab", ".wav")
            
            # --- EXTRACTION AUTOMATIQUE DES INFOS ---
            id_ruche = fichier.split(' - ')[0] if ' - ' in fichier else "Hive1"
            
            # Détection de l'état
            if "Missing Queen" in fichier:
                etat = "Missing Queen"
            elif "Active" in fichier:
                etat = "Active"
            elif "QueenBee" in fichier:
                etat = "Queen"
            else:
                etat = "Unknown"

            print(f"Importation : {nom_wav} ({etat})")

            # 1. Remplissage de la table ENREGISTREMENTS
            curseur.execute("""
                INSERT INTO enregistrements (nom_fichier, id_ruche, etat_reel, moment_journee) 
                VALUES (?, ?, ?, ?)
            """, (nom_wav, id_ruche, etat, "Day"))
            
            id_audio_parent = curseur.lastrowid
            
            # 2. Remplissage de la table SEGMENTS
            with open(chemin_complet, 'r', encoding='utf-8') as f:
                for ligne in f:
                    elements = ligne.strip().split()
                    if len(elements) == 3:
                        curseur.execute("""
                            INSERT INTO segments (debut, fin, label, nom_fichier, id_audio) 
                            VALUES (?, ?, ?, ?, ?)
                        """, (float(elements[0]), float(elements[1]), elements[2], nom_wav, id_audio_parent))

    conn.commit()
    conn.close()
    print("\n✅ Base de données réinitialisée et mise à jour proprement !")

# Lancement
importer_tout_proprement("fichiers_lab")