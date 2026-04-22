from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Any

class CardContent(BaseModel):
    name: str
    description: Union[str, int]

class CardsBatchResponse(BaseModel):
    cards: List[CardContent]


# Полный ответ от нейронки (тот самый JSON)
class CharacterDescriptionResponse(BaseModel):
    biology: CardContent
    appearance: CardContent
    health: CardContent
    job: CardContent
    hobby: CardContent
    fact: CardContent
    phobia: CardContent
    inventory_1: CardContent
    inventory_2: CardContent
    ability_1: CardContent
    ability_2: CardContent


# Расширенные модели под твой словарь
class Biology(BaseModel):
    gender: str
    old: int
    race: str

class Appearance(BaseModel):
    appearance: str
    is_nice: str
    mass: int
    height: int

class Health(BaseModel):
    heal: str
    is_appearance: str

class Job(BaseModel):
    job: str
    is_nice: str
    skill: int

class Hobby(BaseModel):
    hobby: str
    is_nice: str
    is_job: str

class Fact(BaseModel):
    is_positive: str
    is_inexpected: str
    chaos: str

class Phobia(BaseModel):
    phobia: str
    is_nice: str

class Inventory(BaseModel):
    inventory: str
    is_job: str
    is_nice: str

class Ability(BaseModel):
    ability_name: str = Field(alias="ability name") # Обработка пробела в ключе
    is_chaotic: str

class GameGenerationResponse(BaseModel):
    disaster_description: str
    bunker_features: str