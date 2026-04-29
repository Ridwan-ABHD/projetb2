import sqlite3
from contextlib import contextmanager

DB_PATH = "RucheIA.db"

@contextmanager
def get_db_connection():
    """Permet d'ouvrir et fermer la connexion SQL proprement."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par nom (ex: row['poids'])
    try:
        yield conn
    finally:
        conn.close()