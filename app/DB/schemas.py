from pydantic import BaseModel
from typing import Optional
from .models import CardType, ActionEnum

class CardCreate(BaseModel):
    type: CardType
    name: str
    description: str
    power_level: int = 0
    skill_level: int = 0
    chaos_level: int = 0
    interaction_type: Optional[ActionEnum] = None
    base_success_chance: Optional[int] = None