# Ruko Admin Dashboard

FastAPI service that serves a single-page admin dashboard (`/dashboard`) and exposes read-only admin APIs under `/admin/*`.

## Local setup

1. Create and activate a virtualenv (optional).
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Configure environment variables:
   - Copy `.env.example` to `.env` and fill in your Postgres credentials.
4. Create the admin database schema (first time only):
   - `python create_db.py`

## Run

- `python main.py`
- Open `http://localhost:8080/dashboard` (or just `http://localhost:8080/`).

## Docker

- Build: `docker build -t ruko-admin .`
- Run: `docker run --rm -p 8080:8080 --env-file .env ruko-admin`

## Key endpoints

- UI: `GET /dashboard`
- Service health: `GET /health`
- DB health: `GET /admin/db-health`
- Stats: `GET /admin/stats`
- Activity (charts): `GET /admin/activity`
- Top tools: `GET /admin/tools`
- Conversations: `GET /admin/conversations`
- Conversation detail: `GET /admin/conversations/{id}`
- Users: `GET /admin/users`
- User detail: `GET /admin/users/{id}`
- Errors: `GET /admin/errors`
