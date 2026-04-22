from ollama import AsyncClient
import json
import re
from pathlib import Path
from app.ai.respone import SYSTEM_PROMPT # Используем общий системный промпт

PROMPT_DIR = Path("prompt")
# Загружаем промпт катастрофы
GAME_PROMPT = (PROMPT_DIR / "new_game.md").read_text(encoding="utf-8")

async def generate_disaster_ai(game_data: dict) -> dict:
    """
    Отправляет технические параметры игры в ИИ и получает художественное описание.
    game_data: словарь из твоего New_game.py (human_left, bunker_area и т.д.)
    """
    
    # Форматируем промпт данными из Python-скрипта
    game_data["eat_nice"] = game_data.get("eat_items", "Неизвестная еда")
    user_content = GAME_PROMPT.format(**game_data)
    
    client = AsyncClient()
    print("запуск игры")
    
    try:
        response = await client.chat(
            model='gemma4:31b-cloud', # Или qwen2.5:7b для скорости
            format='json',
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': user_content},
            ],
            options={
                "temperature": 0.9, # Для катастрофы можно чуть больше креатива
            }
        )
        
        # ... (начало функции как раньше)
        content = response['message']['content']
        
        # Парсинг JSON
        match = re.search(r'```json\s+(.*?)\s+```', content, re.DOTALL)
        result = json.loads(match.group(1)) if match else json.loads(content)
            
        # Гарантируем, что если ИИ не выдал описание еды, мы не упадем
        if "food_description" not in result:
            result["food_description"] = game_data.get("eat_items", "Запасы неопределенного происхождения")            
        return result 
# ...
        
    except Exception as e:
        print(f"❌ Ошибка генерации катастрофы: {e}")
        return {
            "disaster_description": "Произошло что-то ужасное, но ИИ об этом промолчал.",
            "bunker_features": "Бетонная коробка с запахом сырости."
        }