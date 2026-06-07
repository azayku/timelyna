---
inclusion: always
---

# TimesheetPro — Product Overview

## What We're Building
TimesheetPro is a SaaS application for managing worked hours with a **modular plugin ecosystem**. It targets SMEs of 10–500 employees who manage multi-client/multi-project engagements.

## Core Value Proposition
- Employees log hours daily/weekly on projects
- Managers approve timesheets through a structured workflow
- Finance generates client invoices from approved hours
- Publishers extend the platform via installable, licensed plugins

## User Roles
| Role | Description |
|------|-------------|
| `employee` | Logs their own hours, views personal stats |
| `manager` | Approves their team's timesheets |
| `admin` | Full organization access |
| `finance` | Read-only, generates invoices |
| `publisher` | Manages plugins, clients, licenses (separate system) |

## Business Model
- **SaaS Core:** $10–50/user/month
- **Plugins:** 30–70% revenue share with plugin devs
- **Custom Dev:** $1–10K per custom patch

## Key Constraints
- No physical deletion of approved timesheets
- No modification of invoiced timesheets
- All licenses validated locally (JWT) + remotely (phone home)
- Plugin licenses are per-client, non-transferable
- GDPR-compliant audit logs (90-day retention)
