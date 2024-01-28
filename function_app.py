import azure.functions as func
import datetime
import json
import logging
import os

from aiohttp import web
from aiogram import F, Bot, Dispatcher, types
from aiogram.filters.command import Command
from PIL import Image
import asyncio

#prep
logging.basicConfig(level=logging.DEBUG)

#configuration parameters
tg_bot_token = os.environ.get('TG_BOT_TOKEN')
base_url = f'https://ace-doberman-ultimately.ngrok-free.app/api'

#create components
bot = Bot(token=tg_bot_token)
dp = Dispatcher()
app = func.FunctionApp()

#wire up hook on startup
async def on_startup(_):
    webhook_uri = f'{base_url}/{tg_bot_token}'
    logging.debug(f'=>set_webhook uri={webhook_uri}')
    result = await bot.set_webhook(webhook_uri)
    logging.debug(f'<=set_webhook {result}') 

on_startup(None)

#message handlers
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    logging.info("begin processing /start")
    await message.answer("Hmm...let me think a bit...")
    await asyncio.sleep(3)
    await message.answer("Ah, got it! Hello World!")
    logging.info("end processing /start")

@dp.message(Command("help"))
async def cmd_start(message: types.Message):
    await message.answer("Upload any image")

@dp.message(F.photo)
async def download_photo(message: types.Message, bot: Bot):
    #pass it through filesystem, not optimal but simplifies debugging
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

    processed_image = types.FSInputFile(result_filename)
    result = await message.answer_photo(
        processed_image,
        caption="Rotated image"
    )


@app.route(route=tg_bot_token, auth_level=func.AuthLevel.ANONYMOUS)
async def runaway1bot(req: func.HttpRequest) -> func.HttpResponse:
    json = req.get_json()
    logging.info(f'get_json:{json}')
    
    await dp.feed_raw_update(bot, json)
    resp = func.HttpResponse(status_code=200)
    logging.debug(f"prepared response: {resp}/body={resp.get_body()}") 
    return resp
    