# MerchantHub — Cloud Starter with Frontend

Arabic RTL responsive dashboard + FastAPI backend + PostgreSQL.

## What is included
- Arabic responsive web dashboard served at `/`.
- Login against `/auth/token` (admin and merchant roles).
- Admin overview, merchant list, transaction list, withdrawal list.
- Merchant view of own payments.
- Existing backend API and Docker Compose setup.

## Run with Docker
1. Copy `.env.example` to `.env` and set strong unique secrets/passwords.
2. Run `docker compose up --build -d`.
3. Open `http://YOUR_SERVER:8000`.
4. Sign in using the admin email/password configured in `.env`.

## Important limitations
This is a starter/demo implementation, not production-ready financial software. Fawaterak live integration is disabled until the account-specific API endpoint, authentication scheme, request/response mapping, webhook signature and event verification are confirmed. Automated payouts are not implemented. Ledger posting, reconciliation, refunds, settlement controls, rate limiting, audit hardening, migrations, backups, HTTPS and security review must be completed before real transactions.


## Login troubleshooting (important)
- The login email and password are read by the FastAPI backend from `ADMIN_EMAIL` and `ADMIN_PASSWORD` in the backend environment.
- On startup, the configured admin password is synchronized to the admin account (`ADMIN_SYNC_PASSWORD_ON_STARTUP=true`). Set a long unique password before deployment.
- Login sends the email in the OAuth2 `username` field; the API now normalizes email case and surrounding spaces.
- `GET /health` checks that the backend is actually running.
- Pinning `bcrypt==4.0.1` avoids the Passlib/bcrypt compatibility issue in this starter.

## Cloudflare note
Uploading only `frontend/index.html` as static assets does not deploy this FastAPI backend. The browser login calls `POST /auth/token`, so it must reach a running FastAPI service. Host the Docker/FastAPI backend on a Python/container-capable host, then configure the frontend to call that backend (or put a Worker/API proxy in front of it). Cloudflare static assets alone cannot create the FastAPI login endpoint.

- If the frontend and API use different domains, set `window.MH_API_BASE` in `frontend/config.js` to the backend HTTPS origin and set backend `CORS_ORIGINS` to the frontend origin.
