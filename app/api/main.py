from fastapi import FastAPI, Form, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse


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


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
x=0

app = FastAPI()
templates = Jinja2Templates(directory="frontend")
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "frontend", "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "frontend"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Подключаем папку со статикой (CSS, JS, картинки)
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Твой Jinja2 уже настроен: templates = Jinja2Templates(directory="frontend")

@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    """Главная страница"""
    # Явно указываем request и name
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/games_list", response_class=HTMLResponse)
async def games_page(request: Request, db: Session = Depends(get_db)):
    """Страница со списком всех игр"""
    games = db.query(GameSession).all()
    
    # Контекст передаем в аргумент context
    return templates.TemplateResponse(
        request=request, 
        name="games.html", 
        context={"games": games}
    )


# Добавь импорт Request, если его нет
from fastapi import Request

@app.get("/lobby/{game_id}", response_class=HTMLResponse)
async def lobby_page(request: Request, game_id: int, tg_id: int = 123, name: str = "Черрешня", db: Session = Depends(get_db)):
    """Страница ожидания начала игры"""
    # Автоматически добавляем игрока при входе по ссылке
    player = join_player_to_game(db, game_id, tg_id, name)
    game = db.query(GameSession).filter(GameSession.id == game_id).first()
    
    # Временная логика хоста: если tg_id == 123, то ты ведущий
    is_host = (tg_id == 123)
    
    return templates.TemplateResponse(
        request=request, 
        name="lobby.html", 
        context={
            "game": game, 
            "current_tg_id": tg_id, 
            "current_name": name,
            "is_host": is_host
        }
    )

@app.get("/lobby/{game_id}/players", response_class=HTMLResponse)
async def lobby_players_partial(request: Request, game_id: int, db: Session = Depends(get_db)):
    """HTMX-эндпоинт: возвращает только кусок HTML со списком игроков и статусом"""
    players = get_players_in_game(db, game_id)
    game = db.query(GameSession).filter(GameSession.id == game_id).first()
    
    return templates.TemplateResponse(
        request=request, 
        name="partials/player_list.html", 
        context={"players": players, "game": game}
    )

@app.get("/games/{game_id}/join") #/games/1/join?tg_id=123&name=Cherry
async def join_game(game_id: int, tg_id: int, name: str, db: Session = Depends(get_db)):
    player = join_player_to_game(db, game_id, tg_id, name)
    count = get_players_count(db, game_id)
    return {"status": "joined", "player_id": player.id, "current_players": count}

@app.get("/games/{game_id}/start", response_class=HTMLResponse)
async def start_game(game_id: int, db: Session = Depends(get_db)):
    game = db.query(GameSession).filter(GameSession.id == game_id).first()
    
    # Защита: если игра уже началась, просто кидаем на страницу игры
    if game.status == GameStatus.IN_PROGRESS:
        return f"<script>window.location.href = '/game/{game_id}/play';</script>"

    players = get_players_in_game(db, game_id)
    
    # Порог игроков (ставлю >= 1 для тестов, потом поменяешь)
    if len(players) >= x:  
        game.status = GameStatus.IN_PROGRESS
        distribute_cards_to_all(db, game_id)
        db.commit()
        # Возвращаем JS-скрипт. HTMX его выполнит, и хоста перекинет на новую страницу
        return f"<script>window.location.href = '/game/{game_id}/play';</script>"
    
    return "<p style='color: red;'>Недостаточно игроков!</p>"

@app.get("/game/{game_id}/play", response_class=HTMLResponse)
async def game_play_page(request: Request, game_id: int, tg_id: int = 123, db: Session = Depends(get_db)):
    game = db.query(GameSession).filter(GameSession.id == game_id).first()
    
    # Ищем всех игроков в этой игре
    all_players = db.query(Player).filter(Player.game_id == game_id).all()
    
    # ❗️ КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: Вручную достаем карты для каждого игрока ❗️
    for p in all_players:
        p.cards = db.query(Card).filter(Card.player_id == p.id).all()
        
    current_player = next((p for p in all_players if p.tg_user_id == tg_id), None)
    
    if not current_player:
        return "Вы не участвуете в этой игре"

    # Столбцы для таблицы
    table_columns = [
        "biology", 
        "appearance", 
        "health",       
        "profession", 
        "fact", 
        "hobby", 
        "phobia", 
        "inventory"
    ]

    return templates.TemplateResponse(
        request=request, 
        name="play.html", 
        context={
            "game": game,
            "players": all_players,
            "me": current_player,
            "is_host": (tg_id == 123),
            "columns": table_columns
        }
    )


