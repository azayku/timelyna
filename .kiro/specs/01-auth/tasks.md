# Tasks — Authentication & User Management

## Implementation Checklist

### Phase A — Backend Foundation
- [x] **1.1** Generate RS256 key pair and load from env (`AUTH_PRIVATE_KEY`, `AUTH_PUBLIC_KEY`)
- [x] **1.2** Create `employees` table migration (include `password_hash`, `employment_status`, `role`)
- [x] **1.3** Create `refresh_tokens` table migration
- [x] **1.4** Create `login_attempts` table migration
- [x] **1.5** Create `password_reset_tokens` table migration
- [x] **1.6** Implement `app/core/security.py`: `create_access_token`, `decode_access_token`
- [x] **1.7** Implement `get_current_user` FastAPI dependency (reads Bearer token from `Authorization` header)
- [x] **1.8** Implement `require_role(*roles)` dependency factory
- [x] **1.9** Implement `AuthService.authenticate()` with bcrypt compare + lockout logic
- [x] **1.10** Implement `AuthService.refresh()` with token rotation
- [x] **1.11** Implement `AuthService.revoke_token()` (logout)
- [x] **1.12** Implement `AuthService.change_password()` + invalidate all refresh tokens
- [x] **1.13** Implement `AuthService.request_reset()` — always returns 200, sends email async
- [x] **1.14** Implement `AuthService.reset_password()` — validates token, sets new password
- [x] **1.15** Register all auth routes in `app/api/v1/auth.py`
- [x] **1.16** Expose `GET /.well-known/jwks.json` endpoint

### Phase B — Backend Tests
- [x] **1.17** Unit test: `create_access_token` / `decode_access_token`
- [x] **1.18** Integration test: `POST /login` — success, wrong password, inactive account
- [x] **1.19** Integration test: rate limiting (5 failures → lockout)
- [x] **1.20** Integration test: `POST /refresh` — success, expired, revoked, rotation
- [x] **1.21** Integration test: `POST /logout` — token revoked
- [x] **1.22** Integration test: `POST /password/change`
- [x] **1.23** Integration test: `POST /password/reset-request` + `POST /password/reset`
- [x] **1.24** Integration test: RBAC — employee accessing manager route returns 403

### Phase C — Frontend
- [x] **1.25** Create `LoginPage.tsx` with email/password form, validation (Zod), error display
- [x] **1.26** Implement `useAuth` Zustand store: `login()`, `logout()`, `user`, `isAuthenticated`
- [x] **1.27** Implement Axios interceptor: intercept 401 → `POST /refresh` → retry original request → if refresh fails, redirect to `/login`
- [x] **1.28** Create `PrivateRoute.tsx`: redirect to `/login` if not authenticated, check role
- [x] **1.29** Create `ChangePasswordPage.tsx`
- [x] **1.30** Create `ForgotPasswordPage.tsx` + `ResetPasswordPage.tsx`
- [x] **1.31** Hook up all auth routes in the React Router config

### Phase D — Admin User Management
- [x] **1.32** Implement `POST /api/v1/admin/users` (admin only) — create employee + send welcome email
- [x] **1.33** Implement `GET /api/v1/admin/users` — list with pagination
- [x] **1.34** Implement `PUT /api/v1/admin/users/{id}` — update role, status, manager
- [x] **1.35** Create `AdminUsersPage.tsx` with user list + create form
