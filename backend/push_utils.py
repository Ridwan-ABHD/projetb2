import json
import logging
import os

logger = logging.getLogger("push_utils")


def webpush_send(subscription_info: dict, hive_id: str, message: str) -> int | None:
    """Envoie une push notification. Retourne le status HTTP en cas d'erreur, None si OK."""
    vapid_private_key = os.getenv("VAPID_PRIVATE_KEY")
    vapid_email = os.getenv("VAPID_EMAIL", "mailto:admin@surveillance-apicole.fr")
    if not vapid_private_key:
        logger.warning("VAPID_PRIVATE_KEY non configurée — push ignoré")
        return None
    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        logger.warning("pywebpush non installé — push ignoré")
        return None

    data = json.dumps({
        "title": f"Alerte — Ruche {hive_id}",
        "body":  message,
        "icon":  "/icons/icon-192.png",
        "url":   "/",
        "tag":   f"apicole-{hive_id}",
    })
    try:
        webpush(
            subscription_info=subscription_info,
            data=data,
            vapid_private_key=vapid_private_key,
            vapid_claims={"sub": vapid_email},
        )
        logger.info("Push envoyé → %s…", subscription_info.get("endpoint", "")[:50])
        return None
    except Exception as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        logger.warning("Push échoué (status=%s) : %s", status, exc)
        return status
