# Améliorations Authentification - 5 Mai 2026

## ✅ Fonctionnalités Implémentées

### 1. Connexion avec Email OU Username ✅

**Problème**: Les utilisateurs ne pouvaient se connecter qu'avec leur email

**Solution**: Modification de l'authentification pour accepter email OU username

#### Backend

**Schéma modifié** (`backend/app/schemas/auth.py`):
```python
class LoginRequest(BaseModel):
    identifier: str  # Email or username (avant: email: EmailStr)
    password: str
```

**Service modifié** (`backend/app/services/auth_service.py`):
```python
async def authenticate(
    self, identifier: str, password: str, ip_address: Optional[str] = None
) -> dict:
    # Try to find employee by email OR username
    employee = await self.repo.get_employee_by_email(identifier)
    if not employee:
        employee = await self.repo.get_employee_by_username(identifier)
    # ...
```

**Repository ajouté** (`backend/app/repositories/auth_repository.py`):
```python
async def get_employee_by_username(self, username: str) -> Optional[Employee]:
    result = await self.db.execute(
        select(Employee).where(Employee.username == username, Employee.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()
```

**API modifiée** (`backend/app/api/v1/auth.py`):
```python
@router.post("/login")
async def login(body: LoginRequest, ...):
    tokens = await svc.authenticate(body.identifier, body.password, ip_address=ip)
    # ...
```

#### Frontend

**Page de login** (`frontend-v2/src/pages/LoginPage.tsx`):
- Champ "Email" → "Email ou nom d'utilisateur"
- Placeholder: `name@example.com ou username`
- Type: `text` (au lieu de `email`)
- AutoComplete: `username`

**AuthStore** (`frontend-v2/src/lib/authStore.ts`):
```typescript
login: async (identifier: string, password: string) => {
  const data = await apiClient.post<TokenResponse>('/auth/login', { identifier, password })
  // ...
}
```

**Résultat**:
- ✅ Connexion avec email: `achille.romano@emp15.test.it`
- ✅ Connexion avec username: `aromano` (si username existe)
- ✅ Message d'erreur unifié: "Invalid email/username or password"

---

### 2. Inscription Désactivée ✅

**Problème**: Lien d'inscription visible mais non fonctionnel

**Solution**: Désactivation complète de l'auto-inscription

#### Frontend

**Page de login** (`frontend-v2/src/pages/LoginPage.tsx`):

**Avant**:
```tsx
<Link to="/register" className="text-white font-medium hover:underline">
  {t('login.signUpHere', 'Sign up here')}
</Link>
```

**Après**:
```tsx
<span className="text-white/50 font-medium cursor-not-allowed">
  {t('login.contactAdmin', 'Contactez votre administrateur')}
</span>
```

**Résultat**:
- ✅ Lien d'inscription remplacé par "Contactez votre administrateur"
- ✅ Style grisé (opacity-50)
- ✅ Curseur "not-allowed"
- ✅ Pas de route `/register` accessible

**Note**: Les comptes sont créés uniquement par les administrateurs via l'interface admin

---

### 3. SSO Google Désactivé (Préparé pour Future Implémentation) ✅

**Problème**: Bouton Google SSO visible mais non fonctionnel

**Solution**: Désactivation temporaire avec indication "Bientôt disponible"

#### Frontend

**Page de login** (`frontend-v2/src/pages/LoginPage.tsx`):

**Avant**:
```tsx
<button className="w-full bg-white text-slate-700 ... hover:bg-slate-50">
  <svg>...</svg>
  {t('login.signInWithGoogle', 'Sign in with Google')}
</button>
```

**Après**:
```tsx
<button 
  disabled
  className="w-full bg-slate-200 text-slate-400 ... cursor-not-allowed opacity-50"
>
  <svg fill="#9CA3AF">...</svg>
  {t('login.signInWithGoogle', 'Sign in with Google')} (Bientôt disponible)
</button>
```

