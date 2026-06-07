# Tasks — Notifications

- [x] **10.1** Migration: `notifications` table
- [x] **10.2** Migration: `notification_preferences` table (employee_id, type, email_enabled, in_app_enabled)
- [x] **10.3** Celery task: `send_email_notification(to, subject, template_name, context)` with SMTP + retry
- [x] **10.4** Celery task: `create_in_app_notification(employee_id, type, title, message, entity_type, entity_id)`
- [x] **10.5** Create Jinja2 email templates: approval_submitted, approval_approved, approval_rejected, license_expiry_warning, plugin_update_critical
- [x] **10.6** Wire notification dispatch into: `ApprovalService.approve()`, `ApprovalService.reject()`, `TimesheetService.submit_week()`
- [x] **10.7** Celery beat: `check_budget_warnings()` daily — flag projects at 80%/100% budget
- [x] **10.8** Register notification API routes
- [x] **10.9** Unit test: budget warning — 79% (no alert), 80% (alert), 100% (alert + admin)
- [x] **10.10** Integration test: approve flow → in-app notification created + email queued
- [x] **10.11** Create `NotificationBell.tsx` with React Query polling every 30s (`refetchInterval: 30000`)
- [x] **10.12** Create `NotificationDrawer.tsx` with read/unread states
- [x] **10.13** Create `NotificationPreferencesPage.tsx` with per-type toggle grid
