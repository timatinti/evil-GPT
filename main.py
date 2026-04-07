import os
import logging
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from openai import AsyncOpenAI

load_dotenv()

# Настройки
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Системный промпт (можно менять под что угодно)
SYSTEM_PROMPT = """Ты полезный AI-ассистент. Отвечай дружелюбно и по делу."""

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Хранилище истории диалогов {user_id: [messages]}
user_contexts = {}

MAX_HISTORY = 10

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("Привет! Я AI-бот. Задавай любые вопросы!")

@dp.message(Command("clear"))
async def clear_command(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_contexts:
        del user_contexts[user_id]
    await message.answer("История диалога очищена!")

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    user_text = message.text

    # Инициализируем историю, если её нет
    if user_id not in user_contexts:
        user_contexts[user_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    # Добавляем сообщение пользователя
    user_contexts[user_id].append({"role": "user", "content": user_text})

    # Обрезаем историю
    if len(user_contexts[user_id]) > MAX_HISTORY * 2 + 1:
        user_contexts[user_id] = [
            user_contexts[user_id][0]
        ] + user_contexts[user_id][-(MAX_HISTORY * 2):]

    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=user_contexts[user_id],
            temperature=0.7,
            max_tokens=1000
        )

        bot_reply = response.choices[0].message.content
        user_contexts[user_id].append({"role": "assistant", "content": bot_reply})

        await message.answer(bot_reply)

    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await message.answer("Извините, произошла ошибка. Попробуйте позже.")

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())