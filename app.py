from aiohttp import web
from aiogram import F, Bot, Dispatcher, types
from aiogram.filters.command import Command
import asyncio
from PIL import Image
import os
import logging
from inference import RealESRGAN_Inference
import cv2
import time

#prep
logging.basicConfig(level=logging.DEBUG)

#configuration parameters
tg_bot_token = os.environ.get('TG_BOT_TOKEN')
base_url = os.environ.get('WEBSITE_HOSTNAME')
logging.info(f'starting with tg_bot_token: {tg_bot_token}; base_url: {base_url}')

#create components
bot = Bot(token=tg_bot_token)
dp = Dispatcher()
app = web.Application()

#wire up hook on startup
async def on_startup(_):
    webhook_uri = f'{base_url}/api/{tg_bot_token}'
    logging.debug(f'=>set_webhook uri={webhook_uri}')
    result = await bot.set_webhook(webhook_uri)
    logging.debug(f'<=set_webhook {result}') 

#message handlers
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    logging.info("processing /start")
    await message.answer("[local app]Welcome! This bot upscales any image you send it using <a href='https://github.com/xinntao/Real-ESRGAN'>RealESGRAN_x2plus model</a>.", parse_mode='HTML')

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await asyncio.sleep(1)
    await message.answer("Upload any image and it will be upscaled using <a href='https://github.com/xinntao/Real-ESRGAN'>RealESGRAN_x2plus model</a>.", parse_mode='HTML')

@dp.message(F.photo)
async def download_photo(message: types.Message, bot: Bot):
    rotate = message.caption and "/rotate" in message.caption

    await asyncio.sleep(0.5)

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

#webhook handler
async def process(request):
    dict = await request.json()
    logging.debug(f"Decoded as {type(dict)}: {dict}")
    update_result = await dp.feed_raw_update(bot, dict)
    logging.debug(f"Update result: {update_result} {type(update_result)}")    

async def handle_webhook(request):
    url = str(request.url)
    index = url.rfind('/')
    token = url[index+1:]
    
    if token == tg_bot_token:
        logging.debug(f"Received request {request}")
        asyncio.create_task(process(request))
        resp = web.Response();
        logging.debug(f"prepared response: {resp}/body={resp.body}")
        return resp
    else:
        return web.Response(status=403)
        


### running the app
if __name__ == "__main__":
    app.router.add_post(f'/api/{tg_bot_token}', handler=handle_webhook)
    app.on_startup.append(on_startup) 
    web.run_app(
        app,
        host='0.0.0.0',
        port=80
    )