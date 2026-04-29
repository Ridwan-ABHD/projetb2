import json
from fastapi import APIRouter, HTTPException

from database import get_db_connection
from schemas import PushSubscriptionIn

router = APIRouter(prefix="/api/push", tags=["push"])


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


@router.post("/subscribe", status_code=201)
def subscribe(sub: PushSubscriptionIn):
    _ensure_table()
    subscription = sub.subscription
    endpoint = subscription.get("endpoint")
    if not endpoint:
        raise HTTPException(status_code=400, detail="endpoint manquant")

    subscription_json = json.dumps(subscription)
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
        conn.commit()

    return {"status": "subscribed"}
