# Cookbook

> A self-hosted, multi-user recipe manager with **version-controlled recipes**.
> Every saved change is an immutable version with a star rating — so you always know whether adding 10 % more salt was a good idea.

---

## Features

- **Draft → Version workflow** — edit freely in draft state; commit a version when you're happy
- **Star ratings per version** — rate after cooking, not before
- **Ingredient tweaking** — `+` / `-` buttons adjust quantities by a configurable step (default 10 %)
- **Side-by-side diff** — compare any two versions to see exactly what changed
- **GitHub integration** — each user connects their own repo; the app commits and pushes autonomously
- **Recipe sharing & forking** — share recipes with other users; fork with attribution
- **Categories & tags** — per-user organisation with full-text search
- **Multi-user** — JWT auth (access + refresh tokens), Argon2 password hashing
- **Self-hosted** — Docker on a NAS or any Linux host, with optional Cloudflare Tunnel for external access

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vue 3 + Vite + PrimeVue 4 (custom Aura preset — Cormorant + Plus Jakarta Sans, teal accent, light/dark) |
| State / HTTP | Pinia + Axios |
| Backend | FastAPI (Python 3.12) |
| ORM / DB | SQLAlchemy 2 + SQLite (swappable to PostgreSQL) |
| Migrations | Alembic |
| Auth | JWT (python-jose) + Argon2 (passlib) |
| Encryption | Fernet (GitHub PATs encrypted at rest) |
| Version Control | GitPython — per-user local repos pushed to GitHub |
| Container | Docker + Docker Compose |
| Reverse Proxy | Nginx (multi-stage build) |

---

## Project Structure

```
cookbook/
├── backend/
│   ├── app/
│   │   ├── api/v1/         # Route handlers (auth, users, recipes, categories, tags)
│   │   ├── core/           # Security helpers, git operations, diff engine
│   │   ├── crud/           # Database query layer
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic request / response schemas
│   │   ├── config.py       # Settings (pydantic-settings, reads .env)
│   │   ├── database.py     # Engine, session, Base, SQLite pragmas
│   │   └── main.py         # App entry, CORS, router registration
│   ├── alembic/            # DB migrations
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example        # ← copy to .env and fill in
├── frontend/
│   ├── src/
│   │   ├── api/            # Axios client with JWT refresh + typed API calls
│   │   ├── components/     # DiffViewer, IngredientRow, RecipeCard, …
│   │   ├── views/          # Login, Register, RecipeList, RecipeEditor, Profile, …
│   │   ├── stores/         # Pinia auth store
│   │   ├── router/         # Vue Router with auth guard
│   │   └── types/          # Shared TypeScript interfaces
│   ├── nginx.conf          # Proxies /api/* → backend; serves SPA
│   └── Dockerfile
├── data/                   # Runtime: SQLite DB + per-user git repos (gitignored)
├── docker-compose.yml
├── build.sh                # Rebuild images on the NAS after code changes
├── .env.example
├── SPECIFICATIONS.md       # Detailed product & architecture spec
└── .gitignore
```

---

## Deployment

### Prerequisites

- Docker + Docker Compose
- (Optional) QNAP Container Station or similar for UI-based management

### 1. Clone & configure

```bash
git clone <repo-url> cookbook && cd cookbook

cp .env.example .env                 # Docker Compose vars
cp backend/.env.example backend/.env # backend secrets — fill in both
```

Generate the required secrets:

