# Script de déploiement pour Render.com (Windows PowerShell)

Write-Host "🚀 Préparation du déploiement Bull Sage..." -ForegroundColor Cyan

# Vérifier que les fichiers nécessaires existent
if (-not (Test-Path "backend\.env")) {
    Write-Host "⚠️  Attention: backend\.env n'existe pas. Copiez backend\.env.example et configurez-le." -ForegroundColor Yellow
}

if (-not (Test-Path "frontend\.env")) {
    Write-Host "⚠️  Attention: frontend\.env n'existe pas. Copiez frontend\.env.example et configurez-le." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📋 Instructions de déploiement sur Render.com:" -ForegroundColor Green
Write-Host ""
Write-Host "1. Allez sur https://render.com et créez un compte"
Write-Host ""
Write-Host "2. Créez une base de données MongoDB Atlas gratuite:" -ForegroundColor Yellow
Write-Host "   - https://www.mongodb.com/atlas"
Write-Host "   - Créez un cluster M0 (gratuit)"
Write-Host "   - Autorisez 0.0.0.0/0 dans Network Access"
Write-Host "   - Copiez l'URL de connexion"
Write-Host ""
Write-Host "3. Déployez le Backend (Web Service):" -ForegroundColor Yellow
Write-Host "   - New → Web Service"
Write-Host "   - Connectez votre GitHub repo"
Write-Host "   - Root Directory: backend"
Write-Host "   - Build Command: pip install -r requirements.txt"
Write-Host "   - Start Command: uvicorn server:app --host 0.0.0.0 --port `$PORT"
Write-Host "   - Ajoutez les variables d'environnement"
Write-Host ""
Write-Host "4. Déployez le Frontend (Static Site):" -ForegroundColor Yellow
Write-Host "   - New → Static Site"
Write-Host "   - Root Directory: frontend"
Write-Host "   - Build Command: npm install --legacy-peer-deps && npm run build"
Write-Host "   - Publish Directory: build"
Write-Host "   - REACT_APP_BACKEND_URL = https://votre-backend.onrender.com"
Write-Host ""
Write-Host "✅ Une fois déployé, votre app sera accessible sur:" -ForegroundColor Green
Write-Host "   - Frontend: https://votre-frontend.onrender.com"
Write-Host "   - API: https://votre-backend.onrender.com/api"
