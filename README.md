# Cookbook

> A self-hosted, multi-user recipe manager with **version-controlled recipes**.
> Every saved change is an immutable version with a star rating — so you always know whether adding 10% more salt was a good idea.

---

## Features

- **Draft → Version workflow** — edit freely in draft state; commit a version when you're happy
- **Star ratings per version** — rate after cooking, not before
- **Ingredient tweaking** — `+` / `−` buttons adjust quantities by a configurable step (default 10%)
- **Side-by-side diff** — compare any two versions to see exactly what changed
- **GitHub integration** — each user connects their own repo; the app commits and pushes autonomously
- **Recipe sharing & forking** — share recipes with other users; fork with attribution
- **Categories & tags** — per-user organisation with full-text search
- **Multi-user** — JWT auth (access + refresh tokens), Argon2 password hashing
- **Self-hosted** — runs on a home NAS or any Docker host; external access via Cloudflare Tunnel

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vue 3 + Vite + PrimeVue 4 |
| State / HTTP | Pinia + Axios |
| Backend | FastAPI (Python 3.12) |
| ORM / DB | SQLAlchemy 2 + SQLite (swappable to PostgreSQL) |
| Migrations | Alembic |
| Auth | JWT (python-jose) + Argon2 (passlib) |
| Encryption | Fernet (GitHub PATs at rest) |
| Version Control | GitPython — per-user local repos, pushed to GitHub |
| Container | Docker + Docker Compose |
| Frontend server | Nginx (multi-stage build) |

---

## Project Structure

```
cookbook/
├── backend/
│   ├── app/
│   │   ├── api/v1/         # Route handlers (auth, users, recipes, categories, tags)
│   │   ├── core/           # Security helpers, Git operations, diff engine
│   │   ├── crud/           # Database query layer
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── config.py       # Settings (pydantic-settings, reads .env)
│   │   ├── database.py     # Engine, session, Base, SQLite pragmas
│   │   └── main.py         # App factory, CORS, router registration
│   ├── alembic/            # DB migrations
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example        # ← copy to .env and fill in
├── frontend/
│   ├── src/
│   │   ├── api/            # Axios client + typed API calls
│   │   ├── components/     # DiffViewer, IngredientRow, RecipeCard, etc.
│   │   ├── views/          # Login, Register, RecipeList, RecipeEditor, Profile, …
│   │   ├── stores/         # Pinia auth store
│   │   ├── router/         # Vue Router (auth guard)
│   │   └── types/          # Shared TypeScript interfaces
│   ├── nginx.conf          # Proxies /api/* → backend, serves SPA
│   └── Dockerfile
├── data/                   # Runtime volume (SQLite + per-user git repos) — gitignored
├── docker-compose.yml
├── .env                    # Docker Compose vars (e.g. APP_PORT) — gitignored
├── .env.example
└── SPECIFICATIONS.md       # Detailed product & architecture spec
```

---

## Deployment

### Prerequisites

- Docker + Docker Compose on the host
- A QNAP NAS (or any Linux host) with a LAN-accessible Docker network

### 1. Clone & configure

```bash
git clone <repo-url> cookbook
cd cookbook

# Docker Compose variables (host port, etc.)
cp .env.example .env

# Backend secrets
cp backend/.env.example backend/.env
```

Edit `backend/.env`:

```dotenv
SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_hex(32))">
ENCRYPTION_KEY=<generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
DATABASE_URL=sqlite:///./data/cookbook.db   # or postgresql://...
```

### 2. Networking

The default compose config attaches the frontend to an **external `qnet` network** (`qnet-dhcp-eth0-6d6da6`) so the container gets a real LAN IP from the router's DHCP. This requires QNAP Container Station's `qnet` driver.

**If running on a different host**, replace the `lan` network block in `docker-compose.yml`:

```yaml
# For a standard Linux host — macvlan (container gets its own LAN IP)
networks:
  lan:
    driver: macvlan
    driver_opts:
      parent: eth0          # replace with your physical interface
    ipam:
      config:
        - subnet: 192.168.1.0/24
          gateway: 192.168.1.1
          ip_range: 192.168.1.240/28   # reserve this range in your router's DHCP exclusions

# OR — simple port mapping (no LAN IP, accessible via host IP + port)
# Remove the 'lan' network entirely and add to the frontend service:
#   ports:
#     - "${APP_PORT:-80}:80"
```

### 3. Start

```bash
docker compose up -d
```

Check the assigned LAN IP:

```bash
docker inspect cookbook-frontend-1 | grep -A5 '"qnet-dhcp'
```

### 4. Migrations (production)

```bash
docker compose exec backend alembic upgrade head
```

> In development the app calls `Base.metadata.create_all` on startup as a convenience.

