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
    actor_swap_card_id: int = None,
    roll: int = 100 # <-- ВАЖНО: добавили кубик в аргументы!
):
    """Выполняет изменения в БД в зависимости от типа способности."""

    # === 1. ЗДОРОВЬЕ (ЛЕЧЕНИЕ И УРОН С КУБИКОМ) ===
    if ability_card.interaction_type == ActionEnum.HEAL:
        if target_card and target_card.type == CardType.HEALTH:
            # Извлекаем текущую тяжесть болезни (если вдруг пусто, то 0)
            current_severity = target_card.power_level or 0
            
            if roll >= 80:
                target_card.name = "Идеально здоров"
                target_card.description = "Степень тяжести: 0% (Полностью исцелен)"
                target_card.power_level = 0
            elif roll >= 60:
                heal_amount = roll - 10
                new_severity = max(0, current_severity - heal_amount)
                if new_severity == 0:
                    target_card.name = "Идеально здоров"
                    target_card.description = "Степень тяжести: 0% (Полностью исцелен)"
                else:
                    target_card.description = f"Степень тяжести: {new_severity}% (Стало лучше на {heal_amount}%)"
                target_card.power_level = new_severity
            elif roll >= 30:
                target_card.description += '(Ничего не произошло)'
            else:
                # Осложнение (увеличиваем тяжесть на выпавшее количество)
                new_severity = min(100, current_severity + roll)
                print(new_severity, current_severity)
                target_card.description = f"Степень тяжести: {new_severity}% (Осложнение на {roll}%)"
                if new_severity >= 100:
                    target_card.name = "Терминальная стадия (Смерть близка)"
                target_card.power_level = new_severity

    elif ability_card.interaction_type == ActionEnum.STEAL: # Урон (Обратная логика)
        if target_card and target_card.type == CardType.HEALTH:
            current_severity = target_card.power_level or 0
            
            if roll >= 80:
                # Успешный сильный урон
                damage_amount = roll - 40
                new_severity = min(100, current_severity + damage_amount)
                target_card.description = f"Степень тяжести: {new_severity}% (Состояние ухудшилось на {damage_amount}%)"
                target_card.power_level = new_severity
            elif roll >= 60:
                # Успешный средний урон
                damage_amount = roll - 50
                new_severity = min(100, current_severity + damage_amount)
                target_card.description = f"Степень тяжести: {new_severity}% (Состояние ухудшилось на {damage_amount}%)"
                target_card.power_level = new_severity
            elif roll >= 30:
                pass # Ничего не произошло
            else:
                # Случайно вылечил!
                heal_amount = roll + 10
                new_severity = max(0, current_severity - heal_amount)
                if new_severity == 0:
                    target_card.name = "Идеально здоров"
                    target_card.description = "Степень тяжести: 0% (Попытка покалечить случайно исцелила!)"
                else:
                    target_card.description = f"Степень тяжести: {new_severity}% (Случайно стало лучше на {heal_amount}%)"
                target_card.power_level = new_severity
    # === 2. ИНВЕНТАРЬ (КРАЖА И ПОДАРОК ЧЕРЕЗ ЗАПЯТУЮ) ===
    elif ability_card.interaction_type == ActionEnum.SPOIL:
        if target_card and target_card.type == CardType.INVENTORY:
            actor_inv = db.query(Card).filter(
                Card.player_id == actor_player.id, 
                Card.type == CardType.INVENTORY
            ).first()
            if actor_inv:
                # Прибавляем предмет
                actor_inv.name = f"{actor_inv.name}, {target_card.name}"
                # Опустошаем карту жертвы
                target_card.name = "Пусто"
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
            else:
                random_item.player_id = actor_player.id

    # === 3. ДРУГИЕ ДЕЙСТВИЯ ===
    elif ability_card.interaction_type == ActionEnum.SPAWN:
        if target_card:
            random_card_template = db.query(Card).filter(Card.type == target_card.type).order_by(func.random()).first()
            if random_card_template:
                # Мы не меняем ID, мы просто копируем внутрь все данные
                target_card.name = random_card_template.name
                target_card.description = random_card_template.description
                target_card.power_level = random_card_template.power_level
                target_card.skill_level = random_card_template.skill_level
                target_card.chaos_level = random_card_template.chaos_level
                target_card.interaction_type = random_card_template.interaction_type
                target_card.is_revealed = target_card.is_revealed

    elif ability_card.interaction_type == ActionEnum.CHANGE_GENDER:
        if target_player:
            bio_card = db.query(Card).filter(Card.player_id == target_player.id, Card.type == CardType.BIOLOGY).first()
            if bio_card and bio_card.description:
                if "мужчина" in bio_card.description.lower():
                    bio_card.description = bio_card.description.replace("мужчина", "женщина").replace("Мужчина", "Женщина")
                elif "женщина" in bio_card.description.lower():
                    bio_card.description = bio_card.description.replace("женщина", "мужчина").replace("Женщина", "Мужчина")

    elif ability_card.interaction_type == ActionEnum.REVEAL:
        if target_card:
            target_card.is_revealed = True

    elif ability_card.interaction_type == ActionEnum.REVIVE:
        if target_player and target_player.is_dead:
            target_player.is_dead = False
        else:
            return {"error": "Этот игрок и так жив"}

    elif ability_card.interaction_type == ActionEnum.SWAP_TRAIT:
        if target_card and not actor_player.id == target_player.id:
            # Ищем твою карту точно такого же типа, как та, на которую ты кликнул
            actor_card = db.query(Card).filter(
                Card.player_id == actor_player.id, 
                Card.type == target_card.type
            ).first()
            
            if actor_card:
                # Меняем владельцев местами (одна строчка магии Python)
                target_card.player_id, actor_card.player_id = actor_card.player_id, target_card.player_id
            else:
                # Защита от багов, если карты такого типа у тебя почему-то нет
                return {"error": f"У вас нет карты типа {target_card.type.value} для обмена!"}
        else:
            return {"error": "Вы должны кликнуть по карте, которую хотите обменять!"}

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