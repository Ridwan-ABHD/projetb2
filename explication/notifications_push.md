# Notifications Push — Comment ça marche et pourquoi

## Vue d'ensemble du flux

```
Capteur (moks_live.py)
    → INSERT mesure dans RucheIA.db toutes les 5s
        → _alert_checker() (FastAPI, toutes les 15s)
            → compare mesure aux seuils (settings)
                → INSERT alerte dans alertes
                    → webpush() → Service Worker → Notification téléphone
```

---

## 1. Souscription (une seule fois au premier lancement)

Quand l'utilisateur ouvre l'app et accepte les notifications :

```typescript
// push.service.ts
const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: vapidPublicKey,  // clé publique VAPID
});
// Envoi de la subscription au backend
this.api.subscribePush(subscription.toJSON());
```

Le navigateur génère un **endpoint unique** (URL Firebase/Mozilla) que le
backend stocke dans la table `push_subscriptions`. C'est à cette adresse
que le backend enverra les notifications.

---

## 2. Génération des alertes (backend, toutes les 15 secondes)

```python
# main.py — _alert_checker()
```

| Condition | Type alerte | Sévérité | Push envoyé ? |
|-----------|-------------|----------|---------------|
| freq ≥ 280 Hz | `frequence_critique` | critical | ✅ Oui |
| 260 ≤ freq < 280 Hz | `frequence_warning` | warning | ✅ Oui (essaimage) |
| temp ≥ 38°C | `temperature_critique` | critical | ✅ Oui |
| 36 ≤ temp < 38°C | `temperature_warning` | warning | ❌ Non |

**Pourquoi les alertes fréquence (essaimage) à warning déclenchent un push ?**
L'essaimage peut démarrer dès 260 Hz — attendre le seuil critique (280 Hz)
serait trop tard. La température à 36-38°C est moins urgente (marge normale).

**Logique de réinitialisation** — évite de spammer :
- Si la fréquence repasse sous le seuil critique → l'alerte critique est
  résolue (`is_resolved = 1`) et une alerte warning prend le relais
- Si elle repasse en dessous de 260 Hz → toutes les alertes fréquence
  sont résolues
- La prochaine fois que le seuil est franchi → nouvelle alerte → nouveau push

---

## 3. Envoi via Web Push (pywebpush + VAPID)

```python
# push_utils.py
webpush(
    subscription_info={"endpoint": "https://fcm.googleapis.com/...", "keys": {...}},
    data=json.dumps({"title": "Alerte — Ruche H1", "body": "280 Hz..."}),
    vapid_private_key=VAPID_PRIVATE_KEY,
    vapid_claims={"sub": "mailto:admin@..."},
)
```

**VAPID** (Voluntary Application Server Identification) = paire de clés
asymétriques qui prouve que le serveur est légitime. La clé privée signe
la requête, Firebase/Mozilla vérifie avec la clé publique.

---

## 4. Réception par le Service Worker (même app fermée)

```javascript
// sw.js
self.addEventListener('push', (event) => {
    const data = event.data.json();
    event.waitUntil(
        self.registration.showNotification(data.title, { body: data.body, ... })
    );
});
```

Le **Service Worker** est un script qui tourne en arrière-plan dans le
navigateur, indépendamment de l'app. Il reçoit les push même quand l'onglet
est fermé. L'OS mobile gère la notification (son, vibration, bandeau).

**Condition pour que ça marche app fermée** : le navigateur doit tourner en
arrière-plan (comportement par défaut sur Android/iOS avec une PWA installée).

---

## 5. Pourquoi une seule notification au début ?

**Bug corrigé** : le `conn.commit()` dans `_alert_checker` n'était appelé
que si une *nouvelle* alerte était créée. Les résolutions (`UPDATE
is_resolved=1`) n'étaient jamais persistées → l'alerte critique restait
bloquée indéfiniment → plus aucune nouvelle alerte ne pouvait être créée
→ plus de push.

**Fix** : commit systématique à chaque cycle, même si seules des résolutions
ont eu lieu.

---

## 6. Pourquoi les notifications arrivent aussi à l'inscription ?

```python
# routers/push.py
if is_new:
    _push_existing_criticals_to(subscription_json)
```

Si le backend avait déjà des alertes critiques actives au moment où le
téléphone s'inscrit (app ouverte après le démarrage), il envoie immédiatement
ces alertes au nouvel abonné. Ça évite le cas où l'alerte était créée avant
l'inscription.
