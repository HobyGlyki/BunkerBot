from fastapi import FastAPI, Form, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
import os
import json


from app.services.new_card import generate_full_character
from app.services.new_game import generate_game
from app.services.action_resolver import resolve_ability

from app.ai.parser import parse_ai_response
from app.ai.service import main1
from app.ai.new_game_ai import generate_disaster_ai

from app.DB.database import SessionLocal
from app.DB.models import Card, GameSession, GameStatus, Player, ActionEnum, CardType
from app.DB.crud import (get_card, join_player_to_game, get_players_in_game, get_player_cards,
                         distribute_cards_to_all, leave_player_from_game, get_players_count,
                         get_random_bunker_items)    
from app.DB.init_db import seed_inventory

import asyncio

x=0

app = FastAPI()
templates = Jinja2Templates(directory="frontend")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/games/{game_id}/join")
async def join_game(game_id: int, tg_id: int, name: str, db: Session = Depends(get_db)):
    player = join_player_to_game(db, game_id, tg_id, name)
    count = get_players_count(db, game_id)
    return {"status": "joined", "player_id": player.id, "current_players": count}

@app.get("/games/{game_id}/start")
async def start_game(game_id: int, db: Session = Depends(get_db)):
    
    players = get_players_in_game(db, game_id)
    
    if len(players) > x:  # Твой порог X
        # 1. Меняем статус
        game = db.query(GameSession).filter(GameSession.id == game_id).first()
        game.status = GameStatus.IN_PROGRESS
        
        # 2. Раздаем карты
        distribute_cards_to_all(db, game_id)
        db.commit()
        db.close()
        return {"status": "started", "players_count": len(players)}
    
    db.close()
    return {"status": "error", "message": "Недостаточно игроков"}

@app.get("/create_game")
async def create_game(db: Session = Depends(get_db)):
    # 1. Получаем тех. данные (цифры)
    tech_data = generate_game()
    
    # 2. Берем реальные предметы и еду из базы для контекста
    # Допустим, мы берем 3 случайных предмета из таблицы Cards
    real_items = get_random_bunker_items(db, count=3)
    tech_data["bunker_inventory"] = ", ".join(real_items) if real_items else "Пустые полки"

    # 3. Генерируем текст через ИИ
    ai_data = await generate_disaster_ai(tech_data)
    
    # Исправляем KeyError: проверяем ключи, которые мог вернуть ИИ
    food_text = ai_data.get("food_description") or ai_data.get("food_detailed") or "Еда отсутствует."
    bunker_text = ai_data.get("bunker_features") or ai_data.get("bunker_detailed") or "Стены из бетона."
    bunker_capacity = tech_data['bunker_capacity']

    new_game = GameSession(
        status=GameStatus.WAITING,
        disaster_description=ai_data.get("disaster_description", "Мир погиб молча."),
        bunker_capacity=tech_data["bunker_capacity"],
        bunker_years=tech_data["bunker_years"],
        bunker_features_json={
            "area": tech_data["bunker_area"],
            "population_left": tech_data["human_left"],
            "eat_years": tech_data["eat_count"],
            "inventory": tech_data["bunker_inventory"],
            "food_detailed": food_text,
            "bunker_detailed": bunker_text
        }
    )

    db.add(new_game)
    db.commit()
    db.refresh(new_game)
    
    return {
        "game_id": new_game.id,
        "disaster": new_game.disaster_description,
        "food": food_text,
        "bunker": bunker_text,
        "stats": new_game.bunker_features_json,
        'bunker_capacity': bunker_capacity
    }

@app.get("/player/exit")
async def player_exit(tg_id: int, db: Session = Depends(get_db)):
    leave_player_from_game(db, tg_id)
    db.close()
    return {"status": "exited"}

@app.get("/initgame")
async def new():
    seed_inventory()

@app.get("/new_cards")
async def index():
    strs = generate_full_character()
    new_card = await main1(strs)
    # json_obj = parse_ai_response(new_card[0])
    return new_card, strs


@app.get("/cards")
async def get_all_cards(db: Session = Depends(get_db)):
    """
    Достает все карточки из базы данных и возвращает их списком.
    """
    # Запрашиваем все записи из таблицы cards
    cards = get_card(db)
    
    # Возвращаем общее количество и сами карточки
    return {
        "total_cards_in_db": len(cards),
        "cards": cards
    }

