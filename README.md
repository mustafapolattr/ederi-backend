# Ederi Backend

Backend for **Ederi**, an AI-assisted personal finance assistant. It is a Django REST API that serves an Android client: accounts, transactions, budgets, goals, recurring payments, a dashboard with forecasts, and AI features (natural-language transaction parsing, spending analysis, chat, and "can I afford this?" scenarios).

## Architecture

```mermaid
flowchart LR
    A[Android app] -->|REST /api/v1, JWT| B

    subgraph B[Django modular monolith]
        direction TB
        U[users] --- AC[accounts] --- T[transactions] --- C[categories]
        BU[budgets] --- G[goals] --- R[recurring_payments] --- CO[core: dashboard]
        AI[ai: parse / analyze / chat / scenario]
    end

    B --> P[(PostgreSQL)]
    B --> RD[(Redis)]
    RD --> W[Celery worker]
    AI -->|aggregated data only| GM[Gemini API]
```

One deployable Django project (`config/`) with one app per domain under `apps/`. No microservices. The only module that knows about Gemini is `apps/ai/llm.py`.

## Key design decisions

| Decision | Why |
|---|---|
| **The LLM never does financial math.** Every number (balances, totals, forecasts, available-to-spend, scenario outcomes) is computed in deterministic backend services; the LLM only explains numbers it is given. | LLMs make arithmetic mistakes. Money figures must be reproducible and testable. |
| **Money is `Decimal` / PostgreSQL `NUMERIC(14,2)` everywhere.** No floats. | Floating point can't represent decimal currency exactly, and rounding errors add up. |
| **AI output never writes to the DB directly.** `parse-transaction` checks the LLM JSON against a schema serializer, then runs it through the normal `TransactionSerializer` business validation, and returns a *proposal*. The client saves it with a normal `POST /transactions/` only after the user confirms. | The model can hallucinate accounts, amounts, or categories. The user stays in control of their ledger. |
| **Only aggregated data goes to the LLM, and user text is fenced as untrusted.** Prompts carry backend-computed summaries, never raw transaction lists. Free text from the user sits in a delimited section that is explicitly marked as data, not instructions (`apps/ai/prompts.py`). | Data minimisation, plus defence against prompt injection. |
| **Account balance is not stored.** `current_balance` = `initial_balance` + the transaction ledger, computed with aggregate queries (`apps/transactions/services.py`). | One source of truth, so the stored value can't drift from the ledger. |
| **A transfer is one row with `to_account`.** It takes money out of `account` and adds it to `to_account`. Both accounts must be different and use the same currency. | Net worth stays the same after a transfer, and there's no second row to fall out of sync. |
| **Dashboard totals are grouped by currency.** Balances, monthly income/expense, forecast, and available-to-spend are returned per currency. | There is no FX conversion. Adding up different currencies would give a meaningless number. |
| **Recurring payments and budgets aren't counted twice.** In available-to-spend, a recurring expense is skipped if its category already has an active budget this period, because the budget's remaining amount already reserves that money. | Otherwise the same planned spend would be subtracted twice. |
| **Security basics.** Every queryset is filtered by `request.user`, so other users' objects return 404 (IDOR protection). JWT refresh tokens rotate and are blacklisted after rotation. Auth endpoints are throttled. Each user gets a daily AI request quota (`AI_DAILY_REQUEST_LIMIT`, default 20). | Protects user data and keeps LLM costs bounded. |

## Tech stack

- Python 3.12, Django 5.0, Django REST Framework 3.15
- djangorestframework-simplejwt (JWT auth with refresh rotation + blacklist)
- PostgreSQL 16 (psycopg 3)
- Redis 7 + Celery 5.3
- Google Gemini via REST (`requests`), model set by `LLM_MODEL` (default `gemini-flash-lite-latest`)
- pytest, pytest-django, factory-boy
- Docker Compose for local development, gunicorn for production

## Local setup

