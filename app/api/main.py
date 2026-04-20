from fastapi import FastAPI, Form, Request
from fastapi.templating import Jinja2Templates
import os
import json

from app.ai.parser import parse_ai_response
from app.ai.service import main1
from app.services.new_card import generate_full_character

from app.DB.database import SessionLocal
from app.DB.models import Card
from app.DB.crud import get_card

app = FastAPI()
templates = Jinja2Templates(directory="frontend")


@app.get("/new_cards")
async def index():
    strs = generate_full_character()
    new_card = await main1(strs)
    # json_obj = parse_ai_response(new_card[0])
    return new_card, strs


@app.get("/cards")
async def get_all_cards():
    """
    Достает все карточки из базы данных и возвращает их списком.
    """
    # Запрашиваем все записи из таблицы cards
    cards = get_card(SessionLocal())
    
    # Возвращаем общее количество и сами карточки
    return {
        "total_cards_in_db": len(cards),
        "cards": cards
    }