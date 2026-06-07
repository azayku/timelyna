#!/bin/bash
set -e

echo "=== TimesheetPro — Déploiement Docker ==="

# Vérifier que Docker est disponible
if ! command -v docker &> /dev/null; then
  echo "❌ Docker n'est pas installé."
  exit 1
fi

# Arrêter les anciens conteneurs (sans supprimer les volumes)
echo ""
echo "▶ Arrêt des conteneurs existants..."
docker compose down --remove-orphans

# Build des images
echo ""
echo "▶ Build des images..."
docker compose build --no-cache

# Lancer tous les services
echo ""
echo "▶ Démarrage des services..."
docker compose up -d

# Attendre que le backend soit prêt
echo ""
echo "▶ Attente du backend (migrations + démarrage)..."
timeout=120
elapsed=0
until docker compose exec -T backend curl -sf http://localhost:8000/health > /dev/null 2>&1; do
  sleep 3
  elapsed=$((elapsed + 3))
  if [ $elapsed -ge $timeout ]; then
    echo "⚠️  Timeout — vérifiez les logs : docker compose logs backend"
    break
  fi
  echo "   ... attente ($elapsed s)"
done

echo ""
echo "=== État des services ==="
docker compose ps

echo ""
echo "✅ Déploiement terminé !"
echo ""
echo "   Frontend  → http://localhost"
echo "   Backend   → http://localhost:8000"
echo "   API docs  → http://localhost:8000/docs"
echo "   pgAdmin   → http://localhost:5050"
echo ""
echo "   Compte admin par défaut :"
echo "   Email    : admin@timesheetpro.com"
echo "   Password : Admin1234!"
echo ""
echo "   Logs : docker compose logs -f"
