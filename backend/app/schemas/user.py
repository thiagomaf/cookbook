import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_-]{3,50}$", v):
            raise ValueError(
                "Username must be 3–50 characters: letters, numbers, underscores, or hyphens"
            )
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    # Plaintext token — will be encrypted before storage; never returned in responses
    github_token: Optional[str] = None
    github_repo_url: Optional[str] = None
    tweak_percentage: Optional[float] = None

    @field_validator("tweak_percentage")
    @classmethod
    def validate_tweak(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (1.0 <= v <= 50.0):
            raise ValueError("Tweak percentage must be between 1 and 50")
        return v

    @field_validator("github_repo_url")
    @classmethod
    def validate_repo_url(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v != "" and not re.match(
            r"^https://github\.com/[\w.-]+/[\w.-]+(\.git)?$", v
        ):
            raise ValueError("Must be a valid GitHub HTTPS repository URL")
        return v


class UserPublic(BaseModel):
    """Safe user representation — never includes password or raw token."""

    id: int
    username: str
    email: str
    github_repo_url: Optional[str]
    tweak_percentage: float
    has_github_token: bool  # True if a token is stored; actual token is never returned
    created_at: datetime

    model_config = {"from_attributes": True}
