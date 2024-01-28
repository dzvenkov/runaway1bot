from aiohttp import web
from aiogram import F, Bot, Dispatcher, types
from aiogram.filters.command import Command
from PIL import Image
import os
import logging

#prep
logging.basicConfig(level=logging.DEBUG)

#configuration parameters
tg_bot_token = os.environ.get('TG_BOT_TOKEN')
base_url = f'https://ace-doberman-ultimately.ngrok-free.app'

#create components
bot = Bot(token=tg_bot_token)
dp = Dispatcher()
app = web.Application()


#do on web app startup
async def on_startup(_):
    webhook_uri = f'{base_url}/{tg_bot_token}'
    logging.debug(f'=>set_webhook uri={webhook_uri}')
    result = await bot.set_webhook(webhook_uri)
    await bot.set_my_name()
    logging.debug(f'<=set_webhook {result}') 

#message handlers
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Hello!")

@dp.message(Command("help"))
async def cmd_start(message: types.Message):
    await message.answer("Upload any image")

@dp.message(F.photo)
async def download_photo(message: types.Message, bot: Bot):
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
        caption="Processing results"
    )

    
#webhook handler
async def handle_webhook(request):
    url = str(request.url)
    index = url.rfind('/')
    token = url[index+1:]
    
    if token == tg_bot_token:
        json = await request.json()
        update = types.Update(**json)
        logging.debug(f"Recieved update {json}")
        update_result = await dp.feed_webhook_update(bot, update)
        logging.debug(f"Update result: {update_result}")
        resp = web.Response();
        logging.debug(f"prepared response: {resp}")
        return resp
    else:
        return web.Response(status=403)


### running the app
if __name__ == "__main__":
    app.router.add_post(f'/{tg_bot_token}', handler=handle_webhook)
    app.on_startup.append(on_startup) 
    web.run_app(
        app,
        host='0.0.0.0',
        port=80
    )