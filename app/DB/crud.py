from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from . import models, schemas
from .models import CardType

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
def get_player_cards(db: Session, tg_id: int):
    """
    Возвращает весь инвентарь (все карточки) конкретного игрока.
    """    
    player = db.query(models.Player).filter(models.Player.tg_user_id == tg_id).first()
    if not player:
        return []
    player_id = player.id
    print(player_id)
    
    return db.query(models.Card).filter(models.Card.player_id == player_id).all()

def get_players_in_game(db: Session, game_id: int):
    """Возвращает список всех игроков в лобби."""
    return db.query(models.Player).filter(models.Player.game_id == game_id).all()   

def get_card(db: Session):
    return db.query(models.Card).all()


def get_players_count(db: Session, game_id: int) -> int:
    """Возвращает количество игроков в лобби."""
    return db.query(models.Player).filter(models.Player.game_id == game_id).count()

def join_player_to_game(db: Session, game_id: int, tg_user_id: int, name: str):
    """Добавляет игрока в лобби, если он еще не там."""
    db_player = db.query(models.Player).filter(
        models.Player.game_id == game_id, 
        models.Player.tg_user_id == tg_user_id
    ).first()
    
    if not db_player:
        db_player = models.Player(game_id=game_id, tg_user_id=tg_user_id, name=name)
        db.add(db_player)
        db.commit()
        db.refresh(db_player)
    return db_player

def distribute_cards_to_all(db: Session, game_id: int):
    """Раздает каждому игроку по 1 карте каждого типа из базы."""
    players = get_players_in_game(db, game_id)
    card_types = [
        models.CardType.PROFESSION, models.CardType.appearance, 
        models.CardType.HEALTH, models.CardType.INVENTORY, 
        models.CardType.BIOLOGY, models.CardType.ABILITY, 
        models.CardType.PHOBIA, models.CardType.HOBBY, models.CardType.FACT
    ]

    for player in players:
        for c_type in card_types:
            # Используем твою логику assign_random_card_to_player
            assign_random_card_to_player(db, player.id, c_type)

def leave_player_from_game(db: Session, tg_user_id: int):
    """Удаляет игрока из текущей сессии (выход)."""
    player = db.query(models.Player).filter(models.Player.tg_user_id == tg_user_id).first()
    if player:
        db.delete(player)
        db.commit()
    return True

def get_random_bunker_items(db: Session, count: int = 3):
    """Берет случайные предметы инвентаря из тех, что уже есть в базе."""
    items = db.query(models.Card).filter(
        models.Card.type == models.CardType.INVENTORY,
        models.Card.player_id == None
    ).order_by(func.random()).limit(count).all()
    
    return [i.name for i in items]

def get_any_waiting_game(db: Session):
    """Находит одну случайную игру, которая еще не началась."""
    return db.query(models.GameSession).filter(
        models.GameSession.status == models.GameStatus.WAITING
    ).order_by(func.random()).first()