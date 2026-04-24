import random
from app.DB.models import Card, ActionEnum

def resolve_ability(ability_card: Card, target_card: Card):
    # Если шанс не указан или это кража/обмен (где 100%), считаем успехом
    chance = ability_card.base_success_chance or 100 
    
    roll = random.randint(1, 100)
    is_success = roll <= chance
    
    # Определяем, что именно произошло (для передачи в ИИ)
    outcome_status = "success" if is_success else "reversed_effect"
    
    return outcome_status, roll