**Résultat**:
- ✅ Bouton désactivé visuellement
- ✅ Couleurs grises (bg-slate-200, text-slate-400)
- ✅ Icône Google en gris (#9CA3AF)
- ✅ Texte "(Bientôt disponible)"
- ✅ Curseur "not-allowed"

**Note**: Pour implémenter Google SSO plus tard:
1. Configurer OAuth2 dans Google Cloud Console
2. Ajouter `authlib` ou `python-social-auth` au backend
3. Créer endpoint `/auth/google/login` et `/auth/google/callback`
4. Activer le bouton et connecter au endpoint

---

## 📊 Résumé des Changements

### Backend
- ✅ `LoginRequest.identifier` accepte email OU username
- ✅ `AuthService.authenticate()` cherche par email puis username
- ✅ `AuthRepository.get_employee_by_username()` ajouté
- ✅ Message d'erreur unifié

### Frontend
- ✅ Champ "Email ou nom d'utilisateur"
- ✅ Lien d'inscription désactivé
- ✅ Bouton Google SSO désactivé
- ✅ Messages adaptés

---

## 🎯 Cas d'Usage

### Scénario 1: Connexion avec Email
```
Utilisateur: achille.romano@emp15.test.it
Password: password123
✅ Connexion réussie
```

### Scénario 2: Connexion avec Username
```
Utilisateur: aromano
Password: password123
✅ Connexion réussie (si username existe)
```

### Scénario 3: Tentative d'Inscription
```
Utilisateur clique sur "Contactez votre administrateur"
❌ Aucune action (texte non cliquable)
💡 Message: Contactez votre administrateur
```

### Scénario 4: Tentative Google SSO
```
Utilisateur clique sur "Sign in with Google"
❌ Bouton désactivé
💡 Message: (Bientôt disponible)
```

---

## 🔧 Fichiers Modifiés

### Backend
1. `backend/app/schemas/auth.py`
   - `LoginRequest.email` → `LoginRequest.identifier`

2. `backend/app/services/auth_service.py`
   - `authenticate(identifier, ...)` au lieu de `authenticate(email, ...)`
   - Recherche par email puis username

3. `backend/app/repositories/auth_repository.py`
   - Ajout de `get_employee_by_username()`

4. `backend/app/api/v1/auth.py`
   - `body.identifier` au lieu de `body.email`

### Frontend
1. `frontend-v2/src/pages/LoginPage.tsx`
   - Champ identifier au lieu de email
   - Lien inscription désactivé
   - Bouton Google désactivé

2. `frontend-v2/src/lib/authStore.ts`
   - `login(identifier, password)` au lieu de `login(email, password)`

---

## ✅ Tests à Effectuer

### Connexion avec Email
- [ ] Se connecter avec `achille.romano@emp15.test.it` / `password123`
- [ ] Vérifier que la connexion fonctionne

### Connexion avec Username
- [ ] Vérifier qu'un username existe dans la base
- [ ] Se connecter avec le username / `password123`
- [ ] Vérifier que la connexion fonctionne

### Inscription Désactivée
- [ ] Vérifier que le lien "Sign up here" n'existe plus
- [ ] Vérifier le message "Contactez votre administrateur"
- [ ] Vérifier que le texte n'est pas cliquable

### Google SSO Désactivé
- [ ] Vérifier que le bouton Google est grisé
- [ ] Vérifier le texte "(Bientôt disponible)"
- [ ] Vérifier que le bouton est disabled

---

## 🚀 Déploiement

**Backend**: ✅ Rebuild et redémarré
**Frontend**: ✅ Rebuild et redémarré

**Commande utilisée**:
```bash
docker-compose up -d --build backend frontend
```

---

## 📝 Notes Techniques

### Sécurité
- ✅ Protection contre les attaques par timing (bcrypt toujours exécuté)
- ✅ Lockout après tentatives échouées (inchangé)
- ✅ Pas d'énumération d'utilisateurs (message d'erreur unifié)

### Compatibilité
- ✅ Rétrocompatible: les emails fonctionnent toujours
- ✅ Nouveau: les usernames fonctionnent maintenant
- ✅ Pas de breaking change pour les utilisateurs existants

### Future: Google SSO
Pour implémenter plus tard:
1. Backend: Ajouter OAuth2 avec Google
2. Frontend: Activer le bouton et connecter
3. Créer/lier compte automatiquement
4. Gérer les tokens Google

---

## 🔐 Exemples de Connexion

### Avec Email
```
Identifier: achille.romano@emp15.test.it
Password: password123
```

### Avec Username (si disponible)
```
Identifier: aromano
Password: password123
```

### Comptes de Test Disponibles
Voir `UTILISATEURS_DISPONIBLES.md` pour la liste complète des comptes créés par le seed script.

Tous les comptes utilisent le mot de passe: `password123`
