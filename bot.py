import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import register_handlers
from middlewares import LoggingMiddleware

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.message.middleware(LoggingMiddleware())
register_handlers(dp)

async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())