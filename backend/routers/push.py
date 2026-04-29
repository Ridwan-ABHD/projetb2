import json
import logging
import threading
from fastapi import APIRouter, HTTPException

from database import get_db_connection
from schemas import PushSubscriptionIn
from push_utils import webpush_send

router = APIRouter(prefix="/api/push", tags=["push"])
logger = logging.getLogger("push")


def _ensure_table():
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS push_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT UNIQUE NOT NULL,
                subscription_json TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()


def _push_existing_criticals_to(subscription_json: str):
    """Envoie les alertes critiques actives à un nouvel abonné."""
    with get_db_connection() as conn:
        alerts = conn.execute("""
            SELECT id_ruche, message FROM alertes
            WHERE severite = 'critical' AND is_resolved = 0
            ORDER BY timestamp DESC
        """).fetchall()

    seen = set()
    sub_info = json.loads(subscription_json)
    for a in alerts:
        hive_id = a["id_ruche"]
        if hive_id not in seen:
            seen.add(hive_id)
            webpush_send(sub_info, hive_id, a["message"])


@router.post("/subscribe", status_code=201)
def subscribe(sub: PushSubscriptionIn):
    _ensure_table()
    subscription = sub.subscription
    endpoint = subscription.get("endpoint")
    if not endpoint:
        raise HTTPException(status_code=400, detail="endpoint manquant")

    subscription_json = json.dumps(subscription)
    is_new = False
    with get_db_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM push_subscriptions WHERE endpoint = ?", (endpoint,)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE push_subscriptions SET subscription_json = ? WHERE endpoint = ?",
                (subscription_json, endpoint),
            )
        else:
            conn.execute(
                "INSERT INTO push_subscriptions (endpoint, subscription_json) VALUES (?, ?)",
                (endpoint, subscription_json),
            )
            is_new = True
        conn.commit()

    if is_new:
        logger.info("Nouvel abonné — envoi des alertes critiques actives")
        threading.Thread(
            target=_push_existing_criticals_to,
            args=(subscription_json,),
            daemon=True,
        ).start()

    return {"status": "subscribed"}
