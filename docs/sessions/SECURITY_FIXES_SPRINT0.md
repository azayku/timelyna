# Sprint 0 — Corrections de Sécurité Urgentes

**Date :** 2026-05-04  
**Statut :** ✅ Complété

---

## Corrections Appliquées

### ✅ SEC-01 : Fichier `.env` avec secrets réels
- **Action :** Créé `backend/.env.example` avec valeurs fictives
- **Statut :** `.env` déjà dans `.gitignore`
- **⚠️ ACTION REQUISE :** Régénérer TOUS les secrets exposés (voir section ci-dessous)

### ✅ SEC-02 : Credentials admin hardcodés et loggués
- **Correction :** `entrypoint.sh` modifié pour :
  - Exiger `ADMIN_PASSWORD` en variable d'environnement
  - Supprimer tout affichage de mot de passe dans les logs
  - Bloquer le démarrage si `ADMIN_PASSWORD` est vide au premier lancement

### ✅ SEC-03 : Cookie `refresh_token` sans flag `Secure`
- **Statut :** Déjà corrigé — `secure=settings.APP_ENV == "production"`

### ✅ SEC-04 : `proxy/end` sans contrôle de rôle admin
- **Correction :** Remplacé `Depends(get_current_user)` par `Depends(_admin_only)`
- **Fichier :** `backend/app/api/v1/admin.py:1153`

### ✅ SEC-05 : Mot de passe pgAdmin en clair
- **Correction :** `docker-compose.yml` modifié pour :
  - Utiliser `${PGADMIN_PASSWORD:-changeme}` variable env
  - Utiliser `${PGADMIN_PORT:-5050}` pour le port
  - Ajouter `profiles: [dev]` pour désactiver pgAdmin en production

### ✅ SEC-07 : Clés JWT RS256 éphémères
- **Correction :** `backend/app/core/security.py` modifié pour :
  - Bloquer le démarrage si `APP_ENV=production` et clés JWT vides
  - Afficher un message d'erreur explicite avec instructions de génération

### ✅ SEC-08 : CORS hardcodé et trop permissif
- **Correction :** 
  - Ajout de `CORS_ALLOWED_ORIGINS` dans `config.py`
  - Restriction des méthodes HTTP autorisées
  - Restriction des headers autorisés
  - Configuration via variable d'environnement

### ✅ SEC-09 : JWT access_token dans localStorage
- **Statut :** Déjà corrigé — le token est géré par `tokenStore` séparé (non persisté)

### ✅ SEC-10 : Rôle lu depuis localStorage
- **Correction :** `frontend-v2/src/features/approvals/hooks.ts` modifié pour :
  - Utiliser `useAuthStore()` au lieu de `localStorage.getItem()`
  - Import ajouté : `import { useAuthStore } from '../../lib/authStore'`

---

## ⚠️ ACTIONS REQUISES AVANT DÉPLOIEMENT

### 1. Régénérer les secrets exposés

Le fichier `backend/.env` contenait des secrets réels qui doivent être régénérés :

#### a) SECRET_KEY
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### b) FINANCE_LICENSE_SECRET
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### c) Clés JWT RS256
```bash
# Générer la clé privée
ssh-keygen -t rsa -b 4096 -m PEM -f jwt.key -N ""

# Extraire la clé publique
openssl rsa -in jwt.key -pubout -outform PEM -out jwt.key.pub

# Copier dans .env (remplacer les retours à la ligne par \n)
cat jwt.key | tr '\n' '|' | sed 's/|/\\n/g'
cat jwt.key.pub | tr '\n' '|' | sed 's/|/\\n/g'
```

#### d) Mot de passe PostgreSQL
```bash
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

#### e) Mot de passe pgAdmin (dev uniquement)
```bash
python -c "import secrets; print(secrets.token_urlsafe(16))"
```

#### f) Mot de passe admin initial
```bash
python -c "import secrets, string; alphabet = string.ascii_letters + string.digits + '!@#$%^&*'; print(''.join(secrets.choice(alphabet) for _ in range(20)))"
```

### 2. Mettre à jour les variables d'environnement

Créer un fichier `backend/.env` basé sur `backend/.env.example` avec les nouveaux secrets :

```bash
cp backend/.env.example backend/.env
# Éditer backend/.env avec les secrets générés ci-dessus
```

### 3. Révoquer l'accès Supabase exposé

Le fichier `.env` contenait :
```
SUPABASE_URL=https://gcnkrayueeontqnwcnhk.supabase.co
```

**Actions :**
- Révoquer la clé `SUPABASE_ANON_KEY` exposée dans le dashboard Supabase
- Générer une nouvelle clé
- Mettre à jour `backend/.env` et les variables d'environnement de production

### 4. Configurer CORS pour la production

Dans le fichier `.env` de production, définir :
```bash
CORS_ALLOWED_ORIGINS=https://votre-domaine.com,https://app.votre-domaine.com
```

### 5. Désactiver pgAdmin en production

pgAdmin est maintenant dans le profil `dev`. Pour le démarrer en développement :
```bash
docker-compose --profile dev up
```

En production, il ne sera pas démarré par défaut.

---

## Vulnérabilités Restantes (Sprint 3)

Les vulnérabilités suivantes nécessitent des modifications plus importantes et seront traitées dans le Sprint 3 :

### SEC-06 : `org_id=1` hardcodé
- **Impact :** Isolation multi-tenant nulle
- **Fichiers :** `backend/app/api/v1/admin.py` (9+ occurrences), `core/module_license_deps.py:36`
- **Correction :** Extraire `org_id` du JWT via `current_user.get("org_id")` dans chaque requête

---

## Checklist de Déploiement

Avant tout déploiement en production :

- [ ] Tous les secrets ont été régénérés
- [ ] Le fichier `backend/.env` n'est PAS commité (vérifier `.gitignore`)
- [ ] `APP_ENV=production` est défini
- [ ] `CORS_ALLOWED_ORIGINS` contient uniquement les domaines de production
- [ ] Les clés JWT RS256 sont définies et valides
- [ ] `ADMIN_PASSWORD` est défini pour le premier démarrage
- [ ] pgAdmin est désactivé (pas de `--profile dev`)
- [ ] Le port 5432 (PostgreSQL) n'est PAS exposé publiquement
- [ ] Les logs ne contiennent aucun secret

---

## Tests de Validation

### Test SEC-04 : Endpoint proxy/end
```bash
# En tant qu'employé (doit échouer avec 403)
curl -X POST http://localhost:8000/api/v1/admin/proxy/end \
  -H "Authorization: Bearer $EMPLOYEE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"proxy_log_id": 1, "entries_created": 5}'

# En tant qu'admin (doit réussir)
curl -X POST http://localhost:8000/api/v1/admin/proxy/end \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"proxy_log_id": 1, "entries_created": 5}'
```

### Test SEC-07 : Blocage démarrage sans clés JWT
```bash
# Supprimer temporairement les clés JWT du .env
APP_ENV=production docker-compose up backend
# Doit afficher : "CRITICAL: AUTH_PRIVATE_KEY and AUTH_PUBLIC_KEY must be set in production"
```

### Test SEC-08 : CORS restrictif
```bash
# Depuis un domaine non autorisé (doit échouer)
curl -X GET http://localhost:8000/api/v1/timesheet/entries \
  -H "Origin: https://malicious-site.com" \
  -H "Authorization: Bearer $TOKEN" \
  -v
# Vérifier l'absence de header Access-Control-Allow-Origin
```

---

**Fin du rapport — Sprint 0 complété**
