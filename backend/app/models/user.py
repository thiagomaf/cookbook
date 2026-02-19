from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # GitHub integration — token is Fernet-encrypted before storage
    github_repo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    github_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Per-user config
    tweak_percentage: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    recipes: Mapped[list["Recipe"]] = relationship(  # type: ignore[name-defined]
        "Recipe",
        back_populates="owner",
        foreign_keys="Recipe.owner_id",
    )
