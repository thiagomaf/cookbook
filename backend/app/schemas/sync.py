from pydantic import BaseModel


class SyncFailedItem(BaseModel):
    file: str
    error: str


class SyncResultOut(BaseModel):
    imported: list[str]
    skipped: list[str]
    failed: list[SyncFailedItem]
    error: str | None = None
