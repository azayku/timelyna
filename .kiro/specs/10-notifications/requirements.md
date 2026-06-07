# Requirements — Notifications

## Acceptance Criteria

### US-01 — In-App Notifications
- WHEN an event occurs (approval, rejection, update, budget warning) THE SYSTEM SHALL create an in-app notification for the target user
- WHEN a user has unread notifications THE SYSTEM SHALL display a badge count in the sidebar
- WHEN a user clicks a notification THE SYSTEM SHALL mark it as read and navigate to the relevant entity

### US-02 — Email Notifications
- THE SYSTEM SHALL send emails for: submission received (manager), approved (employee), rejected with reason (employee), license expiry warning (admin), critical update available (admin)
- WHEN an email send fails THE SYSTEM SHALL retry up to 3 times with exponential backoff

### US-03 — Notification Preferences
- WHEN a user updates notification preferences THE SYSTEM SHALL respect their choices for each notification type
- THE SYSTEM SHALL support: email on/off per event type, daily digest mode

### US-04 — Budget Alerts
- WHEN a project reaches 80% of budget hours THE SYSTEM SHALL notify the project manager
- WHEN a project reaches 100% THE SYSTEM SHALL notify manager + admin

# Design — Notifications

## DB Table
```sql
CREATE TABLE notifications (
  id BIGSERIAL PRIMARY KEY,
  employee_id BIGINT REFERENCES employees(employee_id),
  type VARCHAR(100) NOT NULL,
  title VARCHAR(255) NOT NULL,
  message VARCHAR(1000),
  related_entity_type VARCHAR(50),
  related_entity_id BIGINT,
  action_url VARCHAR(500),
  is_read BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_employee_read (employee_id, is_read),
  INDEX idx_created (created_at)
);
```

## Celery Tasks
```python
# All notification dispatch goes through Celery
send_email_notification.delay(to, subject, template, context)
create_in_app_notification.delay(employee_id, type, title, message, entity)
```

## Email Templates (Jinja2)
- `approval_submitted.html` → to manager
- `approval_approved.html` → to employee
- `approval_rejected.html` → to employee (includes reason)
- `license_expiry_warning.html` → to admin
- `plugin_update_critical.html` → to admin

## API
```
GET  /api/v1/notifications          ?unread=true&page=1
POST /api/v1/notifications/{id}/read
POST /api/v1/notifications/read-all
GET  /api/v1/notifications/preferences
PUT  /api/v1/notifications/preferences
```

## Frontend
- `NotificationBell.tsx` — header icon with unread count badge, polling every 30s
- `NotificationDrawer.tsx` — slide-in panel with notification list
- `NotificationItem.tsx` — icon, title, message, time ago, read indicator
- `NotificationPreferencesPage.tsx` — toggles per notification type

# Tasks — Notifications

- [ ] **10.1** Migration: `notifications` table
- [ ] **10.2** Migration: `notification_preferences` table (employee_id, type, email_enabled, in_app_enabled)
- [ ] **10.3** Celery task: `send_email_notification(to, subject, template_name, context)` with SMTP + retry
- [ ] **10.4** Celery task: `create_in_app_notification(employee_id, type, title, message, entity_type, entity_id)`
- [ ] **10.5** Create Jinja2 email templates: approval_submitted, approval_approved, approval_rejected, license_expiry_warning, plugin_update_critical
- [ ] **10.6** Wire notification dispatch into: `ApprovalService.approve()`, `ApprovalService.reject()`, `TimesheetService.submit_week()`
- [ ] **10.7** Celery beat: `check_budget_warnings()` daily — flag projects at 80%/100% budget
- [ ] **10.8** Register notification API routes
- [ ] **10.9** Unit test: budget warning — 79% (no alert), 80% (alert), 100% (alert + admin)
- [ ] **10.10** Integration test: approve flow → in-app notification created + email queued
- [ ] **10.11** Create `NotificationBell.tsx` with React Query polling every 30s (`refetchInterval: 30000`)
- [ ] **10.12** Create `NotificationDrawer.tsx` with read/unread states
- [ ] **10.13** Create `NotificationPreferencesPage.tsx` with per-type toggle grid
