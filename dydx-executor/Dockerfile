# dYdX Executor Service Dockerfile
FROM node:20-slim

WORKDIR /app

# Copier les fichiers de dépendances
COPY package*.json ./

# Installer les dépendances
RUN npm ci --only=production

# Copier le code source
COPY . .

# Port par défaut
ENV PORT=3001
EXPOSE 3001

# Démarrer le serveur
CMD ["node", "server.js"]
