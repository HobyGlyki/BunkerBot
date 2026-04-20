from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from . import models, schemas

# --- СОЗДАНИЕ ---

def create_card(db: Session, card_in: schemas.CardCreate):
    """
    Создает одну новую карточку в общей колоде (без привязки к игроку).
    """
    # model_dump() переводит Pydantic схему в словарь
    db_card = models.Card(**card_in.model_dump()) 
    
    db.add(db_card)
    db.commit()
    db.refresh(db_card) # Обновляем объект, чтобы получить его сгенерированный ID
    
    return db_card


# --- ЧТЕНИЕ И ОБНОВЛЕНИЕ (РАЗДАЧА) ---

def assign_random_card_to_player(db: Session, player_id: int, card_type: models.CardType):
    """
    Находит случайную свободную карточку заданного типа и присваивает её игроку.
    """
    # 1. Ищем случайную свободную карту нужного типа (где player_id == None)
    free_card = db.query(models.Card).filter(
        models.Card.type == card_type,
        models.Card.player_id == None
    ).order_by(func.random()).first()

    # Если свободных карт такого типа не осталось
    if not free_card:
        return None 

    # 2. Присваиваем карту игроку
    free_card.player_id = player_id
    db.commit()
    db.refresh(free_card)
    
    return free_card

# Опционально: функция для получения всех карт игрока
def get_player_cards(db: Session, player_id: int):
    """
    Возвращает весь инвентарь (все карточки) конкретного игрока.
    """
    return db.query(models.Card).filter(models.Card.player_id == player_id).all()

def get_card(db: Session):
    return db.query(models.Card).all()
