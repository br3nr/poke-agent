
from pydantic import BaseModel

class PokemonData(BaseModel):
    name: str
    types: list[str]
    baseStats: dict[str, int]
    abilities: list[str]
    weight: float

class MoveData(BaseModel):
    accuracy: int | None
    basePower: int | None
    category: str
    moveName: str
    pp: int
    flags: dict[str, bool]
    critRatio: int
    type: str
    desc: str
    shortDesc: str
    condition: dict | None = None
    priority: int = 0
    isZ: bool = False

class AbilityData(BaseModel):
    desc: str
    shortDesc: str
    flags: dict[str, bool]