import asyncio
import logging
import os
from aiogram import F, Bot, Dispatcher, types
from aiogram.types import Message, FSInputFile
from aiogram.filters.command import Command
from PIL import Image


logging.basicConfig(level=logging.INFO)
bot = Bot(token=os.environ.get('TG_BOT_TOKEN'))
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Hello!")

@dp.message(Command("help"))
async def cmd_start(message: types.Message):
    await message.answer("Upload any image")

@dp.message(F.photo)
async def download_photo(message: Message, bot: Bot):
    os.makedirs("./downloads", exist_ok=True)
    os.makedirs("./results", exist_ok=True)
    source_filename = f"./downloads/{message.photo[-1].file_id}.jpg"
    result_filename = f"./results/{message.photo[-1].file_id}.jpg"
    await bot.download(
        message.photo[-1],
        destination=source_filename
    )
    with Image.open(source_filename) as img:
        img.rotate(180).save(result_filename)

    processed_image = FSInputFile(result_filename)
    result = await message.answer_photo(
        processed_image,
        caption="Processing results"
    )


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())