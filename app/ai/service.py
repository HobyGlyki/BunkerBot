from ollama import AsyncClient
import json
from respone import format_character_prompt  # Твой файл с промптами
from parser import parse_random_response, parse_ai_response, map_character_data        # Твой парсер
import asyncio
import time




async def ai_response(data: dict) -> str:
    start_time = time.perf_counter()
    character_description = map_character_data(data)
    prompt = format_character_prompt(character_description)
    data = parse_random_response(data)


    system_content = prompt[0]
    user_content = prompt[1]


    client = AsyncClient()
    
    # Делаем до 3 попыток генерации, если вдруг JSON сломается
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await client.chat(
                model='qwen2.5:7b',  # Рекомендуется использовать модель 7b-8b для лучшей логики
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
            json.loads(content)
            
            end_time = time.perf_counter()
            duration = end_time - start_time
            print(f"✅ Карточка готова за {duration:.2f} сек. (Попытка {attempt + 1})")
            return content
            
        except json.JSONDecodeError:
            print(f"⚠️ Ошибка JSON на попытке {attempt + 1}. Пробуем перегенерировать...")
            continue
            
    print("❌ Не удалось сгенерировать валидный JSON за 3 попытки.")
    return "{}" # Заглушка, чтобы бот не упал с ошибкой
semaphore = asyncio.Semaphore(1)  # Ограничиваем до 5 одновременных запросов к AI

async def safe_ai_response(data):
    async with semaphore:
        return await ai_response(data)

async def main1(cards: dict, count: int):
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
    return all_results

    