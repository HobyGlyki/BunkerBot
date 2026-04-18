from ollama import AsyncClient
import json
from respone import format_character_prompt  # Твой файл с промптами
from parser import parse_random_response, parse_ai_response, map_character_data        # Твой парсер
import asyncio
import time


strs= {'biology': {'gender': 'мужчина', 'old': 733, 'race': 'орк'}, 'appearance': {'appearance': 'ходячий анекдот', 'is_nice': 'нет', 'mass': 240, 'height': 284}, 'health': {'heal': 'хрупкое создание', 'is_appearance': 'всё лицо — сплошной симптом'}, 'job': {'job': 'цепной пес режима', 'is_nice': 'Бесполезная', 'skill': 56, 'can_be_ability': 0, 'ability_type': 'абсолютная бездарность', 'ability ID': 10}, 'hobby': {'hobby': 'модельный сорт', 'is_nice': 'нет', 'is_job': 'нет'}, 'fact': {'is_positive': 'нет', 'is_inexpected': 'нет', 'chaos': 'Терминальное безумие'}, 'phobia': {'phobia': 'Легкий абсурд', 'is_nice': 'да'}, 'inventory_1': {'inventory': 'Странный заскок', 'is_job': 'да', 'is_nice': 'да'}, 'inventory_2': {'inventory': 'Легкий абсурд', 'is_job': 'нет', 'is_nice': 'нет'}, 'ability_1': {'ability name': 'депортация в бункер', 'is_chaotic': 'Запущенный маразм', 'ability ID': 9}, 'ability_2': {'ability name': 'регенерация тканей', 'is_chaotic': 'Легкий абсурд', 'ability ID': 1}}

async def ai_response(data: dict) -> str:
    start_time = time.perf_counter() # Стартуем замер
    character_description = map_character_data(data)
    prompt = format_character_prompt(character_description)
    data = parse_random_response(data)


    system_content = prompt[0]
    user_content = prompt[1]


    client = AsyncClient()
    response = await client.chat(
        model='qwen2.5:3b ',
        format='json', 
        messages=[
            {'role': 'system', 'content': system_content},
            {'role': 'user', 'content': user_content},
        ],
        
        options={
            "temperature": 0.7,   # Чуть ниже, чтобы меньше галлюцинировал
            "num_ctx": 3072,
            "num_predict": 500,   # ЭТО ВАЖНО: 350 токенов за глаза хватит на 11 лаконичных полей
            "repeat_penalty": 1.3 # Увеличим, чтобы он не повторял одни и те же слова
        }
    )
    content = response['message']['content']
    end_time = time.perf_counter()
    duration = end_time - start_time
    print(f"✅ Задача готова за {duration:.2f} сек.")
    return content


semaphore = asyncio.Semaphore(3)  # Ограничиваем до 5 одновременных запросов к AI

async def safe_ai_response(data):
    async with semaphore:
        return await ai_response(data)

async def main(cards: dict, count: int):
    start_time = time.perf_counter() # Стартуем замер
    # Создаем список задач (корутин)
    tasks = [safe_ai_response(cards) for _ in range(count)]
    all_results = await asyncio.gather(*tasks)
    # Запускаем всё ОДНОВРЕМЕННО
    # return_exceptions=True поможет, если одна генерация упадет, остальные выживут
    end_time = time.perf_counter()
    duration = end_time - start_time
    print(f"Сгенерировано персонажей: {len(all_results)}")
    print(f"Время генерации: {duration:.2f} сек.")
    print(all_results)


if __name__ == "__main__":
    # Запускаем цикл ОДИН раз
    asyncio.run(main(strs, 3))