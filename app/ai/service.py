from ollama import AsyncClient
import json
from app.ai.respone import format_card_prompt  # Твой файл с промптами
from app.ai.parser import parse_random_response, parse_ai_response        # Твой парсер
from app.DB.models import Card, CardType, ActionEnum
from app.ai.respone import format_card_prompt
import asyncio
import time
import re
from sqlalchemy.orm import Session
from app.DB.database import SessionLocal
from app.DB.crud import create_card
from app.DB.schemas import CardCreate




async def ai_response(cat, data: dict,) -> str:
    start_time = time.perf_counter()

    prompt = format_card_prompt(cat, data)

    

    system_content = prompt[0]
    user_content = prompt[1]


    client = AsyncClient()
    print("отправили запрос")
    # Делаем до 3 попыток генерации, если вдруг JSON сломается
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await client.chat(
                model='gemma4:31b-cloud',  # Рекомендуется использовать модель 7b-8b для лучшей логики
                format='json', 
                messages=[
                    {'role': 'system', 'content': system_content},
                    {'role': 'user', 'content': user_content},
                ],
                options={
                    "temperature": 0.8,    # Чуть меньше хаоса для стабильного JSON
                    "num_ctx": 4096,       # Больше контекста для длинных описаний
                    "num_predict": 2500,   # УВЕЛИЧЕНО: даем модели достаточно токенов, чтобы дописать ответ
                    "repeat_penalty": 1.05 # СНИЖЕНО: разрешаем модели повторять кавычки и ключи JSON
                }
            )
            content = response['message']['content']
            # Проверяем, что нейросеть выдала валидный JSON
            # Если сломанный - уйдет в except и попробует заново
            match = re.search(r'```json\s+(.*?)\s+```', content, re.DOTALL)

            if match:
                json_string = match.group(1)
                datar = json.loads(json_string)
            else:
                datar = json.loads(content)
            
            end_time = time.perf_counter()
            duration = end_time - start_time
            print(f"✅ Карточка готова за {duration:.2f} сек. (Попытка {attempt + 1})")
            if isinstance(datar, dict) and "cards" in datar:
                datar = datar["cards"]

            return datar # Возвращаем список словарей
            
        except json.JSONDecodeError:
            print(f"⚠️ Ошибка JSON на попытке {attempt + 1}. Пробуем перегенерировать... {content}")
            continue
            
    print("❌ Не удалось сгенерировать валидный JSON за 3 попытки.")    
    return "{}" # Заглушка, чтобы бот не упал с ошибкой
semaphore = asyncio.Semaphore(1)  # Ограничиваем до 5 одновременных запросов к AI

async def safe_ai_response(cat, data):
    async with semaphore:
        return await ai_response(cat, data)

async def main1(batch_data: dict):
    start_time = time.perf_counter()

    categories = [
        "BIOLOGY", "APPEARANCE", "HEALTH", "JOB", 
        "HOBBY", "FACT", "PHOBIA", "INVENTORY_1", 
        "ABILITY_1", "ABILITY_2"
    ]

    all_results = {}
    db = SessionLocal() # Открываем сессию к БД

    try:
        for cat in categories:
            print(f"⌛ Начинаю генерацию категории: {cat} (3 карточки)...")
            try:
                # Внимание: правильный порядок аргументов (cat, batch_data)
                result = await safe_ai_response(cat, batch_data) 
                all_results[cat] = result

                # Сразу сохраняем полученные 3 карточки в базу!
                await process_batch_and_save(db, cat, result, batch_data)
                print(f"💾 Категория {cat} успешно сохранена в БД.")

            except Exception as e:
                print(f"❌ Ошибка генерации или сохранения {cat}: {e}")
    finally:
        db.close() # Обязательно закрываем подключение к БД в конце

    end_time = time.perf_counter()
    duration = end_time - start_time

    print(f"✅ Успешно обработано категорий: {len(all_results)} (Всего 33 карточки)")
    print(f"⏱️ Общее время: {duration:.2f} сек.")

    return all_results



