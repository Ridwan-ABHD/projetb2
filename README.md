# BeeGuard AI — Surveillance Apicole Intelligente

Application de surveillance en temps réel d'un parc de ruches connectées. L'IA analyse la fréquence sonore des colonies pour détecter l'essaimage et les anomalies, et envoie des alertes push sur mobile même application fermée.

> **Projet d'études** — Bachelor 2 Informatique · Sprint 72h  
> **Équipe** — Augustin · Sébastien · Kelvya · Ridwan

---

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Frontend | Angular 18 · PWA · Service Worker · Web Push API |
| Backend | FastAPI (Python 3.12) · SQLite · pywebpush · paho-mqtt |
| IA | Azure OpenAI (GPT-4o) · librosa (analyse acoustique) |
| Infra | Docker Compose · Nginx · Eclipse Mosquitto (MQTT) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Docker Compose                       │
│                                                         │
│  ┌──────────┐    MQTT     ┌──────────────┐             │
│  │ Mosquitto│◄────────────│ sensor-mock  │             │
│  │  :1883   │             │ (récupération│             │
│  └────┬─────┘             └──────┬───────┘             │
│       │ subscribe                │ INSERT               │
│       ▼                          ▼                      │
│  ┌────────────────────────────────────────┐            │
│  │          Backend FastAPI :8000         │            │
│  │  • _alert_checker (toutes les 15s)     │            │
│  │  • Alertes + résolution automatique    │            │
│  │  • Web Push (pywebpush + VAPID)        │            │
│  │  • Chat IA (Azure OpenAI)              │            │
│  └────────────────┬───────────────────────┘            │
│                   │ SQLite (volume db-data)             │
│  ┌────────────────▼───────────────────────┐            │
│  │        Frontend Angular :80            │            │
│  │        (build Nginx multi-stage)       │            │
│  └────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────┘
```

---

## Fonctionnalités

- **Temps réel** — capteurs toutes les 5 s (fréquence Hz, température °C, poids kg, humidité %)
- **Alertes intelligentes** — moteur de détection toutes les 15 s avec résolution automatique
- **Notifications push** — même application fermée, via VAPID + Service Worker
- **Essaimage** — alerte dès 260 Hz (avant le seuil critique de 280 Hz)
- **Chat IA** — assistant contextuel GPT-4o avec données en direct des ruches
- **PWA offline** — stale-while-revalidate : données en cache si hors-ligne
- **Diagnostic acoustique** — analyse librosa sur enregistrements audio
- **Responsive** — mobile (bottom nav) + desktop (sidebar)

---

## Pages de l'application

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/dashboard` | KPI fréquence + température, liste des ruches avec statut |
| Ruches | `/map` | Grille des ruches colorées, détail alertes actives |
| Historique | `/history` | Journal chronologique des alertes avec acquittement |
| Paramètres | `/settings` | Seuils configurables (Hz, °C, poids) |
| Assistant | `/chat` | Chat IA contextualisé avec l'état des ruches |
| Diagnostic | `/diag` | Analyse acoustique d'un enregistrement audio |

---

## Structure du projet

```
projetb2/
├── angular-app/          # Frontend Angular 18 PWA
│   ├── src/
│   │   ├── app/
│   │   │   ├── pages/    # dashboard, map, history, settings, chat, diag
│   │   │   ├── shared/   # bottom-nav, offline-banner, network-badge
│   │   │   └── core/     # services (api, push, hive)
│   │   └── styles.css    # Design system global
│   ├── public/
│   │   ├── sw.js         # Service Worker (cache + push)
│   │   └── icons/        # Icônes PWA + navigation
│   ├── nginx.conf        # Reverse proxy + SPA routing
│   └── Dockerfile        # Build multi-stage (Node → Nginx)
│
├── backend/              # API FastAPI Python
│   ├── main.py           # App + _alert_checker background task
│   ├── database.py       # Connexion SQLite
│   ├── push_utils.py     # Envoi Web Push (VAPID)
│   ├── mqtt_client.py    # Subscriber MQTT
│   ├── analyse_ruche.py  # Analyse acoustique librosa
│   ├── schemas.py        # Modèles Pydantic
│   ├── routers/
│   │   ├── hives.py      # GET /hives
│   │   ├── alerts.py     # GET /alerts
│   │   ├── settings.py   # GET/PUT /settings
│   │   ├── push.py       # POST /api/push/subscribe
│   │   ├── chat.py       # POST /chat
│   │   └── diagnosis.py  # POST /diagnosis
│   └── Dockerfile
│
├── BDD/
│   └── recuperation _donnees.py  # Simulateur capteurs (INSERT SQLite direct)
│
├── docker-compose.yml
├── mosquitto.conf
└── .env.example
```

---

## Démarrage rapide

### Prérequis

- Docker + Docker Compose installés
- Un fichier `.env` à la racine (voir `.env.example`)

### Configuration

```bash
cp .env.example .env
# Éditer .env avec vos clés
```

Variables requises dans `.env` :

| Variable | Description |
|----------|-------------|
| `VAPID_PRIVATE_KEY` | Clé privée VAPID pour les push (générer avec `py -m py_vapid`) |
| `VAPID_EMAIL` | Email de contact VAPID (ex: `mailto:admin@exemple.fr`) |
| `AZURE_OPENAI_ENDPOINT` | Endpoint Azure OpenAI |
| `AZURE_OPENAI_API_KEY` | Clé API Azure OpenAI |
| `AZURE_OPENAI_DEPLOYMENT` | Nom du déploiement (ex: `gpt-4o`) |
| `HMAC_SECRET` | Secret HMAC pour la signature des messages MQTT |

### Lancement

```bash
git clone https://github.com/Ridwan-ABHD/projetb2.git
cd projetb2

# Premier lancement (build des images)
docker compose up --build -d

# Relancer après un git pull
git pull && docker compose up --build -d

# Logs en direct
docker compose logs -f backend

# Arrêter
docker compose down
```

L'application est disponible sur **http://\<IP-VM\>** (port 80).

---

## API — Endpoints principaux

| Méthode | Route | Description |
|---------|-------|-------------|
| `GET` | `/hives` | Liste des ruches avec dernière mesure et statut |
| `GET` | `/alerts` | Alertes actives ou filtrées par ruche |
| `GET` | `/settings/` | Seuils configurés |
| `PUT` | `/settings/` | Modifier les seuils |
| `POST` | `/api/push/subscribe` | Enregistrer un abonné push |
| `POST` | `/chat` | Envoyer un message à l'assistant IA |
| `GET` | `/health` | Vérification de l'état du backend |
| `GET` | `/docs` | Documentation interactive Swagger |

---

## Logique des alertes

```
Fréquence ≥ 280 Hz  → frequence_critique  (critical) → 🔔 Push
260 ≤ freq < 280 Hz → frequence_warning   (warning)  → 🔔 Push (essaimage précoce)
Température ≥ 38°C  → temperature_critique (critical) → 🔔 Push
36 ≤ temp < 38°C    → temperature_warning  (warning)  → ❌ Pas de push
```

Le moteur vérifie toutes les **15 secondes** et résout automatiquement les alertes quand les mesures repassent sous les seuils. Un `commit()` systématique garantit la persistance des résolutions.

---

## Charte graphique

| Variable CSS | Valeur | Usage |
|---|---|---|
| `--agri-green` | `#2D6A4F` | Couleur principale, CTAs, sidebar active |
| `--green-light` | `#52B788` | État normal, accents verts |
| `--honey-yellow` | `#F4A261` | Accent miel, alertes douces |
| `--orange` | `#F77F00` | Risque modéré (essaimage) |
| `--alert-red` | `#E63946` | Alerte critique |
| `--bg` | `#F8F9FA` | Fond de page |
| `--soft` | `#F1F3F5` | Fond neutre, hover |

Typographie : pile système (`-apple-system`, `Segoe UI`, `Inter`).  
Format mobile-first, breakpoints à 600 px (tablette) et 1024 px (desktop + sidebar).

---

## Équipe

| Membre | Rôle principal |
|--------|---------------|
| **Augustin** | Frontend Angular, design UI/UX |
| **Sébastien** | Backend FastAPI, alertes, push notifications |
| **Kelvya** | Base de données, schéma, modèles |
| **Ridwan** | Déploiement Docker, infra, MQTT |
