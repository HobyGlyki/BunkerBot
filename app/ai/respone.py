from pathlib import Path

# 1. Указываем путь к папке с промптами
PROMPT_DIR = Path("prompt")

# 2. Считываем файлы заранее (вне функций)
# .read_text() сразу открывает, читает и закрывает файл.
SYSTEM_PROMPT = (PROMPT_DIR / "SystemPrompt.md").read_text(encoding="utf-8")
CHARACTER_PROMPT = (PROMPT_DIR / "new_character.md").read_text(encoding="utf-8")


def format_character_prompt(data: dict) -> str:
    formatted_prompt = CHARACTER_PROMPT.format(**data)
    return [SYSTEM_PROMPT, formatted_prompt]