async def process_batch_and_save(db: Session, cat: str, ai_list: list, batch_data: dict):
    """
    Объединяет текст от ИИ и цифры из рандома, затем пишет в БД по строгим правилам.
    """
    # Превращаем строку категории в значение для Enum (например, "INVENTORY_1" -> "inventory")
    raw_type = cat.lower().replace("_1", "").replace("_2", "")
    if raw_type == "job":
        raw_type = "profession" # В твоем CardType работа называется profession
        
    for i in range(1, 4):
        # Защита на случай, если ИИ вернул меньше 3 карточек
        ai_card = ai_list[i-1] if i-1 < len(ai_list) else {"name": "Ошибка ИИ", "description": ""}
        
        # Базовые значения (по умолчанию берем от ИИ)
        final_name = ai_card.get("name", "Без названия")
        final_desc = ai_card.get("description", "")
        skill = 0
        power = 0
        chance = 0
        chaos_level =0
        
        
        # 1. БИОЛОГИЯ (Свое имя и описание, ИИ игнорируем)
        if cat == "BIOLOGY":
            final_name = str(batch_data.get(f'race{i}', 'Неизвестно'))
            final_desc = f"Пол: {batch_data.get(f'gender{i}')}, Возраст: {batch_data.get(f'old{i}')} лет."
            
        # 2. ВНЕШНОСТЬ (Имя от ИИ, описание свое)
        elif cat == "APPEARANCE":
            final_desc = f"Рост: {batch_data.get(f'height{i}')}см, Вес: {batch_data.get(f'mass{i}')}кг. Телосложение: {batch_data.get(f'appearance_desc{i}')}."
            
        # 3. ЗДОРОВЬЕ (Все от ИИ)
        elif cat == "HEALTH":
            pass 
            
        # 4. РАБОТА (ИИ + данные скрипта)
        elif cat == "JOB":
            skill = batch_data.get(f'job_skill{i}', 0)
            
            # Проверяем, есть ли способность у работы
            can_be_ability = batch_data.get(f'job_can_be_ability{i}')
            ab_id = batch_data.get(f'job_ability_ID{i}', 10)
            
            if can_be_ability:
                power = ab_id
                ab_type = batch_data.get(f'job_ability_type{i}', '')
                chance = batch_data.get(f'job_skill{i}', '')
                chaos_level = 1
                if chance > 0:
                    final_desc += f"\n[способность: {ab_type}. Шанс использования на ком-то: {chance}%, шанс на себе: {chance-(chance*0.9)}%]"
                else: 
                    final_desc += f"\n[способность: {ab_type}.]"
        # 5, 6, 7. ХОББИ, ФАКТ, СТРАХ (Все от ИИ)
        elif cat in ["HOBBY", "FACT", "PHOBIA"]:
            pass
            
        # 8, 9. ИНВЕНТАРЬ (Все от ИИ)
        elif cat in ["INVENTORY_1", "INVENTORY_2"]:
            pass
            
        # 10, 11. СПОСОБНОСТИ (ИИ + ID + стандартное объяснение)
        elif cat in ["ABILITY_1", "ABILITY_2"]:
            prefix = "abil1" if cat == "ABILITY_1" else "abil2"
            
            ab_type = batch_data.get(f'{prefix}_type{i}', '')
            ab_id = batch_data.get(f'{prefix}_ID{i}', 10)
            
            power = ab_id # Записываем ID способности
            final_desc += f"\n[Эффект: {ab_type}]"

            chaos_level = 1

        # Формируем Pydantic схему и отправляем в CRUD
        new_card_data = CardCreate(
            type=CardType(raw_type),
            name=final_name,
            description=final_desc,
            skill_level=skill, #
            power_level=power, #способность
            base_success_chance = chance,
            chaos_level=chaos_level
        )
        
        # Вызываем функцию создания из crud.py
        create_card(db, new_card_data)
        
    return True