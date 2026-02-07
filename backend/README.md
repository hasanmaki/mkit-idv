## Auth Flow (Access JWT + Opaque Refresh)

**Access token (JWT)** is short-lived and used for API authorization.  
**Refresh token (opaque)** is stored hashed in DB and used to rotate tokens.

### Endpoints
- `POST /api/v1/auth/login` (OAuth2 password form)
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`

### Admin Endpoints
- `POST /api/v1/auth/admin/revoke-session`
- `POST /api/v1/auth/admin/revoke-user-sessions`
- `GET /api/v1/auth/admin/sessions?user_id=...`

### Protected Example
- `GET /api/v1/me`

### Environment
- `JWT_SECRET_KEY` required in production
- `HTTPX_*` optional for httpx client config:
  - `HTTPX_TIMEOUT_SECONDS`
  - `HTTPX_MAX_CONNECTIONS`
  - `HTTPX_MAX_KEEPALIVE`
  - `HTTPX_RETRIES`
  - `HTTPX_BACKOFF_FACTOR`
