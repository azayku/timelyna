# Design — Authentication & User Management

## Architecture

### Token Strategy
```
Login Request
    │
    ▼
POST /api/v1/auth/login
    │
    ├─ Validate credentials (bcrypt compare)
    ├─ Check account status + rate limit
    │
    ├─ Generate access_token (JWT RS256, 8h)
    │   Payload: { sub, employee_id, org_id, role, iat, exp }
    │
    └─ Generate refresh_token (opaque UUID, stored in DB)
        └─ Set as httpOnly Secure SameSite=Strict cookie
```

### JWT Structure
```json
{
  "sub": "alice@company.fr",
  "employee_id": 42,
  "org_id": 1,
  "role": "employee",
  "iat": 1743292542,
  "exp": 1743321342
}
```
Signed with RS256. Public key exposed at `GET /api/v1/auth/.well-known/jwks.json`.

### Refresh Token Rotation
```
Client sends expired access_token + refresh cookie
    │
POST /api/v1/auth/refresh
    │
    ├─ Validate refresh token (DB lookup, not expired, not revoked)
    ├─ Invalidate old refresh token (rotation)
    ├─ Issue new access_token + new refresh_token
    └─ Set new refresh cookie
```

---

## Components

### Backend

**`app/api/v1/auth.py`** — Route handlers
- `POST /login` → `AuthService.authenticate()`
- `POST /logout` → `AuthService.revoke_token()`
- `POST /refresh` → `AuthService.refresh()`
- `POST /password/change` → `AuthService.change_password()`
- `POST /password/reset-request` → `AuthService.request_reset()`
- `POST /password/reset` → `AuthService.reset_password()`
- `GET /.well-known/jwks.json` → Returns RS256 public key

**`app/services/auth_service.py`** — Business logic
- `authenticate(email, password) → tokens`
- `refresh(token) → new_tokens`
- `change_password(employee_id, old_pw, new_pw)`
- `request_reset(email)` — always returns 200
- `reset_password(token, new_password)`

**`app/core/security.py`** — JWT utilities
- `create_access_token(data: dict) → str`
- `decode_access_token(token: str) → dict`
- `get_current_user` — FastAPI dependency
- `require_role(*roles)` — FastAPI dependency factory

**`app/models/auth.py`** — ORM models
- `RefreshToken`: `id`, `employee_id`, `token_hash`, `expires_at`, `revoked_at`, `created_at`
- `LoginAttempt`: `id`, `email`, `ip_address`, `success`, `attempted_at`
- `PasswordResetToken`: `id`, `employee_id`, `token_hash`, `expires_at`, `used_at`

---

### Database Schema

```sql
CREATE TABLE refresh_tokens (
  id BIGSERIAL PRIMARY KEY,
  employee_id BIGINT NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
  token_hash VARCHAR(255) NOT NULL UNIQUE,
  expires_at TIMESTAMP NOT NULL,
  revoked_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_employee (employee_id),
  INDEX idx_token_hash (token_hash)
);

CREATE TABLE login_attempts (
  id BIGSERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL,
  ip_address VARCHAR(45),
  success BOOLEAN NOT NULL,
  attempted_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_email_time (email, attempted_at)
);

CREATE TABLE password_reset_tokens (
  id BIGSERIAL PRIMARY KEY,
  employee_id BIGINT NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
  token_hash VARCHAR(255) NOT NULL UNIQUE,
  expires_at TIMESTAMP NOT NULL,
  used_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

### Frontend

**`src/features/auth/`**
- `LoginPage.tsx` — Form: email + password → `POST /api/v1/auth/login`
- `useAuth.ts` — Zustand store: `{ user, isAuthenticated, login(), logout() }`
- `PrivateRoute.tsx` — Wraps routes, checks auth + role
- `api.ts` — Axios interceptor: auto-refresh on 401

---

## Security Notes
- Passwords hashed with bcrypt (12 rounds)
- Rate limit: 5 failed logins → 15-min lockout (checked via `login_attempts` table)
- All password reset emails use `time.sleep()` equalization to prevent timing attacks
- RS256 keys generated at boot, stored as environment variables (`AUTH_PRIVATE_KEY`, `AUTH_PUBLIC_KEY`)
- Refresh cookies: `HttpOnly`, `Secure`, `SameSite=Strict`, path `/api/v1/auth`
