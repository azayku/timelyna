#!/bin/bash

# Script pour exécuter tous les tests de diagnostic du Manager API
# Usage: bash run_all_tests.sh

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                    TESTS MANAGER API - DIAGNOSTIC COMPLET                  ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher un titre
print_title() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

# Test 1: Vérifier que le backend est en ligne
print_title "TEST 1: Vérification du backend"
python check_backend_status.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Le backend n'est pas accessible!${NC}"
    echo -e "${YELLOW}Veuillez démarrer le backend avant de continuer.${NC}"
    exit 1
fi

# Test 2: Tester la base de données
print_title "TEST 2: Vérification de la base de données"
python test_manager_data.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Problème avec les données de la base!${NC}"
    echo -e "${YELLOW}Exécutez le script SQL: psql -U postgres -d timesheetpro -f setup_gianni_final.sql${NC}"
    exit 1
fi

# Test 3: Tester l'API
print_title "TEST 3: Test de l'API Manager"
python test_manager_api.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Problème avec l'API Manager!${NC}"
    exit 1
fi

# Résumé final
echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                           ✅ TOUS LES TESTS RÉUSSIS                         ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}Le backend et l'API Manager fonctionnent correctement!${NC}"
echo ""
echo "Prochaines étapes:"
echo "  1. Ouvrir le frontend: http://localhost:5173"
echo "  2. Se connecter avec: gianni.cappelli@manager.test.it / password123"
echo "  3. Aller dans GESTION → Mes organisations"
echo "  4. Aller dans GESTION → Mon équipe"
echo ""