```bash
# SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Paste the generated values into `backend/.env`.

### 2. Build & start

```bash
docker compose up -d --build
```

Or, to build tagged images first (useful if Container Station manages the stack):

```bash
bash build.sh               # builds cookbook-backend:latest + cookbook-frontend:latest
docker compose up -d
```

### 3. Networking

By default, both containers share the Compose-managed bridge network.
The frontend proxies `/api/*` to the backend internally — no host port mapping is needed unless you want to expose the app on the host.

**Option A — Container Station (QNAP):**
Attach a LAN network adapter to the frontend container via the Container Station UI.
The container gets a real LAN IP from the router's DHCP.

**Option B — macvlan (generic Linux):**
Uncomment the `networks` block at the bottom of `docker-compose.yml` and adjust the
`parent` interface and subnet to match your LAN.

**Option C — port mapping:**
Add `ports: ["${APP_PORT:-80}:80"]` to the frontend service and set `APP_PORT` in `.env`.

### 4. Migrations (production)

```bash
docker compose exec backend alembic upgrade head
```

> In development the app auto-creates tables on startup via `Base.metadata.create_all`.

---

## Configuration Reference

### `backend/.env`

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./data/cookbook.db` | SQLAlchemy connection string |
| `SECRET_KEY` | *(required)* | JWT signing key (hex string) |
| `ENCRYPTION_KEY` | *(required)* | Fernet key for GitHub PAT encryption |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Refresh token lifetime |

### `.env` (project root — Docker Compose only)

| Variable | Default | Description |
|---|---|---|
| `APP_PORT` | `80` | Host port (only used with port-mapping mode) |

---

## API Overview

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Create account |
| `POST` | `/api/v1/auth/login` | Authenticate |
| `POST` | `/api/v1/auth/refresh` | Refresh access token |
| `GET` | `/api/v1/users/me` | Current user profile |
| `PATCH` | `/api/v1/users/me` | Update profile (GitHub token, tweak %, email) |
| `GET` | `/api/v1/recipes/` | List own recipes (search, category/tag filters) |
| `POST` | `/api/v1/recipes/` | Create recipe |
| `GET` | `/api/v1/recipes/shared` | Browse shared recipes from other users |
| `GET` | `/api/v1/recipes/{id}` | Recipe detail (draft + versions) |
| `PATCH` | `/api/v1/recipes/{id}` | Update recipe meta (shared flag) |
| `DELETE` | `/api/v1/recipes/{id}` | Soft-delete recipe |
| `PATCH` | `/api/v1/recipes/{id}/draft` | Save draft |
| `POST` | `/api/v1/recipes/{id}/versions` | Commit version (git commit + async push) |
| `GET` | `/api/v1/recipes/{id}/versions/{n}` | Get specific version |
| `PATCH` | `/api/v1/recipes/{id}/versions/{n}/rating` | Rate a version (1-5) |
| `GET` | `/api/v1/recipes/{id}/diff?v1=n&v2=m` | Structured diff between two versions |
| `POST` | `/api/v1/recipes/{id}/fork` | Fork shared recipe with attribution |
| `GET` | `/api/v1/categories/` | List own categories |
| `GET` | `/api/v1/tags/` | List own tags |
| `GET` | `/health` | Health check |

Interactive API docs: `http://<host>:8000/docs` (Swagger UI).

---

## Data Model

```
User
 └── Recipe  (soft-deletable, slug unique per owner)
      ├── RecipeDraft        one mutable draft (JSON content)
      ├── RecipeVersion[]    immutable, numbered, rated, linked to git commit
      ├── Category[]         M2M, user-scoped
      └── Tag[]              M2M, user-scoped
```

Recipe content (JSON in DB, YAML in git):
`title · description · servings · prep_time · cook_time · ingredients[] · preparations[] · steps[] · categories[] · tags[] · notes · photos[]`

All quantities use **metric units** (g, ml, cm, °C).

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
npm run dev   # Vite dev server → http://localhost:5173
```

Vite proxies `/api/*` to `http://localhost:8000` (see `vite.config.ts`).

### New Alembic migration

```bash
cd backend
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

---

## Roadmap

### Near-term
- [ ] **Frontend redesign foundation** — custom PrimeVue preset, Cormorant + Plus Jakarta Sans typography, light/dark mode toggle, mobile bottom tab bar ([design doc](docs/plans/2026-02-20-frontend-redesign-design.md))
- [ ] Photo uploads — multipart endpoint + local/S3 storage
- [ ] Push status UI — surface git push status (pending / pushed / failed) per version
- [ ] Alembic on startup — replace `create_all` with `alembic upgrade head` in the entrypoint
- [ ] Configurable CORS origins via `ALLOWED_ORIGINS` env var

### Medium-term
- [ ] Meal planner — assign recipes to days of the week
- [ ] Shopping list generator — aggregate ingredients from a meal plan
- [ ] Recipe import from URL — scrape schema.org/Recipe into draft
- [ ] Nutritional information per recipe

### Infrastructure
- [ ] PostgreSQL support — add `db` service to compose; document migration
- [ ] Gitea / self-hosted git — abstract the remote to support any git server
- [ ] Background task queue — Celery + Redis for reliable async GitHub push
- [ ] Rate limiting on auth endpoints
- [ ] Admin panel for the instance owner

---

## License

Private project.
