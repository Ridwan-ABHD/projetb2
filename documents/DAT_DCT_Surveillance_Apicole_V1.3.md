# Dossier d'Architecture Technique (DAT / DCT) - Version Étendue
## Système de Surveillance de Ruches Connectées par IA

**Version :** 1.3  
**Statut :** Document Technique Inter-Équipes  
**Classification :** Interne / Neutre

---

### 1. RÉSUMÉ EXÉCUTIF ET VISION
L'agriculture de précision, appliquée à l'apiculture, permet de répondre à une problématique majeure : la mortalité croissante des colonies d'abeilles. Ce projet propose une infrastructure logicielle complète permettant de surveiller la santé des essaims en temps réel.

La vision du projet repose sur l'exploitation du "vrombissement" des abeilles. Cette signature acoustique, une fois traitée par des modèles d'intelligence artificielle, devient un indicateur prédictif de comportements complexes (essaimage, détresse, maladies) bien avant que les signes physiques ne soient visibles par l'homme.

### 2. ARCHITECTURE FONCTIONNELLE DÉTAILLÉE
Le système est conçu pour traiter trois flux de données distincts permettant une corrélation intelligente :

#### 2.1 Flux Environnemental et Physique
* **Sonde Thermique :** Mesure de la température interne. Une chute brutale ou une montée excessive indique un stress ou un arrêt de la ponte de la reine.
* **Hygrométrie :** L'humidité relative influe sur le développement du couvain.
* **Pesée Statique :** Un capteur de force (type Load Cell) mesure le poids total. Une augmentation rapide signale une miellée (apport de nectar), tandis qu'une baisse brutale peut signaler un essaimage (départ de la moitié de la colonie).

#### 2.2 Flux Acoustique (Analyse IA)
C'est la brique centrale du projet. Le système capture des échantillons sonores qui sont analysés selon deux méthodes :
1.  **Analyse de Fréquence :** Surveillance des pics entre 100 Hz et 500 Hz.
2.  **Analyse Sémantique :** Envoi des métadonnées et échantillons à l'API Grok (xAI) pour obtenir un diagnostic contextuel sur l'état de la ruche.

### 3. ARCHITECTURE TECHNIQUE (STACK LOGICIELLE)
L'architecture est de type *micro-services*, isolée par conteneurisation pour garantir la portabilité entre les environnements de développement (Linux Fedora) et de production (Cloud Azure).

| Composant | Technologie | Rôle / Configuration |
| :--- | :--- | :--- |
| **Frontend** | HTML5 / CSS3 (Mobile-first) | Interface 375px native sans framework pour import Figma. |
| **API Backend** | Python 3.12 / FastAPI | Framework asynchrone pour la gestion des requêtes haute performance. |
| **Base de données** | SQLite (via SQLAlchemy) | Stockage de l'historique et des seuils d'alerte configurables. |
| **Broker MQTT** | Mosquitto | Gestion des flux de données provenant des capteurs simulés. |
| **Simulation IoT** | Python (sensor_mock.py) | Émulation de 20 ruches avec injection d'anomalies. |

### 4. STRATÉGIE DE SIMULATION (MOCKING)
Le projet utilise une approche de simulation active pour valider la logique backend sans matériel physique :
* **Génération de Courbes :** Les scripts utilisent des fonctions mathématiques pour simuler les variations de température (cycles circadiens) et de poids.
* **Injection d'Incidents :** Possibilité de déclencher via script un "mode essaimage" pour vérifier la réactivité des alertes sur le dashboard mobile.
* **Émulation Réseau :** Simulation de latence pour tester la résilience des appels API.

### 5. CYBERSÉCURITÉ ET RÉSILIENCE
Conformément aux exigences de cybersécurité pour les infrastructures critiques agricoles :
* **Signature HMAC-SHA256 :** Chaque message envoyé par les unités de simulation comporte un code d'authentification de message. Le backend rejette toute donnée dont la signature ne correspond pas à la clé secrète.
* **Environnement Isolé :** Utilisation de réseaux Docker internes. Seul le port 8000 (API) et le port 80 (Frontend) sont exposés.
* **Protection des Secrets :** Les clés API pour Grok et les accès Azure sont stockés dans des fichiers .env exclus du versioning Git.

### 6. MODÈLE ÉCONOMIQUE ET RENTABILITÉ (ROI)
L'étude financière repose sur une exploitation de 50 ruches.

#### 6.1 Investissement Initial (CAPEX)
* Hardware (Passerelles + Capteurs pour 20 ruches pilotes) : 4 000 €
* Mise en place Infrastructure Cloud & Sécurité : 2 500 €
* Logistique et tests terrain : 2 000 €
* **TOTAL : 8 500 €**

#### 6.2 Gains Annuels Estimés (OPEX Savings)
* Sauvegarde de 8 colonies (mortalité évitée) : 1 200 €
* Gain de productivité miel (timing optimal) : 3 300 €
* Réduction des frais de déplacement (maintenance prédictive) : 2 000 €
* **TOTAL DES GAINS : 6 500 € / an**

**Seuil de rentabilité : 1,3 année (soit environ 16 mois).**

### 7. ANALYSE DES RISQUES ET ACTIONS PRÉVENTIVES
| Risque | Niveau | Action de Mitigation |
| :--- | :--- | :--- |
| Injection de données | **Critique** | Mise en place de signatures HMAC sur chaque trame. |
| Perte de connectivité | Moyen | Bufferisation des données en local sur l'unité IoT. |
| Vol de matériel | Moyen | Géolocalisation passive et alertes accéléromètre. |

### 8. ROADMAP DU PROJET (SPRINT 72H)
1.  **T+0h à T+24h :** Maquettage Figma et intégration Frontend statique.
2.  **T+24h à T+48h :** Développement API FastAPI et script de simulation des capteurs.
3.  **T+48h à T+60h :** Intégration de l'IA Grok et corrélation des alertes.
4.  **T+60h à T+72h :** Dockerisation, tests de sécurité et déploiement final.

---
*Document technique confidentiel - Ne pas diffuser hors du cadre du projet B2.*
