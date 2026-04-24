from ollama import AsyncClient
import json
import re
from pathlib import Path
from app.ai.respone import SYSTEM_PROMPT

PROMPT_DIR = Path("prompt")

GAME_PROMPT = (PROMPT_DIR / "action_card.md").read_text(encoding="utf-8")