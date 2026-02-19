from pydantic import BaseModel
from app.schemas.recipe import Ingredient


class IngredientChange(BaseModel):
    name: str
    from_: Ingredient
    to: Ingredient

    model_config = {"populate_by_name": True}


class IngredientDiff(BaseModel):
    added: list[Ingredient] = []
    removed: list[Ingredient] = []
    changed: list[IngredientChange] = []


class StepDiff(BaseModel):
    added: list[str] = []
    removed: list[str] = []


class MetadataChange(BaseModel):
    from_: object = None
    to: object = None

    model_config = {"populate_by_name": True}


class DiffOut(BaseModel):
    recipe_id: int
    v1: int
    v2: int
    metadata_changes: dict[str, dict] = {}
    ingredients: IngredientDiff = IngredientDiff()
    steps: StepDiff = StepDiff()
    preparations: StepDiff = StepDiff()
