# Explication — mqtt_client.py

## 1. MQTT — c'est quoi ?

MQTT c'est un protocole de messagerie léger, conçu pour les capteurs IoT. Ça fonctionne comme un système pub/sub (publish/subscribe) :

```
[Ruche / sensor_mock.py]  →  publie sur "apicole/hive/3/sensors"
                                        ↓
                                  [Broker Mosquitto]
                                        ↓
[Backend / mqtt_client.py]  ←  reçoit le message (abonné au topic)
```

Le `+` dans `apicole/hive/+/sensors` c'est un **wildcard** : une seule souscription capte les 6 ruches d'un coup.

---

## 2. HMAC-SHA256 — la sécurité

**Le problème sans sécurité :** n'importe qui pourrait envoyer de fausses données et déclencher de fausses alertes.

**La solution :** une signature partagée. Le simulateur et le backend connaissent tous les deux le même secret (`HMAC_SECRET`).

### Côté simulateur (`sensor_mock.py`) — signature avant envoi

```python
raw = json.dumps(data, sort_keys=True).encode()
signature = hmac.new(SECRET.encode(), raw, hashlib.sha256).hexdigest()
# → "a3f9c2e1b7..." (64 caractères)
```

### Côté backend (`mqtt_client.py`) — vérification à la réception

```python
received = payload.pop("signature", None)          # extrait la signature reçue
raw = json.dumps(payload, sort_keys=True).encode() # recalcule de son côté
expected = hmac.new(SECRET.encode(), raw, hashlib.sha256).hexdigest()
return hmac.compare_digest(received, expected)      # compare les deux
```

Si quelqu'un envoie de fausses données sans connaître le secret → la signature ne correspond pas → **message ignoré**.

---

## 3. Génération d'alertes automatiques

Dès qu'un message valide arrive, `_evaluate_and_alert()` compare les valeurs aux seuils stockés en base :

| Valeur | Seuil | Alerte créée |
|---|---|---|
| `frequency_hz` ≥ 280 Hz | `freq_critical` | SWARMING — critique |
| `frequency_hz` ≥ 260 Hz | `freq_warning` | SWARMING — warning |
| `temperature_c` ≥ 38°C | `temp_critical` | THERMAL_STRESS — critique |
| `temperature_c` ≥ 36°C | `temp_warning` | THERMAL_STRESS — warning |

Le statut de la ruche (`normal` / `warning` / `critical`) est mis à jour à chaque lecture — ce qui changera la couleur sur le dashboard.

---

## 4. Le thread séparé

Le subscriber MQTT tourne dans un **thread séparé** pour ne pas bloquer l'API FastAPI pendant qu'elle écoute les messages en continu.

```python
thread = threading.Thread(target=client.loop_forever, daemon=True)
thread.start()
```

`daemon=True` → le thread s'arrête automatiquement quand l'API s'arrête.
