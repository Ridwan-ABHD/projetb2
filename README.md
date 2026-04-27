# Surveillance Apicole IA

Application mobile de surveillance apicole intelligente. L'IA analyse le vrombissement des abeilles (données sonores) pour prédire l'essaimage ou détecter des maladies dans les colonies.

> **Projet d'études** — Bachelor 2 Informatique · Sprint 72h
> **Équipe** — Augustin · Sébastien · Kelvya · Ridwan

---

## Sommaire

- [Concept](#concept)
- [Structure du projet](#structure-du-projet)
- [Pages de l'application](#pages-de-lapplication)
- [Démarrage rapide](#démarrage-rapide)
- [Charte graphique](#charte-graphique)
- [Auteurs](#auteurs)

---

## Concept

L'application surveille en temps réel un parc de ruches connectées et propose :

- **Capteurs en direct** : fréquence sonore (Hz), température (°C), humidité (%).
- **Analyse IA** : détection des comportements anormaux (essaimage, maladies, stress thermique).
- **Alertes contextuelles** : notifications quand un seuil est dépassé.
- **Historique** : journal complet des évènements.
- **Paramétrage** : réglage fin des seuils par l'apiculteur.

## Structure du projet

```
projetb2/
├── frontend/
│   ├── index.html        # Dashboard
│   ├── map.html          # Carte interactive des ruches
│   ├── diag.html         # Module de diagnostic IA
│   ├── history.html      # Historique des rapports
│   ├── settings.html     # Paramètres & seuils
│   ├── base.css          # Variables, reset, layout
│   ├── ui.css            # Composants (boutons, cartes, alertes…)
│   └── pages.css         # Styles spécifiques aux pages
├── backend/
└── README.md
```

## Pages de l'application

| Page              | Fichier         | Rôle                                                  |
| ----------------- | --------------- | ----------------------------------------------------- |
| Dashboard         | `index.html`    | Résumé : KPI sonore/temp/humidité + alertes IA        |
| Carte des ruches  | `map.html`      | Grille de 6 ruches colorées (vert/orange/rouge)       |
| Diagnostic IA     | `diag.html`     | Lancement d'une analyse acoustique + résultat        |
| Historique        | `history.html`  | Journal chronologique des évènements                  |
| Paramètres        | `settings.html` | Réglage des seuils (Hz, °C, %)                        |

Toutes les pages partagent une **bottom navigation** à 5 onglets pour la cohérence mobile.

## Démarrage rapide

Le frontend étant statique, aucune installation n'est requise.

```bash
# Cloner le dépôt
git clone https://github.com/Ridwan-ABHD/projetb2.git
cd projetb2/frontend

# Ouvrir dans le navigateur
# Option 1 : double-clic sur index.html
# Option 2 : serveur local Python
python -m http.server 8000
# puis ouvrir http://localhost:8000
```

Pour simuler un mobile dans Chrome/Edge : `F12` → bascule responsive → choisir **iPhone SE / 375 × 812**.

## Charte graphique

| Variable CSS    | Valeur     | Usage                       |
| --------------- | ---------- | --------------------------- |
| `--green`       | `#2D6A4F`  | Couleur principale (CTA)    |
| `--green-light` | `#52B788`  | État normal / accents verts |
| `--yellow`      | `#F4A261`  | Accent miel / alertes douces|
| `--orange`      | `#F77F00`  | Risque modéré (essaimage)   |
| `--red`         | `#E63946`  | Alerte critique (maladie)   |
| `--soft`        | `#F1F3F5`  | Fond neutre                 |

Typographie : `system-ui` / `Segoe UI` / `Inter` (pile sans-serif native).
Format mobile-first 375 px de large.

## Auteurs

Projet réalisé en équipe dans le cadre du Bachelor 2 Informatique :

- **Augustin**
- **Sébastien**
- **Kelvya**
- **Ridwan**