@app.get("/playerinfo")
async def playerinfo(tg_id: int, db: Session = Depends(get_db)):
    print(tg_id)
    return get_player_cards(db, tg_id)

@app.get("/next_turn")
def next_turn():
        pass

@app.get("/games/{game_id}/use_ability")
async def use_card(
    actor_tg_id: int, 
    ability_card_id: int, 
    target_tg_id: int, 
    target_card_id: int = None, # Делаем None, так как для REVIVE или GIFT конкретная карта цели может быть не нужна
    actor_swap_card_id: int = None, # Нужно для SWAP (какую свою карту отдает актор)
    db: Session = Depends(get_db)
):
    ability_card = db.query(Card).filter(Card.id == ability_card_id).first()
    target_card = db.query(Card).filter(Card.id == target_card_id).first()
    actor_player = db.query(Player).filter(Player.tg_user_id == actor_tg_id).first()
    target_player = db.query(Player).filter(Player.tg_user_id == target_tg_id).first()

    # Базовые проверки
    if not ability_card or not target_card:
        return {"status": "error", "message": "Карта не найдена"}
    if ability_card.is_used:
        return {"status": "error", "message": "Эта способность уже была использована"}

    # 2. Бросаем кубики

    outcome, roll = resolve_ability(ability_card, target_card)

    # 1. МЕХАНИЧЕСКИЕ ДЕЙСТВИЯ (Меняем связи в БД без участия ИИ)
    if outcome == "success":
        
        if ability_card.interaction_type == ActionEnum.SPIOL:
            # Вор забирает карту себе
            target_card.player_id = actor_player.id

        elif ability_card.interaction_type == ActionEnum.REVEAL:
            # Карта становится видимой для всех
            target_card.is_revealed = True

        elif ability_card.interaction_type == ActionEnum.REVIVE:
            # Воскрешение (в models.py у тебя есть поле is_dead)
            target_player.is_dead = False

        elif ability_card.interaction_type == ActionEnum.SWAP_TRAIT:
            # Обмен. Нам нужна карта, которую актор отдает взамен
            if actor_swap_card_id:
                actor_card = db.query(Card).filter(Card.id == actor_swap_card_id).first()
                if actor_card:
                    # Меняем владельцев местами
                    target_card.player_id, actor_card.player_id = actor_card.player_id, target_card.player_id

        elif ability_card.interaction_type == ActionEnum.GIFT:
            # Ищем случайную свободную карту инвентаря в БД (которая никому не принадлежит)
            random_inventory_card = db.query(Card).filter(
                Card.type == CardType.INVENTORY,
                Card.player_id.is_(None) # Карта лежит в "колоде", а не у игрока
            ).order_by(func.random()).first()
            random_inventory_card.player_id = actor_player.id
                # Если хочешь, можешь добавить пометку, что это был подарок
        elif ability_card.interaction_type == ActionEnum.CHANGE_GENDER:
            pass
        elif ability_card.interaction_type == ActionEnum.SPAWN:
            pass

    ability_card.is_used = True
    db.commit()

    # 2. РП ДЕЙСТВИЯ (Работает ИИ)
    # Если это изменение состояния, мы собираем промпт и ждем ответ от нейросети
    rp_actions = [ActionEnum.HEAL, ActionEnum.SPOIL]
    
    if ability_card.interaction_type in rp_actions:
        ai_context = {
            "action_type": ability_card.interaction_type.value,
            "actor_name": actor_player.name,
            "target_name": target_player.name,
            "target_card_name": target_card.name if target_card else "Биология",
            "target_card_desc": target_card.description if target_card else "",
            "outcome": outcome, 
            "roll": roll
        }
        
        # Тут ты вызовешь свой ИИ
        # ai_result = await action_ai.generate_action_outcome(ai_context)
        
        # Перезаписываем текст карточки тем, что придумал ИИ
        # target_card.description = ai_result["new_description"]
        # db.commit()
        
        # Для РП-действий возвращаем ИИ-описание на фронтенд
        # narrative = ai_result["narrative"]
    else:
        # Для механических действий ИИ не нужен, генерируем простое системное сообщение
        narrative = f"Действие {ability_card.interaction_type.value} завершилось со статусом: {outcome}."

    return {
        "status": "ok", 
        "outcome": outcome, 
        "roll": roll, 
        "narrative": narrative
    }