```bash
# 1. Environment
cp .env.example .env          # set SECRET_KEY, and LLM_API_KEY for the AI endpoints

# 2a. Everything in Docker (db, redis, web, celery)
docker compose -f docker/docker-compose.yml up --build
docker compose -f docker/docker-compose.yml exec web python manage.py migrate

# 2b. Or: only db + redis in Docker, Django on the host
docker compose -f docker/docker-compose.yml up -d db redis
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements/dev.txt
python manage.py migrate
python manage.py runserver
```

Postgres is exposed on host port **5433** and Redis on **6380** so they don't clash with local installs. If you run Django on the host, point `DATABASE_URL` and the Redis URLs in `.env` at those ports (e.g. `postgres://ederi:ederi@localhost:5433/ederi`).

The API is served at `http://localhost:8000/api/v1/`. Health check: `GET /api/v1/health/`.

## Tests

```bash
docker compose -f docker/docker-compose.yml up -d db   # tests need PostgreSQL
pytest                                                  # uses config.settings.test
pytest --cov=apps                                       # with coverage
```

**157 tests** in these areas:

| App | Tests | Covers |
|---|---:|---|
| ai | 34 | parse-transaction validation path, analyze, chat, scenario, LLM client errors, prompt construction, daily quota |
| transactions | 24 | CRUD API, ledger balance math, transfers |
| users | 19 | register, login/refresh/logout, password reset, email verification, user model |
| recurring_payments | 17 | CRUD API, expected-totals service |
| goals | 16 | CRUD API, progress services |
| budgets | 13 | CRUD API, budget status services |
| core | 13 | health, dashboard, month-end forecast, available-to-spend |
| accounts | 12 | CRUD API, model |
| categories | 9 | API, seeded default categories |

## API overview

All endpoints are under `/api/v1/` and need `Authorization: Bearer <access>` unless marked public.

| Area | Method & path | Notes |
|---|---|---|
| Health | `GET /health/` | Public |
| Auth | `POST /auth/register/` | Public |
| | `POST /auth/login/`, `POST /auth/login/refresh/` | Public. JWT pair / rotated refresh |
| | `POST /auth/logout/` | Public. Blacklists the given refresh token |
| | `POST /auth/password-reset/`, `POST /auth/password-reset/confirm/` | Public |
| | `POST /auth/email/verify/` | Public |
| | `POST /auth/email/resend/` | |
| | `GET/PATCH /auth/profile/` | |
| Accounts | `/accounts/`, `/accounts/{id}/` | CRUD, balance is computed |
| Categories | `/categories/`, `/categories/{id}/` | CRUD, plus system defaults |
| Transactions | `/transactions/`, `/transactions/{id}/` | CRUD (income / expense / transfer) |
| Budgets | `/budgets/`, `/budgets/{id}/` | CRUD |
| Goals | `/goals/`, `/goals/{id}/` | CRUD |
| Recurring | `/recurring-payments/`, `/recurring-payments/{id}/` | CRUD |
| Dashboard | `GET /dashboard/` | Per-currency totals, budgets, goals, forecast, available-to-spend |
| AI | `POST /ai/parse-transaction/` | Text → validated transaction proposal (not saved) |
| | `POST /ai/analyze/` | Narrative on backend-computed spending comparison |
| | `POST /ai/chat/` | Q&A over aggregated financial summary |
| | `POST /ai/scenario/` | "Can I afford X?" with numbers computed by the backend |

CRUD routes are DRF `ModelViewSet`s: `GET`/`POST` on the list, `GET`/`PUT`/`PATCH`/`DELETE` on the detail.

## Known limitations / roadmap

- **No CSV import yet.** `apps/imports` is empty scaffolding.
- **No notifications yet.** `apps/notifications` is empty scaffolding. `apps/reports` is too.
- **No FX conversion.** Amounts in different currencies are never combined, and transfers between different currencies are rejected.
- **No bank integrations.** Out of scope for the MVP by design.
