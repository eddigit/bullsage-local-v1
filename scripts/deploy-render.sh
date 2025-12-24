#!/bin/bash
# Script de déploiement pour Render.com

echo "🚀 Préparation du déploiement Bull Sage..."

# Vérifier que les fichiers nécessaires existent
if [ ! -f "backend/.env" ]; then
    echo "⚠️  Attention: backend/.env n'existe pas. Copiez backend/.env.example et configurez-le."
fi

if [ ! -f "frontend/.env" ]; then
    echo "⚠️  Attention: frontend/.env n'existe pas. Copiez frontend/.env.example et configurez-le."
fi

echo ""
echo "📋 Instructions de déploiement sur Render.com:"
echo ""
echo "1. Allez sur https://render.com et créez un compte"
echo ""
echo "2. Créez une base de données MongoDB Atlas gratuite:"
echo "   - https://www.mongodb.com/atlas"
echo "   - Créez un cluster M0 (gratuit)"
echo "   - Autorisez 0.0.0.0/0 dans Network Access"
echo "   - Copiez l'URL de connexion"
echo ""
echo "3. Déployez le Backend (Web Service):"
echo "   - New → Web Service"
echo "   - Connectez votre GitHub repo"
echo "   - Root Directory: backend"
echo "   - Build Command: pip install -r requirements.txt"
echo "   - Start Command: uvicorn server:app --host 0.0.0.0 --port \$PORT"
echo "   - Ajoutez les variables d'environnement"
echo ""
echo "4. Déployez le Frontend (Static Site):"
echo "   - New → Static Site"
echo "   - Root Directory: frontend"
echo "   - Build Command: npm install --legacy-peer-deps && npm run build"
echo "   - Publish Directory: build"
echo "   - REACT_APP_BACKEND_URL = https://votre-backend.onrender.com"
echo ""
echo "✅ Une fois déployé, votre app sera accessible sur:"
echo "   - Frontend: https://votre-frontend.onrender.com"
echo "   - API: https://votre-backend.onrender.com/api"
