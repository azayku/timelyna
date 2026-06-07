# Requirements — License System (Main App)

## Feature Overview
JWT-based licensing controlling access to feature packs (TRIAL, STARTER, PRO, ENTERPRISE). Validated locally (signature) + remotely (phone home).

---

## Acceptance Criteria

### US-01 — License Activation
- WHEN an organization provides a valid license serial THE SYSTEM SHALL parse and validate the JWT locally (RS256 signature + expiry)
- WHEN the JWT is valid THE SYSTEM SHALL perform a remote validation call to confirm the license is not revoked
- WHEN local or remote validation fails THE SYSTEM SHALL disable licensed features and show an upgrade prompt

### US-02 — Feature Gating
- WHEN a user accesses a feature not included in their pack THE SYSTEM SHALL return a 402 error with `{ code: "FEATURE_NOT_INCLUDED", upgrade_url }`
- WHEN a user exceeds a limit (e.g. max employees) THE SYSTEM SHALL return a 402 error with `{ code: "LIMIT_EXCEEDED", current, max }`
- THE SYSTEM SHALL check limits on every create operation for employees, clients, and projects

### US-03 — Offline Grace Period
- WHEN the remote validation endpoint is unreachable THE SYSTEM SHALL use the cached last-valid result for up to 24 hours
- WHEN offline for more than the grace period THE SYSTEM SHALL restrict access to core read-only features only

### US-04 — License Expiry & Renewal
- WHEN a license is within 60 days of expiry THE SYSTEM SHALL show a renewal banner to admins
- WHEN a license expires THE SYSTEM SHALL enter a 7-day grace period with full access
- WHEN the grace period ends THE SYSTEM SHALL disable all licensed features

### US-05 — License Revocation
- WHEN a license is revoked THE SYSTEM SHALL detect this on the next phone-home call
- WHEN revoked THE SYSTEM SHALL immediately disable features and notify the admin