@app.post("/game/{game_id}/next_phase")
async def next_phase(game_id: int, db: Session = Depends(get_db)):
    game = db.query(GameSession).filter(GameSession.id == game_id).first()
    # Простое переключение: из ожидания в фазу раскрытия (reveal)
    if game.current_phase == "narrative":
        game.current_phase = "reveal"
    db.commit()
    return {"status": "ok"}



@app.get("/create_game")
async def create_game(db: Session = Depends(get_db)):
    # 1. Получаем тех. данные (цифры)
    tech_data = generate_game(db)
    
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
    info = get_player_cards(db, tg_id)
    print(info)
    return info

@app.get("/next_turn")
def next_turn():
        pass


# Добавь эти импорты в начало main.py:
from app.services.action_resolver import resolve_ability, execute_ability_mechanics, build_action_narrative

@app.get("/games/{game_id}/use_ability") #http://127.0.0.1:8000/games/1/use_ability?actor_tg_id=1111&ability_card_id=5&target_tg_id=2222&target_card_id=12
async def use_card(
    actor_tg_id: int, 
    ability_card_id: int, 
    target_tg_id: int = None, # Сделал None на всякий случай
    target_card_id: int = None, 
    actor_swap_card_id: int = None, 
    db: Session = Depends(get_db)
):
    ability_card = db.query(Card).filter(Card.id == ability_card_id).first()
    actor_player = db.query(Player).filter(Player.tg_user_id == actor_tg_id).first()
    
    if not ability_card:
        return {"status": "error", "message": "Карта способности не найдена"}
    if ability_card.is_used:
        return {"status": "error", "message": "Эта способность уже была использована"}

    target_player = None
    if target_tg_id:
        target_player = db.query(Player).filter(Player.tg_user_id == target_tg_id).first()

    target_card = None
    if target_card_id:
        target_card = db.query(Card).filter(Card.id == target_card_id).first()

    # Проверка обязательной цели
    needs_target = [ActionEnum.STEAL, ActionEnum.SPOIL, ActionEnum.SPAWN, ActionEnum.REVEAL, ActionEnum.SWAP_TRAIT, ActionEnum.HEAL]
    if ability_card.interaction_type in needs_target and not target_card:
        return {"status": "error", "message": "Для этого действия необходимо выбрать карту цели"}

    # Бросок кубиков (только для HEAL и STEAL)
    rp_actions = [ActionEnum.HEAL, ActionEnum.STEAL]
    is_random = ability_card.interaction_type in rp_actions
    outcome = "success"
    roll = 100

    if is_random:
        outcome, roll = resolve_ability(ability_card, target_card)

    # Механика
    if outcome == "success":
        result = execute_ability_mechanics(
            db=db, 
            ability_card=ability_card, 
            actor_player=actor_player, 
            target_player=target_player, 
            target_card=target_card, 
            actor_swap_card_id=actor_swap_card_id
        )
        
        # Если механика вернула ошибку (например, воскрешение живого)
        if "error" in result:
            return {"status": "error", "message": result["error"]}

    ability_card.is_used = True
    db.commit()

    # Формируем текст
    narrative = build_action_narrative(
        actor=actor_player, 
        ability=ability_card, 
        target=target_player, 
        target_card=target_card, 
        is_random=is_random, 
        roll=roll, 
        outcome=outcome
    )

    return {
        "status": "ok", 
        "outcome": outcome, 
        "roll": roll, 
        "narrative": narrative
    }