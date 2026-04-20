import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from service import main1

BOT_TOKEN = "7927953823:AAFDHFIZ7n0nuWGpE2FcLnvHhX6ZTIASS-I"

strs = {
    'biology': {'gender': 'мужчина', 'old': 151, 'race': 'ящеролюд'}, 
    'appearance': {'appearance': 'Рама 2 на 2', 'is_nice': 'да', 'mass': 187, 'height': 237}, 
    'health': {'heal': 'недуг не серъёзный', 'is_appearance': 'на теле есть заметные симптомы'}, 
    'job': {'job': 'работает в сфере искусства', 'is_nice': 'полезная', 'skill': 9, 'can_be_ability': False, 'ability_type': 'None', 'ability ID': 10}, 
    'hobby': {'hobby': 'Атлетическое телосложение', 'is_nice': 'нет', 'is_job': 'нет'},
     'fact': {'is_positive': 'нет', 'is_inexpected': 'нет', 'chaos': 'Скучная норма'}, 
    'phobia': {'phobia': 'Мрачная тайна', 'is_nice': 'нет'}, 
    'inventory_1': {'inventory': 'Запущенный маразм', 'is_job': 'нет', 'is_nice': 'нет'}, 
    'inventory_2': {'inventory': 'Странный заскок', 'is_job': 'нет', 'is_nice': 'да'}, 
    'ability_1': {'ability name': 'заменить карточку игроку', 'is_chaotic': 'метерный абсурд', 'ability ID': 5}, 
    'ability_2': {'ability name': 'украсть предмет', 'is_chaotic': 'Странный заскок', 'ability ID': 2}}

# Инициализация бота с HTML парсингом (он стабильнее для форматирования)
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# --- ХЕНДЛЕРЫ ---

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    resp = await main1(strs, 1) 
    print(resp)
    await message.answer(("SAFSAFASFSA"),  parse_mode=ParseMode.MARKDOWN)

async def main():
    print("Бот запущен (HTML Mode)...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")