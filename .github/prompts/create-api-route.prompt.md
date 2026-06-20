# Create API Route

Create a new FastAPI route following the Timelyna conventions.

## Context
- Domain: {{domain}}
- Resource: {{resource}}
- Method: {{method}}

## Requirements
1. Add a new route in `backend/app/api/v1/{{domain}}.py`.
2. Implement business logic in `backend/app/services/{{domain}}_service.py`.
3. Add DB access in `backend/app/repositories/{{domain}}_repository.py`.
4. Define Pydantic schemas in `backend/app/schemas/{{domain}}.py`.
5. Ensure async/await is used throughout.
6. Add basic unit tests in `backend/tests/`.
