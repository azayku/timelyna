@echo off
REM Script pour exécuter tous les tests de diagnostic du Manager API (Windows)
REM Usage: run_all_tests.bat

echo ================================================================================
echo                    TESTS MANAGER API - DIAGNOSTIC COMPLET
echo ================================================================================
echo.

REM Test 1: Vérifier que le backend est en ligne
echo ================================================================================
echo   TEST 1: Verification du backend
echo ================================================================================
echo.
python check_backend_status.py
if errorlevel 1 (
    echo.
    echo [ERREUR] Le backend n'est pas accessible!
    echo Veuillez demarrer le backend avant de continuer.
    pause
    exit /b 1
)

REM Test 2: Tester la base de données
echo.
echo ================================================================================
echo   TEST 2: Verification de la base de donnees
echo ================================================================================
echo.
python test_manager_data.py
if errorlevel 1 (
    echo.
    echo [ERREUR] Probleme avec les donnees de la base!
    echo Executez le script SQL: psql -U postgres -d timesheetpro -f setup_gianni_final.sql
    pause
    exit /b 1
)

REM Test 3: Tester l'API
echo.
echo ================================================================================
echo   TEST 3: Test de l'API Manager
echo ================================================================================
echo.
python test_manager_api.py
if errorlevel 1 (
    echo.
    echo [ERREUR] Probleme avec l'API Manager!
    pause
    exit /b 1
)

REM Résumé final
echo.
echo ================================================================================
echo                           TOUS LES TESTS REUSSIS
echo ================================================================================
echo.
echo Le backend et l'API Manager fonctionnent correctement!
echo.
echo Prochaines etapes:
echo   1. Ouvrir le frontend: http://localhost:5173
echo   2. Se connecter avec: gianni.cappelli@manager.test.it / password123
echo   3. Aller dans GESTION -^> Mes organisations
echo   4. Aller dans GESTION -^> Mon equipe
echo.
pause
