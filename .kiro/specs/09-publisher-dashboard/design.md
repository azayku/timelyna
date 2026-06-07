# Design — Publisher Dashboard

## Separate Auth Context
Publisher dashboard uses a **separate JWT issuer** (`publisher-admin`) with its own login endpoint. Publisher users are NOT in the `employees` table.

```sql
CREATE TABLE publisher_users (
  id BIGSERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(50) DEFAULT 'publisher',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE publisher_clients (
  client_id VARCHAR(50) PRIMARY KEY,  -- CLIENT-ABC-123
  company_name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  status VARCHAR(50) DEFAULT 'active',
  api_key_hash VARCHAR(255) UNIQUE NOT NULL,
  onboarded_date DATE,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE validation_checks (
  id BIGSERIAL PRIMARY KEY,
  license_id VARCHAR(100),
  client_id VARCHAR(50),
  check_timestamp TIMESTAMP DEFAULT NOW(),
  request_ip VARCHAR(45),
  result VARCHAR(50),  -- valid|expired|revoked|invalid
  error_code VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_client_time (client_id, check_timestamp)
);

CREATE TABLE audits (
  audit_id VARCHAR(100) PRIMARY KEY,
  client_id VARCHAR(50),
  status VARCHAR(50),  -- pending|running|completed|failed
  results JSONB,
  triggered_by VARCHAR(255),
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);
```

## API (Publisher-only, prefix `/api/v1/publisher/`)
```
POST   /publisher/auth/login
GET    /publisher/plugins
POST   /publisher/plugins                  upload new plugin ZIP
GET    /publisher/plugins/{id}/versions
POST   /publisher/releases
POST   /publisher/releases/{id}/publish

GET    /publisher/clients
POST   /publisher/clients                  onboard new client → returns client_id + api_key
GET    /publisher/clients/{id}
POST   /publisher/clients/{id}/rotate-key
POST   /publisher/clients/{id}/suspend

POST   /publisher/licenses
GET    /publisher/licenses
POST   /publisher/licenses/{id}/revoke

GET    /publisher/validation-checks        timeline view
POST   /publisher/clients/{id}/audit       trigger remote audit
GET    /publisher/audits/{id}

# Phone-home endpoint (called by client apps):
POST   /api/v1/license/validate            body: { clientId, apiKey, licenseToken }
```

## License Generation
```python
def generate_license(plugin_id, client_id, expiry, features, limits) -> str:
    payload = {
        "licenseId": f"LICENSE-{plugin_id}-{client_id}-{uuid4()}",
        "pluginId": plugin_id,
        "clientId": client_id,
        "features": features,
        "limits": limits,
        "iat": now(),
        "exp": expiry,
        "grace": expiry + timedelta(days=7),
        "revoked": False,
    }
    return jwt.encode(payload, PUBLISHER_PRIVATE_KEY, algorithm="RS256")
```

## Alert Rules Engine (Celery Beat)
```
Every 5 min: check validation_checks last 1h per client
  → If 3+ failures → POST to alert_webhook + email publisher admin

Every day: check license expiry
  → 60 days before → email client admin
  → 30 days before → email again
  → At grace_end → revoke license
```

## Frontend Pages (Publisher)
- `PublisherLoginPage.tsx`
- `PluginsListPage.tsx` + `PluginDetailPage.tsx` + `UploadPluginModal.tsx`
- `ClientsListPage.tsx` + `ClientDetailPage.tsx` + `OnboardClientModal.tsx`
- `LicensesListPage.tsx` + `CreateLicenseModal.tsx`
- `ReleasesPage.tsx` + `CreateReleaseModal.tsx`
- `AuditDashboardPage.tsx` — validation timeline + trigger audit button
- `AlertRulesPage.tsx`

# Tasks — Publisher Dashboard

- [ ] **9.1** Migration: `publisher_users`, `publisher_clients`, `validation_checks`, `audits` tables
- [ ] **9.2** Separate publisher auth: `POST /publisher/auth/login` with own JWT issuer
- [ ] **9.3** `ClientService.onboard()` — generate client_id + api_key, hash + store api_key
- [ ] **9.4** `ClientService.rotate_api_key()` — new key, revoke old
- [ ] **9.5** `LicenseGeneratorService.generate(plugin_id, client_id, config)` — sign JWT with publisher private key
- [ ] **9.6** `LicenseService.revoke(license_id)` — set revoked flag in DB (detected at next phone-home)
- [ ] **9.7** `POST /api/v1/license/validate` phone-home endpoint — check DB, log to validation_checks, return features
- [ ] **9.8** `ReleaseService.publish(release_id)` — set status, notify targeted clients via Celery
- [ ] **9.9** Celery beat: alert rules engine (validation failure threshold, expiry warnings)
- [ ] **9.10** `AuditService.trigger(client_id)` — async Celery audit task (check license, plugin status, resource usage)
- [ ] **9.11** Register all publisher routes with `require_role('publisher')`
- [ ] **9.12** Unit test: license generation — correct payload, valid RS256 signature
- [ ] **9.13** Unit test: phone-home — valid, revoked, expired licenses
- [ ] **9.14** Unit test: alert rule — 3 failures triggers alert, 2 does not
- [ ] **9.15** Create `PublisherLoginPage.tsx` (separate route `/publisher/login`)
- [ ] **9.16** Create `ClientsListPage.tsx` + `OnboardClientModal.tsx`
- [ ] **9.17** Create `CreateLicenseModal.tsx` with feature checkboxes + limits inputs
- [ ] **9.18** Create `AuditDashboardPage.tsx` — validation timeline table + manual trigger
- [ ] **9.19** Create `AlertRulesPage.tsx` — list rules, enable/disable toggles
