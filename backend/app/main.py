from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
import app.models  # noqa: F401 — registers all models with Base before create_all
from app.api.v1 import auth, categories, recipes, sync, tags, users

# In production, run: alembic upgrade head
# During development, auto-create tables for convenience
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Cookbook API",
    version="0.1.0",
    description="Version-controlled recipe management",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(recipes.router, prefix="/api/v1/recipes", tags=["recipes"])
app.include_router(categories.router, prefix="/api/v1/categories", tags=["categories"])
app.include_router(tags.router, prefix="/api/v1/tags", tags=["tags"])
app.include_router(sync.router, prefix="/api/v1/sync", tags=["sync"])


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
