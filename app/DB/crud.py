from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from . import models, schemas
from .models import CardType, Player, Card, GameSession, GameStatus, Vote, Player, Card, ActionEnum

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
        return ["пусто"]
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
    """Добавляет игрока в игру или переносит его из старой сессии в новую."""
    
    # 1. Ищем, существует ли уже игрок с таким Telegram ID в базе
    existing_player = db.query(Player).filter(Player.tg_user_id == tg_user_id).first()
    
    if existing_player:
        # Если он УЖЕ сидит в нужном лобби, ничего не делаем, просто возвращаем его
        if existing_player.game_id == game_id:
            return existing_player
            
        # Если он был в ДРУГОМ лобби, заставляем старую игру его забыть:
        # Переносим в новую игру и воскрешаем (если он умер в прошлой)
        existing_player.game_id = game_id
        existing_player.is_dead = False
        
        # Сжигаем все его старые карточки и голоса из прошлой игры!
        db.query(Card).filter(Card.player_id == existing_player.id).delete()
        db.query(Vote).filter(Vote.voter_id == existing_player.id).delete()
        
        db.commit()
        db.refresh(existing_player)
        return existing_player

    # 2. Если игрока вообще не было в базе, создаем его с нуля
    new_player = Player(
        game_id=game_id, 
        tg_user_id=tg_user_id, 
        name=name,
        is_dead=False
    )
    db.add(new_player)
    db.commit()
    db.refresh(new_player)
    return new_player

def distribute_cards_to_all(db: Session, game_id: int):
    """Раздает каждому игроку по 1 карте каждого типа из базы."""
    players = get_players_in_game(db, game_id)
    card_types = [
        models.CardType.PROFESSION, models.CardType.appearance, 
        models.CardType.HEALTH, models.CardType.INVENTORY, models.CardType.INVENTORY, 
        models.CardType.BIOLOGY, models.CardType.ABILITY, models.CardType.ABILITY, 
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


def reset_entire_database(db: Session):
    """Полное обнуление состояния игры для тестов"""
    try:
        # 1. Обнуляем все карты: убираем владельца и сбрасываем флаги
        db.query(Card).update({
            Card.player_id: None,
            Card.is_used: False,
            Card.is_revealed: False
        })
        
        # 2. Удаляем всех игроков (чтобы лобби стали пустыми)
        db.query(Player).delete()
        
        # 3. Сбрасываем игровые сессии в начальное состояние
        db.query(GameSession).update({
            GameSession.status: GameStatus.WAITING,
            GameSession.current_round: 1,
            GameSession.current_phase: "narrative",
            GameSession.finale_text: None
        })
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Ошибка при сбросе базы: {e}")
        return False
    


def cast_vote(db: Session, game_id: int, voter_id: int, target_id: int = None):
    """Регистрирует или обновляет голос игрока."""
    # Проверяем, есть ли у игрока активная способность "Двойной голос" (ID 9)
    # Ищем среди неиспользованных карт игрока
    double_vote_card = db.query(Card).filter(
        Card.player_id == voter_id,
        Card.interaction_type == "revive", # В твоем AbilityType это 9 (проверь соответствие в Enum)
        Card.is_used == False
    ).first()
    
    weight = 2 if double_vote_card else 1

    # Проверяем, голосовал ли уже этот игрок
    existing_vote = db.query(Vote).filter(Vote.game_id == game_id, Vote.voter_id == voter_id).first()
    
    if existing_vote:
        existing_vote.target_id = target_id
        existing_vote.weight = weight
    else:
        new_vote = Vote(game_id=game_id, voter_id=voter_id, target_id=target_id, weight=weight)
        db.add(new_vote)
    
    db.commit()

def get_voting_results(db: Session, game_id: int):
    """Считает голоса и возвращает ID игрока на вылет."""
    # Считаем сумму весов голосов за каждого target_id (исключая None)
    results = db.query(
        Vote.target_id, 
        func.sum(Vote.weight).label('total_weight')
    ).filter(
        Vote.game_id == game_id, 
        Vote.target_id.isnot(None)
    ).group_by(Vote.target_id).order_by(func.sum(Vote.weight).desc()).all()

    if not results:
        return None # Никто не проголосовал или все "против никого"

    # Если есть ничья по максимальному количеству голосов
    max_votes = results[0].total_weight
    top_candidates = [r.target_id for r in results if r.total_weight == max_votes]
    
    if len(top_candidates) > 1:
        return "tie" # Ничья — обычно в Бункере это переголосование или никто не уходит
        
    return top_candidates[0]