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
from app.DB.models import Card, GameSession, GameStatus, Player, ActionEnum, CardType, Vote
from app.DB.crud import (get_card, join_player_to_game, get_players_in_game, get_player_cards,
                         distribute_cards_to_all, leave_player_from_game, get_players_count,
                         get_random_bunker_items, reset_entire_database, get_voting_results, cast_vote)    
from app.DB.init_db import seed_inventory
from app.DB.init_db2 import seed_extra_cards, seed_biology_and_appearance

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
async def lobby_players_partial(request: Request, game_id: int, tg_id: int = 123, db: Session = Depends(get_db)):
    """HTMX-эндпоинт: возвращает только кусок HTML со списком игроков и статусом"""
    players = get_players_in_game(db, game_id)
    game = db.query(GameSession).filter(GameSession.id == game_id).first()
    
    # ПЕРЕДАЕМ current_tg_id В ШАБЛОН, ЧТОБЫ ОН НЕ ПОТЕРЯЛСЯ
    return templates.TemplateResponse(
        request=request, 
        name="partials/player_list.html", 
        context={"players": players, "game": game, "current_tg_id": tg_id}
    )

@app.get("/games/{game_id}/start", response_class=HTMLResponse)
async def start_game(game_id: int, tg_id: int = 123, db: Session = Depends(get_db)):
    game = db.query(GameSession).filter(GameSession.id == game_id).first()
    
    # Защита: если игра уже началась
    if game.status == GameStatus.IN_PROGRESS:
        # ВАЖНО: Добавляем ?tg_id={tg_id} в ссылку редиректа!
        return f"<script>window.location.href = '/game/{game_id}/play?tg_id={tg_id}';</script>"

    players = get_players_in_game(db, game_id)
    
    # Порог игроков (ставлю >= 1 для тестов, потом поменяешь)
    if len(players) >= x:  
        game.status = GameStatus.IN_PROGRESS
        distribute_cards_to_all(db, game_id)
        db.commit()
        # ВАЖНО: Добавляем ?tg_id={tg_id} в ссылку редиректа!
        return f"<script>window.location.href = '/game/{game_id}/play?tg_id={tg_id}';</script>"
    
    return "<p style='color: red;'>Недостаточно игроков!</p>"

@app.get("/games/{game_id}/join") #/games/1/join?tg_id=123&name=Cherry
async def join_game(game_id: int, tg_id: int, name: str, db: Session = Depends(get_db)):
    player = join_player_to_game(db, game_id, tg_id, name)
    count = get_players_count(db, game_id)
    return {"status": "joined", "player_id": player.id, "current_players": count}

