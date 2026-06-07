# Tasks — License System

- [x] **6.1** Migration: `organization_licenses` table
- [x] **6.2** Embed publisher RS256 public key as app env var `LICENSE_PUBLIC_KEY`
- [x] **6.3** `LicenseService.validate_local(token)` — decode JWT, verify signature, check exp + grace
- [x] **6.4** `LicenseService.validate_remote(org_id, api_key, token)` — POST to publisher endpoint
- [x] **6.5** Redis caching layer: cache valid result with 24h TTL, fallback to stale on network error
- [x] **6.6** `require_feature(feature_name)` decorator for FastAPI route handlers
- [x] **6.7** `check_limit(resource)` dependency — runs on create operations
- [x] **6.8** `LicenseMiddleware` — validates license on every request, injects license context
- [x] **6.9** `POST /api/v1/admin/license/activate` — store + validate new serial
- [x] **6.10** `GET /api/v1/admin/license/status` — returns pack, features, limits + usage
- [x] **6.11** Unit test: local validation — valid token, expired, revoked, wrong signature
- [x] **6.12** Unit test: feature gate — feature enabled, disabled, 402 response shape
- [x] **6.13** Unit test: limit check — under limit, at limit, over limit
- [x] **6.14** Integration test: cache behavior — hit, miss, stale fallback
- [x] **6.15** `useLicense` Zustand store: `canUse(feature)`, `isAtLimit(resource)`, `daysUntilExpiry`
- [x] **6.16** `LicenseBanner.tsx` — shown to admin when ≤ 60 days left
- [x] **6.17** `UpgradePrompt.tsx` — full-width overlay replacing locked features
- [x] **6.18** `LicenseSettingsPage.tsx` — current status + activate new serial form

### Phase E — Paramètres organisation (post-spec)
- [x] **6.19** Créer modèle `OrgSettings` : `standard_hours_per_day`, `max_hours_per_day`, `overtime_rate_multiplier`, `travel_rate_multiplier`, `default_currency`, `org_name`
- [x] **6.20** `GET /api/v1/admin/settings` — retourne les paramètres courants (défauts si vierge)
- [x] **6.21** `PUT /api/v1/admin/settings` — mise à jour par l'admin
- [x] **6.22** `OrgSettingsPage.tsx` — formulaire de configuration organisation (heures, taux, devise)
- [x] **6.23** Table `org_settings` créée automatiquement au démarrage (`on_startup` dans `main.py`)
