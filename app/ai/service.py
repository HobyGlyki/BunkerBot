from ollama import AsyncClient
import json
from respone import format_character_prompt  # Твой файл с промптами
from parser import parse_random_response, parse_ai_response, map_character_data        # Твой парсер
import asyncio
import time




async def ai_response(data: dict) -> str:
    start_time = time.perf_counter() # Стартуем замер
    character_description = map_character_data(data)
    prompt = format_character_prompt(character_description)
    data = parse_random_response(data)


    system_content = prompt[0]
    user_content = prompt[1]


    client = AsyncClient()
    response = await client.chat(
        model='llama3.2:3b',
        format='json', 
        messages=[
            {'role': 'system', 'content': system_content},
            {'role': 'user', 'content': user_content},
        ],
        
        options={
        "temperature": 0.4,    # Делает ответы более четкими и менее "размазанными"
        "num_predict": 1024,   # Ограничиваем максимальную длину, чтобы она не уходила в бесконечные описания
        "top_p": 0.9,          # Срезает маловероятные варианты слов, ускоряя выбор
        "num_ctx": 2048,
        "num_thread": 8
    }
    )
    content = response['message']['content']
    end_time = time.perf_counter()
    duration = end_time - start_time
    print(f"✅ Задача готова за {duration:.2f} сек.")
    return content


semaphore = asyncio.Semaphore(3)

async def safe_ai_response(data):
    async with semaphore:
        return await ai_response(data)

async def main(cards: dict):
    # Создаем список задач (корутин)
    tasks = [safe_ai_response(cards) for _ in range(7)]
    all_results = await asyncio.gather(*tasks)
    # Запускаем всё ОДНОВРЕМЕННО
    # return_exceptions=True поможет, если одна генерация упадет, остальные выживут
    print(f"Сгенерировано персонажей: {len(all_results)}")
    print(all_results)
