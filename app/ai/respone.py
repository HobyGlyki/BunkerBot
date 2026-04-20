from pathlib import Path
import re

# 1. Указываем путь к папке с промптами
PROMPT_DIR = Path("prompt")

# 2. Считываем файлы заранее (вне функций)
# .read_text() сразу открывает, читает и закрывает файл.
SYSTEM_PROMPT = (PROMPT_DIR / "SystemPrompt.md").read_text(encoding="utf-8")
def load_card_prompts() -> dict:
    # Читаем наш новый файл
    content = (PROMPT_DIR / "new_character.md").read_text(encoding="utf-8")
    
    # Регулярка, которая ищет заголовки вида "# ИМЯ" на отдельной строке
    parts = re.split(r'^#\s+([A-Z0-9_]+)\s*$', content, flags=re.MULTILINE)
    
    prompts = {}
    # Пропускаем parts[0] (там пустота до первого заголовка)
    for i in range(1, len(parts), 2):
        key = parts[i]              # Например, 'BIOLOGY'
        value = parts[i+1].strip()  # Сам текст промпта
        prompts[key] = value
        
    return prompts

# Загружаем ОДИН РАЗ при старте скрипта
CARD_PROMPTS =  load_card_prompts()


def format_card_prompt(card_type: str, data: dict) -> list:
    """
    card_type: Ключ из файла, например 'INVENTORY' или 'HEALTH'
    data: Твой огромный словарь со всеми переменными (лишние проигнорируются)
    """
    raw_prompt = CARD_PROMPTS.get(card_type.upper())
    if not raw_prompt:
        raise ValueError(f"Промпт для {card_type} не найден!")
    
    # Подставляем переменные. Python сам возьмет только те, что нужны конкретному промпту
    formatted_prompt = raw_prompt.format(**data)
    
    return [SYSTEM_PROMPT, formatted_prompt]

