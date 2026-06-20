# Design — License System

## License JWT Payload
```json
{
  "sub": "timelyna-app",
  "iss": "timelyna-publisher",
  "licenseId": "LICENSE-APP-ORG-UUID",
  "organizationId": "ORG-ABC-123",
  "pack": "PRO",
  "features": {
    "timesheet_entry": true,
    "approvals": true,
    "reporting_advanced": true,
    "invoicing": true,
    "integrations": true,
    "sso_saml": false
  },
  "limits": { "max_employees": 50, "max_clients": 20, "max_projects": 100 },
  "iat": 1743292542,
  "exp": 1774828542,
  "grace": 1775433542,
  "revoked": false
}
```
Signed RS256. Publisher private key signs; app validates with embedded public key.

## Validation Flow
```
App Boot
  │
  ├─ Load license token from DB (org settings)
  ├─ Decode + verify RS256 signature
  ├─ Check exp + grace timestamp
  │
  ├─ Check Redis cache: "license:valid:{org_id}" (TTL 24h)
  │   ├─ Cache HIT → use cached result
  │   └─ Cache MISS → POST /api/v1/license/validate (phone home)
  │       ├─ Success → cache result 24h
  │       └─ Unreachable → use last cached result if < 24h old
  │
  └─ Store validated features in request context
```

## Feature Gate Decorator
```python
# Backend
def require_feature(feature_name: str):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            license_ctx = get_license_context()
            if not license_ctx.features.get(feature_name):
                raise LicenseFeatureError(feature=feature_name)
            return await func(*args, **kwargs)
        return wrapper
    return decorator

@require_feature("invoicing")
async def create_invoice(...):
    ...
```

## Limit Check Middleware
```python
async def check_employee_limit(org_id, license_ctx):
    current = await EmployeeRepository.count_active(org_id)
    if license_ctx.limits.max_employees > 0 and current >= license_ctx.limits.max_employees:
        raise LicenseLimitError(resource="employees", current=current, max=license_ctx.limits.max_employees)
```

## DB Table
```sql
CREATE TABLE organization_licenses (
  id BIGSERIAL PRIMARY KEY,
  org_id VARCHAR(100) NOT NULL UNIQUE,
  license_token TEXT NOT NULL,
  pack VARCHAR(50),
  activated_at TIMESTAMP,
  expires_at TIMESTAMP,
  grace_ends_at TIMESTAMP,
  last_validated_at TIMESTAMP,
  validation_status VARCHAR(50) DEFAULT 'valid',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

## Frontend
- `LicenseBanner.tsx` — sticky warning banner when < 60 days to expiry (admin only)
- `UpgradePrompt.tsx` — shown when feature/limit blocked (replaces locked content)
- `LicenseSettingsPage.tsx` — shows current pack, expiry, limits usage, input to activate new serial
- `useLicense.ts` — Zustand store with feature gates (`canUse('invoicing')`, `isAtLimit('employees')`)
