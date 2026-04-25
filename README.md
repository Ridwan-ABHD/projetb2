# Projet B2 — IA & Agriculture

Projet d'études Bachelor 2 Sup de Vinci. Application mobile de surveillance et diagnostic agricole basée sur l'IA, déployée sur infrastructure cloud.

**Équipe :** Augustin · Sébastien · Kelvya · Ridwan

## Stack

| Couche | Choix |
|---|---|
| Front mobile | HTML5 / CSS3 (sans framework, mobile-first 375px) |
| Back-end | Python — FastAPI + SQLite |
| IA | API Grok (xAI) |
| Déploiement | Docker + Azure |

## Structure

```
projetb2/
├── frontend/
│   ├── index.html              Dashboard
│   ├── parcelles.html          Carte interactive
│   ├── diagnostic.html         Module IA
│   ├── historique.html         Rapports
│   ├── parametres.html         Seuils d'alerte
│   └── assets/
│       ├── css/
│       │   ├── variables.css   Couleurs, typo, spacing
│       │   ├── base.css        Reset + globals
│       │   ├── components.css  Header, nav, cards, boutons
│       │   └── pages/          Styles spécifiques par page
│       ├── js/                 (à venir)
│       └── img/
└── README.md
```

## Lancer en local

Aucune dépendance pour le front : ouvrir `frontend/index.html` dans un navigateur, ou servir le dossier :

```bash
cd frontend
python -m http.server 8000
```

Puis ouvrir http://localhost:8000.

## Roadmap

- [x] Maquettes HTML/CSS des 5 écrans principaux
- [ ] Backend FastAPI + endpoints capteurs / diagnostic
- [ ] Intégration API Grok pour le diagnostic IA
- [ ] Schéma d'architecture réseau
- [ ] Conteneurisation Docker
- [ ] Déploiement Azure
# projetb2
