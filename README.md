# Surveillance Apicole IA

Application mobile de surveillance apicole intelligente. L'IA analyse le vrombissement des abeilles (données sonores) pour prédire l'essaimage ou détecter des maladies dans les colonies.

> **Projet d'études** — Bachelor 2 Informatique · Sprint 72h
> **Équipe** — Augustin · Sébastien · Kelvya · Ridwan

---

## Sommaire

- [Concept](#concept)
- [Stack technique](#stack-technique)
- [Structure du projet](#structure-du-projet)
- [Pages de l'application](#pages-de-lapplication)
- [Démarrage rapide](#démarrage-rapide)
- [Intégration Figma](#intégration-figma)
- [Charte graphique](#charte-graphique)
- [Points d'intégration backend](#points-dintégration-backend)
- [Roadmap](#roadmap)
- [Auteurs](#auteurs)

---

## Concept

L'application surveille en temps réel un parc de ruches connectées et propose :

- **Capteurs en direct** : fréquence sonore (Hz), température (°C), humidité (%).
- **Analyse IA** : détection des comportements anormaux via l'API Grok (essaimage, maladies, stress thermique).
- **Alertes contextuelles** : notifications push quand un seuil est dépassé.
- **Historique** : journal complet des évènements stocké en SQLite.
- **Paramétrage** : réglage fin des seuils par l'apiculteur.

## Stack technique

| Couche         | Technologie                          |
| -------------- | ------------------------------------ |
| Frontend       | HTML5 / CSS3 (mobile-first 375px)    |
| Backend        | Python · FastAPI                     |
| Base de données| SQLite                               |
| IA             | API Grok (xAI)                       |
| Conteneurisation | Docker                             |
| Déploiement    | Microsoft Azure                      |
| Maquettage     | Figma (import via `html.to.design`)  |

> Le frontend est volontairement **sans framework** (ni Tailwind, ni Bootstrap) pour garantir un import parfait dans Figma et une maintenance pédagogique simple.

## Structure du projet

```
projetb2/
├── frontend/
│   ├── index.html        # Dashboard
│   ├── map.html          # Carte interactive des ruches
│   ├── diag.html         # Module de diagnostic IA
│   ├── history.html      # Historique des rapports
│   ├── settings.html     # Paramètres & seuils
│   └── style.css         # Feuille de styles partagée
├── backend/              # (à venir) FastAPI + SQLite
├── README.md
└── .gitignore
```

## Pages de l'application

| Page              | Fichier         | Rôle                                                    |
| ----------------- | --------------- | ------------------------------------------------------- |
| Dashboard         | `index.html`    | Résumé : KPI sonore/temp/humidité + alertes IA         |
| Carte des ruches  | `map.html`      | Grille de 6 ruches colorées (vert/orange/rouge)         |
| Diagnostic IA     | `diag.html`     | Lancement d'une analyse acoustique + résultat Grok     |
| Historique        | `history.html`  | Journal chronologique des évènements (SQLite)           |
| Paramètres        | `settings.html` | Réglage des seuils (Hz, °C, %) et configuration API     |

Toutes les pages partagent une **bottom navigation** à 5 onglets pour la cohérence mobile.

## Démarrage rapide

Le frontend étant statique, aucune installation n'est requise.

```bash
# Cloner le dépôt
git clone <repo-url>
cd projetb2/frontend

# Ouvrir dans le navigateur
# Option 1 : double-clic sur index.html
# Option 2 : serveur local Python (recommandé pour DevTools mobile)
python -m http.server 8000
# puis ouvrir http://localhost:8000
```

Pour simuler un mobile dans Chrome/Edge : `F12` → bascule responsive → choisir **iPhone SE / 375 × 812**.

## Intégration Figma

Le code est optimisé pour l'extension **html.to.design** :

1. Installer l'extension Figma `html.to.design`.
2. Coller l'URL locale du fichier HTML (ou uploader le dossier).
3. Importer — chaque page devient un frame Figma de 375 px de large, calques nommés selon les classes CSS.

**Bonnes pratiques respectées** :
- Classes sémantiques explicites (`.kpi-card`, `.hive-card`, `.history-item`).
- Aucun `position: absolute` complexe, aucun `transform` exotique.
- Variables CSS centralisées (couleurs, espacements, rayons).
- Police système sans-serif (pas de webfont à charger).

## Charte graphique

| Variable CSS           | Valeur     | Usage                       |
| ---------------------- | ---------- | --------------------------- |
| `--agri-green`         | `#2D6A4F`  | Couleur principale (CTA)    |
| `--agri-green-light`   | `#52B788`  | État normal / accents verts |
| `--honey-yellow`       | `#F4A261`  | Accent miel / alertes douces|
| `--alert-orange`       | `#F77F00`  | Risque modéré (essaimage)   |
| `--alert-red`          | `#E63946`  | Alerte critique (maladie)   |
| `--soft-gray`          | `#F1F3F5`  | Fond neutre                 |

Typographie : `system-ui` / `Segoe UI` / `Inter` (pile sans-serif native).

## Points d'intégration backend

Le frontend contient 9 commentaires HTML `<!-- TODO: ... (FastAPI) -->` aux endroits où le backend devra brancher ses endpoints :

| Endpoint                          | Page          | Usage                              |
| --------------------------------- | ------------- | ---------------------------------- |
| `GET /api/sensors/aggregate`      | index.html    | KPI temps réel (Hz/°C/%)           |
| `GET /api/alerts/latest`          | index.html    | Bannière d'alerte IA               |
| `GET /api/hives`                  | index/map.html| Liste & statut des ruches          |
| `POST /api/diagnostic/start`      | diag.html     | Lancer une analyse Grok            |
| `POST /api/diagnostic/result`     | diag.html     | Récupérer le résultat              |
| `GET /api/history?range=7d`       | history.html  | Journal des évènements             |
| `GET /api/settings`               | settings.html | Pré-remplir les seuils             |
| `POST /api/settings`              | settings.html | Sauvegarder les seuils             |

## Roadmap

- [x] Maquette frontend mobile (5 pages)
- [x] Charte graphique & variables CSS
- [x] Import Figma compatible
- [ ] Backend FastAPI + schéma SQLite
- [ ] Intégration API Grok pour analyse acoustique
- [ ] JS de fetch et rafraîchissement des KPI
- [ ] Conteneurisation Docker
- [ ] Déploiement Azure
- [ ] Démo finale (30 pts)

## Auteurs

Projet réalisé en équipe dans le cadre du Bachelor 2 Informatique :

- **Augustin**
- **Sébastien**
- **Kelvya**
- **Ridwan**
