# 🚀 Instructions de déploiement

## Problème : Déconnexion au rafraîchissement

### ✅ Solution implémentée
Le token JWT est maintenant persisté dans `localStorage` pour éviter la déconnexion au rafraîchissement de la page.

**Fichiers modifiés :**
- `frontend-v2/src/lib/tokenStore.ts` - Ajout de la persistence localStorage
- `frontend-v2/src/lib/authStore.ts` - Amélioration de la logique de rehydration

### 📦 Déploiement requis

Pour que les changements prennent effet, vous devez **reconstruire le container Docker frontend** :

```bash
# Option 1 : Reconstruire uniquement le frontend
docker-compose up -d --build frontend

# Option 2 : Reconstruire tous les containers
docker-compose up -d --build

# Option 3 : Arrêter, reconstruire et redémarrer
docker-compose down
docker-compose up -d --build
```

### 🔍 Vérification

Après le déploiement :

1. **Connectez-vous** à l'application
2. **Ouvrez les DevTools** (F12) → Onglet "Application" → "Local Storage"
3. Vérifiez que la clé `access_token` est présente
4. **Rafraîchissez la page** (F5 ou Ctrl+R)
5. Vous devriez rester connecté ✅

### 🐛 Si le problème persiste

1. **Vider le cache du navigateur** :
   - Chrome/Edge : Ctrl+Shift+Delete
   - Firefox : Ctrl+Shift+Delete
   - Cocher "Cookies" et "Cache"

2. **Vérifier les logs du backend** :
   ```bash
   docker-compose logs backend
   ```

3. **Vérifier que le container frontend est bien mis à jour** :
   ```bash
   docker-compose ps
   docker-compose logs frontend
   ```

4. **Forcer la reconstruction sans cache** :
   ```bash
   docker-compose build --no-cache frontend
   docker-compose up -d frontend
   ```

### 📝 Notes techniques

**Avant (problème) :**
- Token stocké uniquement en mémoire (`let _token: string | null = null`)
- Au rafraîchissement : token perdu → déconnexion

**Après (solution) :**
- Token stocké en mémoire ET dans localStorage
- Au rafraîchissement : token récupéré depuis localStorage → reste connecté
- Fallback sur refresh token (httpOnly cookie) si localStorage échoue

### 🔐 Sécurité

**Note :** Stocker le token dans localStorage est un compromis entre UX et sécurité :
- ✅ **Avantage** : Pas de déconnexion au rafraîchissement
- ⚠️ **Risque** : Vulnérable aux attaques XSS (Cross-Site Scripting)

**Mitigations en place :**
- Content Security Policy (CSP) headers
- Validation stricte des inputs
- Expiration du token (8h)
- Refresh token dans httpOnly cookie (plus sécurisé)

**Alternative plus sécurisée (future) :**
- Utiliser uniquement les httpOnly cookies
- Implémenter un endpoint `/auth/me` pour vérifier l'authentification
- Appeler cet endpoint au chargement de l'app

---

**Date :** 2026-05-05  
**Build :** ✅ 524ms, 0 erreurs  
**Status :** ⏳ En attente de déploiement Docker
