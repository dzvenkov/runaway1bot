import azure.functions as func
import logging
import sys
from opencensus.ext.azure.log_exporter import AzureLogHandler

import os
import time

from aiogram import F, Bot, Dispatcher, types
from aiogram.filters.command import Command
import asyncio

from inference import RealESRGAN_Inference
from PIL import Image
import cv2

#prep
logging.basicConfig(stream=sys.stdout, level=logging.info)

app_insight_conn = os.environ.get('APPLICATIONINSIGHTS_CONNECTION_STRING')

if app_insight_conn:
    logger = logging.getLogger(__name__)
    logger.addHandler(AzureLogHandler(connection_string=app_insight_conn))


#configuration parameters
tg_bot_token = os.environ.get('TG_BOT_TOKEN')
base_url = os.environ.get('WEBSITE_HOSTNAME')
logging.info(f'starting with tg_bot_token: {tg_bot_token}; base_url: {base_url}')
print(f'tg_bot_token: {tg_bot_token}; base_url: {base_url}')
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
    await message.answer("Welcome! This bot upscales any image you send it using <a href='https://github.com/xinntao/Real-ESRGAN'>RealESGRAN_x2plus model</a>.", parse_mode='HTML')

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await asyncio.sleep(1)
    await message.answer("Upload any image and it will be upscaled using <a href='https://github.com/xinntao/Real-ESRGAN'>RealESGRAN_x2plus model</a>.", parse_mode='HTML')

@dp.message(F.photo)
async def download_photo(message: types.Message, bot: Bot):
    rotate = message.caption and "/rotate" in message.caption

    await asyncio.sleep(0.5) #pretend thinking :)

    if not rotate:
        await message.answer("Nice picture! Ok, now I'll upscale it x2, this may take couple of minutes, please be patient");

    os.makedirs("./downloads", exist_ok=True)
    os.makedirs("./results", exist_ok=True)
    source_filename = f"./downloads/{message.photo[-1].file_id}.jpg"
    result_filename = f"./results/{message.photo[-1].file_id}.jpg"
    await bot.download(
        message.photo[-1],
        destination=source_filename
    )
    
    start_time = time.time()
    if rotate:
        with Image.open(source_filename) as img:
            img.rotate(180).save(result_filename)
        result_message = f"Here's the rotated image, it took {time.time() - start_time:.1f} seconds to make it"
    else:
        image = cv2.imread(source_filename, cv2.IMREAD_UNCHANGED)
        inference = RealESRGAN_Inference()
        output = inference.upsample(image)
        cv2.imwrite(result_filename, output)
        result_message = f"Here's the upscaled image, it took {time.time() - start_time:.1f} seconds to make it"

    processed_image = types.FSInputFile(result_filename)
    await message.answer_photo(
        processed_image,
        caption=result_message
    )

#azure function
async def process(req: func.HttpRequest):
    try:
        json = req#for exception reporting if get_json fails
        json = req.get_json()
        logging.info(f'get_json:{json}')
        
        await dp.feed_raw_update(bot, json)
        
    except Exception:
        logging.exception(f"Exception while processing request {json}") 

print("registering runaway1bot function")

@app.route(route=tg_bot_token, auth_level=func.AuthLevel.ANONYMOUS)
async def runaway1bot(req: func.HttpRequest) -> func.HttpResponse:
    #respond immediately, TG has 60 sec timeout, inference may take longer
    asyncio.create_task(process(req))
    return func.HttpResponse(status_code=200)
