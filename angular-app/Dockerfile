# Dockerfile — Build multi-étapes pour l'application Angular
# Étape 1 : Build (Node.js)  → Étape 2 : Servir (Nginx)

# =====================================================
# ÉTAPE 1 : Construction de l'application Angular
# =====================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copie d'abord les fichiers de dépendances (optimise le cache Docker)
COPY package.json package-lock.json ./

# Installation des dépendances npm
RUN npm ci

# Copie du reste des sources
COPY . .

# Build de production (génère les fichiers dans dist/beeguard-app/browser)
RUN npm run build:prod

# =====================================================
# ÉTAPE 2 : Serveur Nginx (image légère ~20MB)
# =====================================================
FROM nginx:alpine

# Configuration Nginx personnalisée (gestion du routing Angular + proxy backend)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copie des fichiers Angular buildés vers le dossier servi par Nginx
COPY --from=builder /app/dist/beeguard-app/browser /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
