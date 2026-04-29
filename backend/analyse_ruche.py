from database import get_db_connection
import librosa
import numpy as np
import os 

def son_abeille(debut, fin, nom_wav):
    longueur = fin - debut
    # On cherche l'audio dans le dossier "audio"
    chemin_complet = os.path.join("audio", nom_wav) 
    y, sr = librosa.load(chemin_complet, offset=debut, duration=longueur)
    return y, sr

def detecter_frequence(y, sr):
    spectre = np.abs(librosa.stft(y))
    frequence = librosa.fft_frequencies(sr=sr)
    # On trouve la fréquence dominante (pic d'énergie)
    index_max = np.argmax(np.mean(spectre, axis=1))
    return frequence[index_max]

# --- DÉBUT DU TRAITEMENT ---

with get_db_connection() as conn:
    curseur = conn.cursor()

    # 1. On récupère les fichiers audio qui ont des segments marqués 'bee'
    curseur.execute("""
        SELECT DISTINCT e.id_audio, e.id_ruche, e.nom_fichier
        FROM enregistrements e
        JOIN segments s ON s.id_audio = e.id_audio
        WHERE s.label = 'bee'
    """)
    enregistrements = curseur.fetchall()

    for id_audio, id_ruche, nom_fichier in enregistrements:
        # 2. Récupère tous les segments 'bee' pour cet audio précis
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
                frequences.append(freq)
            except Exception as e:
                print(f"  ⚠️ Segment [{debut:.2f}s - {fin:.2f}s] ignoré : {e}")

        # 3. Si on a réussi à calculer des fréquences
        if frequences:
            freq_moyenne = round(float(np.mean(frequences)), 2)
            print(f"🐝 {nom_fichier} ({id_ruche}) → {len(frequences)} segments → {freq_moyenne:.2f} Hz")

            # 4. MISE À JOUR CIBLÉE : 
            # On met à jour la fréquence pour les mesures de cette ruche 
            # UNIQUEMENT là où la fréquence n'a pas encore été renseignée.
            curseur.execute("""
                UPDATE mesures 
                SET frequence_moyenne = ? 
                WHERE id_ruche = ? 
            """, (freq_moyenne, id_ruche))
            
            conn.commit()
            print(f"  ✅ Base de données mise à jour pour la ruche {id_ruche}.")
        else:
            print(f"  ❌ Aucune fréquence calculée pour {nom_fichier}.")

    print("\n🏁 Analyse terminée. Ta table 'mesures' contient maintenant les diagnostics IA.")