@app.get("/game/{game_id}/play", response_class=HTMLResponse)
async def game_play_page(request: Request, game_id: int, tg_id: int = 123, db: Session = Depends(get_db)):
    game = db.query(GameSession).filter(GameSession.id == game_id).first()
    
    all_players = db.query(Player).filter(Player.game_id == game_id).all()
    
    for p in all_players:
        p.cards = db.query(Card).filter(Card.player_id == p.id).all()
        
    current_player = next((p for p in all_players if p.tg_user_id == tg_id), None)
 # Берем только живых игроков для расчета очереди
    alive_players = [p for p in all_players if not p.is_dead]
    active_player = alive_players[game.active_player_idx % len(alive_players)] if alive_players else None
    
    if not current_player:
        return "Вы не участвуете в этой игре"

    return templates.TemplateResponse(
        request=request, 
        name="play.html", 
        context={
            "game": game,
            "players": all_players,
            "me": current_player,
            "active_player": active_player, 
            "is_my_turn": (current_player.id == active_player.id) if current_player and active_player else False,
            "columns": ["biology", "appearance", "health", "profession", "fact", "hobby", "phobia", "inventory_1", "inventory_2"],
            "is_host": (tg_id == 123),
            "is_my_turn": (current_player.id == active_player.id) if current_player and active_player and not current_player.is_dead else False,
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
    seed_extra_cards()
    seed_biology_and_appearance(count=15)

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

from fastapi.responses import HTMLResponse # Убедись, что это есть в начале файла

@app.get("/games/{game_id}/use_ability", response_class=HTMLResponse)
async def use_card(
    actor_tg_id: int, 
    ability_card_id: int, 
    target_tg_id: int, 
    target_card_id: int = None, 
    actor_swap_card_id: int = None, 
    db: Session = Depends(get_db)
):
    ability_card = db.query(Card).filter(Card.id == ability_card_id).first()
    target_card = db.query(Card).filter(Card.id == target_card_id).first() if target_card_id else None
    actor_player = db.query(Player).filter(Player.tg_user_id == actor_tg_id).first()
    target_player = db.query(Player).filter(Player.tg_user_id == target_tg_id).first()

    # Вспомогательная функция для возврата ошибки в лог
    def error_response(msg: str):
        return HTMLResponse(f"<span style='color: #ff4757;'>❌ Ошибка: {msg}</span>")

    if not ability_card:
        return error_response("Карта способности не найдена")
    if ability_card.is_used:
        return error_response("Эта способность уже была использована")

    # Пример проверки (чтобы крали только инвентарь)
    if ability_card.interaction_type == ActionEnum.SPOIL:
        if not target_card or target_card.type != CardType.INVENTORY and target_card.type != CardType.HOBBY:
            return error_response("Красть можно только предметы инвентаря и кое что ещё!")

    # Бросаем кубики
    outcome, roll = resolve_ability(ability_card, target_card)

    if outcome == "success":
        result = execute_ability_mechanics(
            db=db, 
            ability_card=ability_card, 
            actor_player=actor_player, 
            target_player=target_player, 
            target_card=target_card, 
            actor_swap_card_id=actor_swap_card_id,
            roll=roll # <--- ДОБАВЬ ЭТУ СТРОКУ
        )
    if "error" in result:
            return error_response(result["error"])
    # Отмечаем, что способность потрачена
    ability_card.is_used = True
    db.commit()

    # Генерация текста лога
    rp_actions = [ActionEnum.HEAL, ActionEnum.STEAL]
    if ability_card.interaction_type in rp_actions:
        narrative = f"РП Действие выполнено! Статус: {outcome} (Кубик: {roll})."
        # Позже тут вернешь вызов ИИ
    else:
        narrative = f"Действие успешно выполнено на игроке {target_player.name}."
        

    # ВОТ ОНО! Возвращаем красивый HTML блок с логом и скриптом перезагрузки
    response_html = f"""
    <div style='color: #2ed573; font-weight: bold; padding: 10px; border: 1px dashed #2ed573; background: #1a2a1a;'>
        ✨ {narrative}
    </div>
    <script>
        // Через 2.5 секунды страница перезагрузится, чтобы обновить таблицу и скрыть способность
        setTimeout(() => location.reload(), 2500);
    </script>
    """
    
    return HTMLResponse(content=response_html)


@app.get("/admin/reset_all")
async def admin_reset(db: Session = Depends(get_db)):
    """Секретный эндпоинт для полного сброса игры"""
    success = reset_entire_database(db)
    
    if success:
        # Возвращаем простой скрипт, который выведет уведомление и вернет на главную
        return HTMLResponse(content="""
            <script>
                alert('База успешно обнулена: карты свободны, игры в ожидании!');
                window.location.href = '/';
            </script>
        """)
    else:
        return HTMLResponse(content="<h1 style='color:red;'>Ошибка при обнулении базы</h1>", status_code=500)
    


@app.get("/admin/cards", response_class=HTMLResponse)
async def admin_cards_page(
    request: Request, 
    card_type: str = None, 
    db: Session = Depends(get_db)
):
    # Получаем все возможные типы карт для выпадающего списка
    all_types = [t.value for t in CardType]
    
    query = db.query(Card)
    
    # Если выбран фильтр по типу
    if card_type and card_type in all_types:
        query = query.filter(Card.type == CardType(card_type))
    
    cards = query.order_by(Card.type).all()
    
    return templates.TemplateResponse(
        request=request, 
        name="admin_cards.html", 
        context={
            "cards": cards,
            "all_types": all_types,
            "current_type": card_type
        }
    )

@app.get("/game/{game_id}/self_reveal")
async def self_reveal(game_id: int, card_id: int, tg_id: int, db: Session = Depends(get_db)):
    card = db.query(Card).filter(Card.id == card_id).first()
    game = db.query(GameSession).filter(GameSession.id == game_id).first()
    
    if card.is_revealed:
        return HTMLResponse("<span style='color:#ffa502;'>Эта иконка уже раскрыта</span>")
    
    # Вскрываем карту
    card.is_revealed = True
    
    # ПЕРЕДАЕМ ХОД следующему игроку
    game.active_player_idx += 1
    
    db.commit()
    return HTMLResponse("<span style='color:#2ed573;'>Карта вскрыта! Ход переходит к следующему...</span>")


@app.get("/game/{game_id}/sync")
async def sync_game(game_id: int, db: Session = Depends(get_db)):
    game = db.query(GameSession).filter(GameSession.id == game_id).first()
    if not game:
        return {"error": "Игра не найдена"}
    
    # Получаем ID всех игроков за этим столом
    player_ids = [p.id for p in db.query(Player.id).filter(Player.game_id == game_id).all()]
    
    if not player_ids:
         return {"phase": game.current_phase, "hash": 0}

    # Считаем количество использованных способностей и раскрытых карт в этой игре
    used_cards = db.query(Card).filter(Card.player_id.in_(player_ids), Card.is_used == True).count()
    revealed_cards = db.query(Card).filter(Card.player_id.in_(player_ids), Card.is_revealed == True).count()
    
    # Создаем уникальный "слепок" (хэш) состояния игры
    # Он будет увеличиваться при любом действии любого игрока
    state_hash = game.active_player_idx + used_cards + revealed_cards
    
    return {
        "phase": game.current_phase,
        "hash": state_hash
    }



@app.post("/game/{game_id}/start_voting")
async def start_voting(game_id: int, db: Session = Depends(get_db)):
    """Переводит игру в фазу голосования (только хост)."""
    game = db.query(GameSession).filter(GameSession.id == game_id).first()
    game.current_phase = "voting"
    # Очищаем старые голоса, если они были
    db.query(Vote).filter(Vote.game_id == game_id).delete()
    db.commit()
    return {"status": "voting_started"}

@app.post("/game/{game_id}/cast_vote")
async def handle_vote(
    game_id: int, 
    voter_tg_id: int, 
    target_tg_id: int = None, # None если "против никого"
    db: Session = Depends(get_db)
):
    voter = db.query(Player).filter(Player.tg_user_id == voter_tg_id, Player.game_id == game_id).first()
    target = None
    if target_tg_id:
        target = db.query(Player).filter(Player.tg_user_id == target_tg_id, Player.game_id == game_id).first()
    
    cast_vote(db, game_id, voter.id, target.id if target else None)
    
    # Проверяем, все ли проголосовали
    total_players = db.query(Player).filter(Player.game_id == game_id, Player.is_dead == False).count()
    total_votes = db.query(Vote).filter(Vote.game_id == game_id).count()
    
    if total_votes >= total_players:
        # Автоматически завершаем голосование, если все сделали выбор
        return await finish_voting(game_id, db)
        
    return {"status": "voted"}

async def finish_voting(game_id: int, db: Session):
    result = get_voting_results(db, game_id)
    game = db.query(GameSession).filter(GameSession.id == game_id).first()
    
    msg = ""
    if result == "tie":
        msg = "Ничья! Никто не покидает бункер в этот раз."
    elif result is None:
        msg = "Голосование не состоялось."
    else:
        kicked_player = db.query(Player).filter(Player.id == result).first()
        kicked_player.is_dead = True
        msg = f"Игрок {kicked_player.name} изгоняется из убежища!"

    game.current_phase = "reveal" # Возвращаемся в фазу раскрытия
    game.active_player_idx = 0 # Сбрасываем очередь ходов
    db.commit()
    return {"status": "finished", "message": msg}


@app.post("/game/{game_id}/start_voting")
async def start_voting(game_id: int, tg_id: int, db: Session = Depends(get_db)):
    # Только хост (123) может начать голосование
    if tg_id != 123:
        return {"error": "Только ведущий может начать Судный час"}
        
    game = db.query(GameSession).filter(GameSession.id == game_id).first()
    game.current_phase = "voting"
    db.commit()
    return {"status": "voting_started"}