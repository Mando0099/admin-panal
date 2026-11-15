# Why login did not work on the current Cloudflare deployment

The screenshot showed a Worker serving static assets, with no Worker script/backend attached. The HTML login form sends `POST /auth/token`; static assets do not implement that endpoint. A FastAPI server must be running and reachable at the API URL.

This ZIP fixes backend login handling and improves the front-end error message, but it does not turn the static-assets-only Worker into a FastAPI server. Deploy the Docker backend to a compatible container/Python host, configure its environment variables, and then connect the frontend to that backend.

Set these backend environment variables before first start:
- `ADMIN_EMAIL`: the admin email you want
- `ADMIN_PASSWORD`: a long, unique password
- `ADMIN_SYNC_PASSWORD_ON_STARTUP=true`
- `JWT_SECRET`: a random secret of at least 32 bytes
- `DATABASE_URL`: your persistent database connection string

Do not put `ADMIN_PASSWORD`, `JWT_SECRET`, or provider secret keys in frontend code or public static assets.

If the frontend remains on Cloudflare and the API is hosted elsewhere, edit `frontend/config.js` before uploading the frontend and set `window.MH_API_BASE` to the backend HTTPS origin (no trailing slash). Also set the backend `CORS_ORIGINS` to the exact Cloudflare frontend origin.
