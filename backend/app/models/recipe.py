import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Enum as SAEnum, ForeignKey,
    Integer, JSON, String, Table, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# ── Association tables ────────────────────────────────────────────────────────

recipe_categories = Table(
    "recipe_categories",
    Base.metadata,
    Column("recipe_id", Integer, ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)

recipe_tags = Table(
    "recipe_tags",
    Base.metadata,
    Column("recipe_id", Integer, ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


# ── Enums ─────────────────────────────────────────────────────────────────────

class PushStatus(str, enum.Enum):
    pending = "pending"
    pushed = "pushed"
    failed = "failed"


# ── Models ────────────────────────────────────────────────────────────────────

class Recipe(Base):
    __tablename__ = "recipes"
    __table_args__ = (
        UniqueConstraint("owner_id", "slug", name="uq_recipe_owner_slug"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    slug: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    is_shared: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # True when a RecipeDraft exists for this recipe
    has_draft: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Fork attribution
    forked_from_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("recipes.id", ondelete="SET NULL"), nullable=True
    )
    forked_from_attribution: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    owner: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User", back_populates="recipes", foreign_keys=[owner_id], lazy="selectin"
    )
    versions: Mapped[list["RecipeVersion"]] = relationship(
        "RecipeVersion", back_populates="recipe", order_by="RecipeVersion.version_number"
    )
    draft: Mapped["RecipeDraft | None"] = relationship(
        "RecipeDraft", back_populates="recipe", uselist=False
    )
    categories: Mapped[list["Category"]] = relationship(
        "Category", secondary=recipe_categories, back_populates="recipes"
    )
    tags: Mapped[list["Tag"]] = relationship(
        "Tag", secondary=recipe_tags, back_populates="recipes"
    )


class RecipeVersion(Base):
    """Immutable snapshot of a recipe at the time of a 'Save Version' action."""

    __tablename__ = "recipe_versions"
    __table_args__ = (
        UniqueConstraint("recipe_id", "version_number", name="uq_version_recipe_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recipe_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)  # 1–5, set after cooking

    # Full recipe content as JSON (mirrors the YAML structure)
    content: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Git integration
    commit_hash: Mapped[str | None] = mapped_column(String(40), nullable=True)
    push_status: Mapped[PushStatus] = mapped_column(
        SAEnum(PushStatus), default=PushStatus.pending, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    recipe: Mapped["Recipe"] = relationship("Recipe", back_populates="versions")


class RecipeDraft(Base):
    """Mutable draft state for a recipe — one per recipe, persists across sessions."""

    __tablename__ = "recipe_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recipe_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("recipes.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    recipe: Mapped["Recipe"] = relationship("Recipe", back_populates="draft")


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_category_owner_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    recipes: Mapped[list["Recipe"]] = relationship(
        "Recipe", secondary=recipe_categories, back_populates="categories"
    )


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_tag_owner_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    recipes: Mapped[list["Recipe"]] = relationship(
        "Recipe", secondary=recipe_tags, back_populates="tags"
    )
