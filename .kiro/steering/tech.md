---
inclusion: always
---

# Timelyna — Technology Stack

## Backend
- **Framework:** FastAPI (Python 3.11+)
- **Server:** Uvicorn (ASGI)
- **ORM:** SQLAlchemy 2.x (async)
- **Validation:** Pydantic v2
- **Auth:** PyJWT (RS256), passlib (bcrypt)
- **Task Queue:** Celery + Redis
- **Scheduler:** APScheduler
- **Testing:** pytest + httpx (async)

## Frontend
- **Framework:** React 18+ with TypeScript
- **Build:** Vite
- **Styling:** Tailwind CSS (utility-first)
- **Data Fetching:** React Query (TanStack Query v5)
- **State:** Zustand (lightweight global state)
- **Forms:** React Hook Form + Zod
- **Charts:** Recharts
- **Icons:** Lucide React
- **Testing:** Vitest + React Testing Library

## Database & Storage
- **Primary DB:** PostgreSQL 15+
- **Cache / Queue Broker:** Redis 7+
- **File Storage:** AWS S3 (plugin ZIPs, PDF invoices, backups)

## Infrastructure
- **Containerization:** Docker + Docker Compose
- **CI/CD:** GitHub Actions
- **Hosting:** AWS (ECS Fargate) or DigitalOcean App Platform
- **CDN / Gateway:** CloudFlare

## Monitoring
- **Errors:** Sentry
- **Metrics:** Prometheus + Grafana
- **Logs:** ELK Stack (Elasticsearch, Logstash, Kibana)

## Conventions
- REST API versioned at `/api/v1/`
- All dates in ISO 8601 (UTC)
- All monetary values stored as `DECIMAL(12,2)`
- IDs: `BIGINT` auto-increment (core) or `VARCHAR(100)` UUID (plugins/licenses)
- Soft deletes everywhere (`deleted_at` timestamp)
- JWT access tokens: 8h expiry; refresh tokens: 30d
