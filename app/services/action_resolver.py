import random
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from app.DB.models import Card, Player, ActionEnum, CardType

def resolve_ability(ability_card: Card, target_card: Card):
    """Бросает кубик для вероятностных событий."""
    chance = ability_card.base_success_chance or 100 
    roll = random.randint(1, 100)
    is_success = roll <= chance
    
    outcome_status = "success" if is_success else "reversed_effect"
    return outcome_status, roll


def execute_ability_mechanics(
    db: Session, 
    ability_card: Card, 
    actor_player: Player, 
    target_player: Player = None, 
    target_card: Card = None, 
    actor_swap_card_id: int = None
):
    """Выполняет изменения в БД в зависимости от типа способности."""
    
    if ability_card.interaction_type == ActionEnum.SPOIL:
        if target_card and target_card.type == CardType.INVENTORY:
            actor_inv = db.query(Card).filter(
                Card.player_id == actor_player.id, 
                Card.type == CardType.INVENTORY
            ).first()
            if actor_inv:
                actor_inv.name = f"{actor_inv.name}, {target_card.name}"
                target_card.name = "Пусто (Украдено)"
                target_card.description = "Этот предмет был украден."
            else:
                return {"error": "У вас нет инвентаря, куда можно положить предмет"}
        else:
            return {"error": "Красть можно только карты инвентаря"}

    elif ability_card.interaction_type == ActionEnum.GIFT:
        random_item = db.query(Card).filter(
            Card.type == CardType.INVENTORY,
            Card.player_id.is_(None)
        ).order_by(func.random()).first()
        
        if random_item:
            actor_inv = db.query(Card).filter(
                Card.player_id == actor_player.id, 
                Card.type == CardType.INVENTORY
            ).first()
            if actor_inv:
                actor_inv.name = f"{actor_inv.name}, {random_item.name}"
                db.delete(random_item) 
            else:
                random_item.player_id = actor_player.id

    elif ability_card.interaction_type == ActionEnum.REVEAL:
        if target_card:
            target_card.is_revealed = True

    elif ability_card.interaction_type == ActionEnum.REVIVE:
        if target_player and target_player.is_dead:
            target_player.is_dead = False
        else:
            return {"error": "Этот игрок и так жив"}

    elif ability_card.interaction_type == ActionEnum.SWAP_TRAIT:
        if actor_swap_card_id and target_card:
            actor_card = db.query(Card).filter(Card.id == actor_swap_card_id).first()
            if actor_card:
                target_card.player_id, actor_card.player_id = actor_card.player_id, target_card.player_id

    elif ability_card.interaction_type == ActionEnum.CHANGE_GENDER:
        if target_player:
            bio_card = db.query(Card).filter(Card.player_id == target_player.id, Card.type == CardType.BIOLOGY).first()
            if bio_card and bio_card.description:
                if "мужчина" in bio_card.description.lower():
                    bio_card.description = bio_card.description.replace("мужчина", "женщина").replace("Мужчина", "Женщина")
                elif "женщина" in bio_card.description.lower():
                    bio_card.description = bio_card.description.replace("женщина", "мужчина").replace("Женщина", "Мужчина")

    elif ability_card.interaction_type == ActionEnum.SPAWN:
        if target_card:
            random_card_template = db.query(Card).filter(Card.type == target_card.type).order_by(func.random()).first()
            if random_card_template:
                target_card.name = random_card_template.name
                target_card.description = random_card_template.description
                target_card.power_level = random_card_template.power_level
                target_card.skill_level = random_card_template.skill_level
                target_card.chaos_level = random_card_template.chaos_level
                target_card.interaction_type = random_card_template.interaction_type
                target_card.is_revealed = False 

    return {"success": True}


def build_action_narrative(actor: Player, ability: Card, target: Player = None, target_card: Card = None, is_random: bool = False, roll: int = None, outcome: str = None):
    """Формирует текстовое сообщение о том, что произошло."""
    narrative = f"Игрок {actor.name} использовал способность «{ability.name}»"
    
    if target and target_card:
        narrative += f" на игроке {target.name} (карта: «{target_card.name}»)."
    elif target:
        narrative += f" на игроке {target.name}."
    else:
        narrative += "."

    if is_random:
        status_text = "Успешно!" if outcome == "success" else "Провал!"
        narrative += f" Результат: {status_text} (Выпало: {roll})."
        
    return narrative