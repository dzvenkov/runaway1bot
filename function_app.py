import azure.functions as func
import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler

import os

from aiogram import F, Bot, Dispatcher, types
from aiogram.filters.command import Command
import asyncio

from PIL import Image


#prep
logging.basicConfig(level=logging.info)

app_insight_conn = os.environ.get('APPLICATIONINSIGHTS_CONNECTION_STRING')

if app_insight_conn:
    logger = logging.getLogger(__name__)
    logger.addHandler(AzureLogHandler(connection_string=app_insight_conn))


#configuration parameters
tg_bot_token = os.environ.get('TG_BOT_TOKEN')
base_url = os.environ.get('WEBSITE_HOSTNAME')
logging.info(f'starting with tg_bot_token: {tg_bot_token}; base_url: {base_url}')
#create components
bot = Bot(token=tg_bot_token)
dp = Dispatcher()
app = func.FunctionApp()

set_url = "none"

#wire up hook on startup
async def startup():
    global set_url
    webhook_uri = f'{base_url}/api/{tg_bot_token}'
    set_url = webhook_uri
    logging.info(f'=>set_webhook uri={webhook_uri}')
    result = await bot.set_webhook(webhook_uri)
    logging.info(f'<=set_webhook {result}') 
    set_url = f">{webhook_uri}<"

logging.info(f"startup {base_url}/api/{tg_bot_token}")
asyncio.create_task(startup())

#message handlers
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    logging.info("processing /start")
    await message.answer("Welcome! This bot upscales any image you send it using Real-ESGRAN model.")

@dp.message(Command("test"))
async def cmd_test(message: types.Message):
    logging.info("begin processing /test")
    await message.answer("[function_app]start test")
    await asyncio.sleep(3)
    await message.answer(f"finish test! Hello World! incoming message {message.model_dump_json()}")
    logging.info("end processing /test")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("Upload any image and it will be upscaled using Real-ESGRAN model.")

@dp.message(F.photo)
async def download_photo(message: types.Message, bot: Bot):
    logging.info("begin processing image upload")
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
    logging.info(f"end processing image upload {result}")


@app.route(route=tg_bot_token, auth_level=func.AuthLevel.ANONYMOUS)
async def runaway1bot(req: func.HttpRequest) -> func.HttpResponse:
    try:
        json = req.get_json()
        logging.info(f'get_json:{json}')
        
        await dp.feed_raw_update(bot, json)
        resp = func.HttpResponse(status_code=200)
        
    except Exception as e:
        logging.error(f"exception:{e}; url={set_url}") 
        resp = func.HttpResponse(f"exception:{e}; url={set_url}", status_code=200)
    finally:
        logging.info(f"sending response: {resp}|body={resp.get_body()}") 
        return resp
    
