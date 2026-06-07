# Requirements — Authentication & User Management

## Feature Overview
Foundation authentication system: registration, login, JWT tokens, password management, and role-based access control. Everything else depends on this.

---

## User Stories & Acceptance Criteria

### US-01 — Employee Login
**As an** employee,  
**I want to** log in with my email and password,  
**So that** I can access my personal timesheet dashboard.

**Acceptance Criteria:**
- WHEN a user submits valid credentials THE SYSTEM SHALL return a JWT access token (8h) and set a refresh token in an httpOnly cookie (30d)
- WHEN a user submits invalid credentials THE SYSTEM SHALL return a 401 error with message "Invalid email or password" (no user enumeration)
- WHEN a user's account is inactive THE SYSTEM SHALL return a 403 error
- WHEN a user fails login 5 times in 10 minutes THE SYSTEM SHALL lock the account for 15 minutes
- THE SYSTEM SHALL never return a plain-text password in any response

### US-02 — Token Refresh
**As an** authenticated user,  
**I want to** automatically renew my session,  
**So that** I am not unexpectedly logged out while working.

**Acceptance Criteria:**
- WHEN an access token is expired AND a valid refresh token exists THE SYSTEM SHALL issue a new access token without requiring re-login
- WHEN a refresh token is expired THE SYSTEM SHALL redirect the user to the login page
- THE SYSTEM SHALL invalidate a refresh token after it is used once (rotation)

### US-03 — Logout
**As an** authenticated user,  
**I want to** log out securely,  
**So that** my session is fully terminated.

**Acceptance Criteria:**
- WHEN a user logs out THE SYSTEM SHALL revoke the refresh token server-side
- WHEN a user logs out THE SYSTEM SHALL clear the httpOnly cookie
- WHEN a revoked refresh token is used THE SYSTEM SHALL return a 401 error

### US-04 — Password Change
**As an** authenticated user,  
**I want to** change my password,  
**So that** I can maintain account security.

**Acceptance Criteria:**
- WHEN a user submits a correct current password and a new password (min 8 chars, 1 uppercase, 1 digit) THE SYSTEM SHALL update the password hash
- WHEN a user submits an incorrect current password THE SYSTEM SHALL return a 400 error
- WHEN a password is changed THE SYSTEM SHALL invalidate all existing refresh tokens for that user
- THE SYSTEM SHALL send a confirmation email after a successful password change

### US-05 — Password Reset (Forgot Password)
**As an** unauthenticated user,  
**I want to** reset my password via email,  
**So that** I can regain access to my account.

**Acceptance Criteria:**
- WHEN a user requests a password reset THE SYSTEM SHALL send a reset link valid for 1 hour regardless of whether the email exists (prevent enumeration)
- WHEN a user clicks a valid reset link THE SYSTEM SHALL allow setting a new password
- WHEN a reset link is used THE SYSTEM SHALL invalidate it immediately (single-use)

### US-06 — Role-Based Access Control
**As a** system administrator,  
**I want** role-based permissions enforced on all endpoints,  
**So that** users can only access resources appropriate to their role.

**Acceptance Criteria:**
- THE SYSTEM SHALL enforce roles: `employee`, `manager`, `admin`, `finance`
- WHEN an `employee` accesses a manager-only endpoint THE SYSTEM SHALL return a 403 error
- WHEN an `admin` accesses any endpoint THE SYSTEM SHALL allow access
- THE SYSTEM SHALL include the user's role in the JWT payload
- WHEN a manager accesses team data THE SYSTEM SHALL only return data for their direct reports

### US-07 — User Creation (Admin)
**As an** admin,  
**I want to** create employee accounts,  
**So that** new staff can start using the system.

**Acceptance Criteria:**
- WHEN an admin creates a user with a unique email THE SYSTEM SHALL create the account and send a welcome email with a one-time password setup link
- WHEN an admin creates a user with a duplicate email THE SYSTEM SHALL return a 409 conflict error
- THE SYSTEM SHALL require: email, first_name, last_name, role, manager_id (optional)
