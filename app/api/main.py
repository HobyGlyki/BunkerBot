from fastapi import FastAPI, Form, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os
import json


from app.services.new_card import generate_full_character
from app.services.new_game import generate_game

from app.ai.parser import parse_ai_response
from app.ai.service import main1
from app.ai.new_game_ai import generate_disaster_ai

from app.DB.database import SessionLocal
from app.DB.models import Card, GameSession, GameStatus
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

    
    db.add(new_game)
    db.commit()
    db.refresh(new_game)
    
    # Возвращаем данные для моментального просмотра на фронтенде
    return {
        "game_id": new_game.id,
        "disaster": new_game.disaster_description,
        "bunker": ai_data["bunker_features"],
        "stats": new_game.bunker_features_json
    }

@app.get("/player/exit")
async def player_exit(tg_id: int, db: Session = Depends(get_db)):
    leave_player_from_game(db, tg_id)
    db.close()
    return {"status": "exited"}

@app.get("/new_cards_deg")
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
    return get_player_cards(db, tg_id)
    