---

## Configuration Reference

### `backend/.env`

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/cookbook.db` | SQLAlchemy connection string |
| `SECRET_KEY` | — **required** | JWT signing key (hex string) |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Refresh token lifetime |
| `ENCRYPTION_KEY` | — **required** | Fernet key for GitHub PAT encryption |

### `.env` (root — Docker Compose only)

| Variable | Default | Description |
|---|---|---|
| `APP_PORT` | `80` | Host port when using port-mapping mode |

---

## API Overview

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Create account → returns tokens |
| `POST` | `/api/v1/auth/login` | Authenticate → returns tokens |
| `POST` | `/api/v1/auth/refresh` | Refresh access token |
| `GET` | `/api/v1/users/me` | Current user profile |
| `PATCH` | `/api/v1/users/me` | Update profile (GitHub token, tweak %, email) |
| `GET` | `/api/v1/recipes/` | List own recipes (search, category, tag filters) |
| `POST` | `/api/v1/recipes/` | Create recipe |
| `GET` | `/api/v1/recipes/shared` | Browse shared recipes from other users |
| `GET` | `/api/v1/recipes/{id}` | Recipe detail (draft + versions) |
| `PATCH` | `/api/v1/recipes/{id}` | Update recipe meta (shared flag) |
| `DELETE` | `/api/v1/recipes/{id}` | Soft-delete recipe |
| `PATCH` | `/api/v1/recipes/{id}/draft` | Save draft changes |
| `POST` | `/api/v1/recipes/{id}/versions` | Commit version (git commit + async push) |
| `GET` | `/api/v1/recipes/{id}/versions/{n}` | Get specific version |
| `PATCH` | `/api/v1/recipes/{id}/versions/{n}/rating` | Rate a version (1–5) |
| `GET` | `/api/v1/recipes/{id}/diff?v1=n&v2=m` | Structured diff between two versions |
| `POST` | `/api/v1/recipes/{id}/fork` | Fork shared recipe with attribution |
| `GET` | `/api/v1/categories/` | List own categories |
| `GET` | `/api/v1/tags/` | List own tags |
| `GET` | `/health` | Health check |

Interactive docs available at `http://<host>:8000/docs` (backend port).

---

## Data Model (summary)

```
User
 └── Recipe (soft-deletable, slug per owner)
      ├── RecipeDraft        (one active draft, JSON content)
      ├── RecipeVersion[]    (immutable, numbered, rated, git commit hash)
      ├── Category[]         (M2M, user-scoped)
      └── Tag[]              (M2M, user-scoped)
```

Recipe content (stored as JSON in DB, serialised as YAML in git):
`title · description · servings · prep_time · cook_time · ingredients[] · preparations[] · steps[] · categories[] · tags[] · notes · photos[]`

All quantities use **metric units** (g, ml, °C, cm).

---

## Development

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # fill in SECRET_KEY and ENCRYPTION_KEY
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # Vite dev server on http://localhost:5173
```

The Vite dev server proxies `/api/*` to `http://localhost:8000` (configure in `vite.config.ts` if needed).

### Alembic — create a new migration

```bash
cd backend
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

---

## Roadmap

Items from `SPECIFICATIONS.md` and architectural notes for future development:

### Near-term
- [ ] **Photo uploads** — currently `photos` is a list of URLs; add multipart upload endpoint and local/S3 storage
- [ ] **Push status UI** — surface `push_status` (pending / pushed / failed) per version in the frontend so users know if GitHub sync succeeded
- [ ] **Alembic auto-run** — replace `create_all` in `main.py` with `alembic upgrade head` on container startup (add to Dockerfile `CMD` or an entrypoint script)
- [ ] **CORS hardening** — replace wildcard localhost origins with a configurable `ALLOWED_ORIGINS` env var

### Medium-term
- [ ] **Meal planner** — assign recipes to days of the week (weekly view)
- [ ] **Shopping list generator** — aggregate ingredients across a meal plan with unit consolidation
- [ ] **Recipe import from URL** — scrape recipe sites (schema.org/Recipe) into draft state
- [ ] **Nutritional information** — per-ingredient lookup + per-recipe totals

### Architecture / Infrastructure
- [ ] **PostgreSQL support** — `DATABASE_URL` already supports it; add a `db` service to compose and document migration path
- [ ] **Gitea / self-hosted git** — currently GitHub-only; abstract the remote URL to support any git remote
- [ ] **Background task queue** — replace FastAPI `BackgroundTasks` with Celery + Redis for more robust async GitHub push with retries
- [ ] **Rate limiting** — add per-user request rate limiting on auth endpoints
- [ ] **Admin panel** — user management (deactivate accounts, view usage) for the NAS owner

---

## License

Private / personal project.
