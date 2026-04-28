# DAT / DCT — Surveillance Apicole IoT & Edge AI
**Version :** 1.3 — Post-déploiement  
**Équipe :** Augustin · Sébastien · Kelvya · Ridwan  
**Date :** 27 avril 2026  
**Statut :** Infrastructure déployée et opérationnelle

---

## 1. Contexte & Objectifs

L'apiculture professionnelle subit des pertes annuelles de 25 à 40 % des colonies en France, liées au varroa, aux pesticides et aux essaimages non détectés. Ce projet déploie une infrastructure IoT simulée pour surveiller en temps réel un parc de ruches connectées via analyse acoustique et intelligence artificielle.

**Objectifs**
- Réduire la mortalité des colonies via détection précoce des anomalies comportementales.
- Optimiser les récoltes par suivi continu des miellées (capteurs de poids simulés).
- Réduire les coûts logistiques grâce à la maintenance prédictive.
- Fournir une interface mobile de supervision temps réel à l'apiculteur.

**Modèle économique (20 ruches pilotes / parc 50)**

| Poste | Montant |
|---|---|
| CAPEX total (hardware + cloud + logistique) | 8 500 € |
| Gains annuels estimés (colonies + productivité + déplacements) | 6 500 €/an |
| Seuil de rentabilité | ~16 mois |

---

## 2. Architecture Déployée

Infrastructure opérationnelle depuis le 27 avril 2026 — VM Azure Ubuntu 24.04 (Canada Central, Standard_B2s) hébergeant 3 conteneurs Docker, accès privé exclusivement via Tailscale VPN mesh.

### 2.1 Vue d'ensemble

| Couche | Composant | Technologie | Statut |
|---|---|---|---|
| Simulation | 6 mocks capteurs | Python sensor_mock.py | ✅ Opérationnel |
| Transport | Broker MQTT | Eclipse Mosquitto 2 | ✅ Opérationnel |
| Backend | API REST + WebSocket | FastAPI Python 3.12 + SQLite | ✅ Opérationnel |
| Présentation | Interface mobile 5 pages | HTML/CSS vanilla 375px | ✅ Opérationnel |
| Réseau privé | VPN mesh | Tailscale (WireGuard) | ✅ Opérationnel |
| Hébergement | VM Linux cloud | Azure Ubuntu 24.04 | ✅ Opérationnel |

### 2.2 Topologie réseau

| Flux | Protocole | Sécurité |
|---|---|---|
| Mock capteurs → Mosquitto | MQTT (interne Docker) | Auth user/password + réseau Docker isolé |
| Mosquitto → FastAPI | MQTT subscribe | Interne conteneur, non exposé |
| FastAPI → Frontend | HTTP reverse proxy nginx | Interne conteneur |
| Utilisateur → Application | HTTPS 443 | Tailscale Serve — certificat Let's Encrypt auto |
| Admin → VM (SSH) | SSH via Tailscale | Aucun port SSH ouvert sur Internet |
| Internet → VM | — | Aucun port exposé (NSG Azure tout fermé) |

### 2.3 Accès à l'application

- **URL privée :** `https://vm-apiculture.<tailnet>.ts.net`
- **IP Tailscale VM :** `100.66.232.56`
- **Démo soutenance :** `tailscale funnel --bg 80` (URL publique temporaire, coupée après)

---

## 3. Stack Technique

### 3.1 Conteneurs Docker

| Conteneur | Image | Port | Rôle |
|---|---|---|---|
| backend | Build ./backend (Python 3.12) | 8000 | API FastAPI + consommateur MQTT + WebSocket alertes |
| frontend | nginx:alpine | 80 | Sert les 5 pages HTML/CSS + reverse proxy API |
| mosquitto | eclipse-mosquitto:2 | 1883 | Broker MQTT — reçoit les payloads des mocks |

### 3.2 Simulation des capteurs

6 scripts Python simulent les ruches. Chaque mock émet un payload binaire 12 octets (`struct pack >BHbBHBBBBB`) toutes les 15-20 secondes.

| Mock | DevEUI | Profil | Comportement |
|---|---|---|---|
| mock-1 | 70B3D57ED0000001 | normal | ~244 Hz, état sain |
| mock-2 | 70B3D57ED0000002 | swarm | ~271 Hz, risque essaimage |
| mock-3 | 70B3D57ED0000003 | disease | ~312 Hz, alerte maladie |
| mock-4 | 70B3D57ED0000004 | normal | ~244 Hz, état sain |
| mock-5 | 70B3D57ED0000005 | normal | ~244 Hz, état sain |
| mock-6 | 70B3D57ED0000006 | swarm | ~253 Hz, risque essaimage |

### 3.3 API Backend

| Méthode | Route | Usage |
|---|---|---|
| GET | /api/sensors/aggregate | KPI temps réel (Hz / °C / %) |
| GET | /api/alerts/latest | Alertes actives non acquittées |
| GET | /api/hives | Liste et statut des 6 ruches |
| POST | /api/diagnostic/start | Lance une analyse IA (job asynchrone) |
| GET | /api/diagnostic/{job_id} | Résultat du diagnostic |
| GET | /api/history | Journal des événements (?range=7d) |
| GET | /api/settings | Lecture des seuils configurés |
| POST | /api/settings | Mise à jour des seuils |
| WS | /ws/alerts | Push WebSocket alertes temps réel |

---

## 4. Sécurité

**Modèle retenu : zéro surface d'attaque WAN.** Aucun service n'est exposé sur Internet. Tout accès passe par Tailscale (WireGuard sous-jacent).

| Menace | Contre-mesure |
|---|---|
| Accès non autorisé à l'app | Tailscale VPN obligatoire |
| Intrusion SSH sur la VM | Port 22 fermé WAN — SSH via Tailscale uniquement |
| Exposition des ports Docker | Bind sur 127.0.0.1 uniquement |
| Injection de fausses données MQTT | Auth Mosquitto + réseau Docker isolé |
| Vol de secrets | `.env` exclu du versioning Git |
| Accès non autorisé à la DB | SQLite non exposée, accès conteneur uniquement |

**Chiffrement actif**
- Transport utilisateur → app : TLS 1.3 (Let's Encrypt via Tailscale Serve)
- Tunnel VM ↔ clients : WireGuard (Tailscale)
- Payload mocks : AES-128 CTR illustratif (simule le chiffrement LoRaWAN AppSKey en prod)

---

## 5. Roadmap

| Phase | Livrable | Statut |
|---|---|---|
| Sprint 0 | Maquette frontend 5 pages + charte graphique | ✅ Fait |
| Sprint 1 | Backend FastAPI + SQLite + mocks Python | ✅ Fait |
| Sprint 2 | Dockerisation + déploiement Azure + Tailscale VPN | ✅ Fait |
| Sprint 3 | Intégration API Grok + WebSocket alertes temps réel | 🔄 En cours |
| Sprint 4 | Tests de charge + démo finale soutenance | ⏳ À venir |
| Post-projet | Hardware ESP32 + LoRaWAN + déploiement terrain | ⏳ Phase prod |

---

*Document interne — Projet Bachelor 2 Informatique · Sup de Vinci*
