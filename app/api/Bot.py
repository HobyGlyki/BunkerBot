import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "7927953823:AAFDHFIZ7n0nuWGpE2FcLnvHhX6ZTIASS-I"
ADMIN_ID = 123  # Твой TG ID Хоста!

# Глобальная переменная: бот стартует "вслепую", без ссылки
current_web_url = None

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- СЕКРЕТНАЯ КОМАНДА АДМИНА ---
@dp.message(Command("setlink"))
async def set_link_cmd(message: types.Message):
    global current_web_url
    
    # Защита: реагируем только на тебя
    if message.from_user.id != ADMIN_ID:
        return

    # Извлекаем ссылку из сообщения (например: /setlink https://rnxyz.trycloudflare.com)
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("⚠️ Укажи ссылку! Формат:\n/setlink https://твой-адрес.trycloudflare.com")
        return

    new_url = parts[1].strip()
    # На всякий случай отрезаем слэш на конце, если он есть
    if new_url.endswith('/'):
        new_url = new_url[:-1]

    current_web_url = new_url
    await message.answer(f"✅ Врата Убежища открыты!\n\nТекущая ссылка: {current_web_url}\nТеперь игроки могут писать /start")


# --- ОБЫЧНЫЙ ВХОД ДЛЯ ИГРОКОВ ---
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    global current_web_url
    user_id = message.from_user.id
    name = message.from_user.first_name or "Выживший"

    # Если ты еще не скинул ссылку боту:
    if not current_web_url:
        await message.answer("📡 Сервер убежища пока недоступен. Ожидайте сигнала от Ведущего...")
        return

    # Если ссылка есть — пускаем в игру
    game_url = f"{current_web_url}/?tg_id={user_id}&name={name}"
    
    web_app = WebAppInfo(url=game_url)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="☢️ Войти в Бункер", web_app=web_app)]
        ]
    )
    
    await message.answer(
        f"Внимание, {name}! Сирена уже воет. Успей занять место в убежище.", 
        reply_markup=keyboard
    )

async def main():
    print("Бот запущен! Ждет ссылку от Администратора...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())