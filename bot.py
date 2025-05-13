import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook

# Configuration
API_TOKEN = ('7739157518:AAHthUbed4gd3diUvHi2Fp1lGVlSlfVcOSQ')  # Telegram Bot token from environment
WEBHOOK_HOST = ('https://shawarma-bot-cb27.onrender.com')  # e.g. https://your-app-name.onrender.com
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = int(os.getenv('PORT', 8080))

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Menu data
tmenu = {
    'Куриная шаурма': 200,
    'Говяжья шаурма': 250,
    'Вегетарианская': 180
}
addons = {
    'Сыр': 30,
    'Острый соус': 20,
    'Халапеньо': 25
}
drinks = {
    'Кола': 50,
    'Фанта': 50,
    'Вода': 30
}

# Orders storage
orders = {}
order_initiator = None

# Utility to build reply keyboards
def get_keyboard(options):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for opt in options:
        keyboard.add(types.KeyboardButton(opt))
    return keyboard

# Handlers
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply(
        "Привет! Я бот для заказа шаурмы. \n"  
        "Чтобы начать сбор заказов, отправь /start_order"
    )

@dp.message_handler(commands=['start_order'])
async def cmd_start_order(message: types.Message):
    global order_initiator, orders
    if order_initiator:
        await message.reply(f"Сбор заказа уже начат пользователем.")
        return
    order_initiator = message.from_user.id
    orders = {}
    await message.reply("Сбор заказа начат! Каждый может добавить свой заказ командой /order.")

@dp.message_handler(commands=['order'])
async def cmd_order(message: types.Message):
    if not order_initiator:
        await message.reply("Сначала начни сбор заказа: /start_order")
        return
    await message.reply("Выберите шаурму:", reply_markup=get_keyboard(list(tmenu.keys())))

@dp.message_handler(lambda m: m.text in tmenu.keys())
async def process_main(m: types.Message):
    uid = m.from_user.id
    orders.setdefault(uid, {'items': [], 'total': 0})
    orders[uid]['items'].append(m.text)
    orders[uid]['total'] += tmenu[m.text]
    await m.reply("Выберите добавки или 'Без добавок':", reply_markup=get_keyboard(list(addons.keys()) + ['Без добавок']))

@dp.message_handler(lambda m: m.text in addons.keys() or m.text == 'Без добавок')
async def process_addons(m: types.Message):
    uid = m.from_user.id
    if m.text in addons:
        orders[uid]['items'].append(f"Добавка: {m.text}")
        orders[uid]['total'] += addons[m.text]
        return
    await m.reply("Выберите напиток или 'Без напитка':", reply_markup=get_keyboard(list(drinks.keys()) + ['Без напитка']))

@dp.message_handler(lambda m: m.text in drinks.keys() or m.text == 'Без напитка')
async def process_drinks(m: types.Message):
    uid = m.from_user.id
    if m.text in drinks:
        orders[uid]['items'].append(f"Напиток: {m.text}")
        orders[uid]['total'] += drinks[m.text]
    await m.reply("Заказ зарегистрирован. Для просмотра своего заказа — /my_order.")

@dp.message_handler(commands=['my_order'])
async def cmd_my_order(m: types.Message):
    uid = m.from_user.id
    order = orders.get(uid)
    if not order:
        await m.reply("У вас нет заказа.")
        return
    text = "Ваш заказ:\n"
    for item in order['items']:
        text += f"- {item}\n"
    text += f"Итого: {order['total']}₽"
    await m.reply(text)

@dp.message_handler(commands=['final_order'])
async def cmd_final(m: types.Message):
    if m.from_user.id != order_initiator:
        return
    text = "Итоговый заказ:\n"
    total_sum = 0
    for uid, o in orders.items():
        user = (await bot.get_chat(uid)).full_name
        items = '\n'.join(o['items'])
        text += f"{user}:\n{items}\nСумма: {o['total']}₽\n\n"
        total_sum += o['total']
    text += f"Общая сумма: {total_sum}₽"
    await m.reply(text)

# Startup and shutdown callbacks
async def on_startup(dp):
    logging.info('Setting webhook...')
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(dp):
    logging.info('Removing webhook...')
    await bot.delete_webhook()

if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
