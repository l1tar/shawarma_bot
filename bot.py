import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook

# Configuration
API_TOKEN = '7739157518:AAHthUbed4gd3diUvHi2Fp1lGVlSlfVcOSQ'  # Telegram Bot token
WEBHOOK_HOST = 'https://shawarma-bot-cb27.onrender.com'  # URL of your deployed bot on Render
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
admin_id = 123456789  # Замените на ваш ID

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
        "Привет! Я бот для заказа шаурмы. \\n"
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

    # Creating a single message for all selections
    await message.reply(
        "Выберите шаурму:\n" + "\n".join(tmenu.keys()) +
        "\n\nВыберите добавки (или 'Далее'):\n" + "\n".join(addons.keys()) + "\nДалее" +
        "\n\nВыберите напиток (или 'Далее'):\n" + "\n".join(drinks.keys()) + "\nДалее",
        reply_markup=get_keyboard(list(tmenu.keys()) + list(addons.keys()) + list(drinks.keys()) + ['Далее'])
    )

@dp.message_handler(lambda m: m.text in tmenu.keys())
async def process_main(m: types.Message):
    uid = m.from_user.id
    orders.setdefault(uid, {'items': [], 'total': 0, 'shawarma': {}})
    orders[uid]['shawarma'][m.text] = orders[uid]['shawarma'].get(m.text, 0) + 1
    orders[uid]['total'] += tmenu[m.text]
    await m.reply("Теперь выберите добавки или нажмите 'Далее'.")

@dp.message_handler(lambda m: m.text in addons.keys() or m.text == 'Далее')
async def process_addons(m: types.Message):
    uid = m.from_user.id
    if m.text in addons:
        orders[uid]['items'].append(f"Добавка: {m.text}")
        orders[uid]['total'] += addons[m.text]
    await m.reply("Теперь выберите напиток или нажмите 'Далее'.")

@dp.message_handler(lambda m: m.text in drinks.keys() or m.text == 'Далее')
async def process_drinks(m: types.Message):
    uid = m.from_user.id
    if m.text in drinks:
        orders[uid]['items'].append(f"Напиток: {m.text}")
        orders[uid]['total'] += drinks[m.text]
    await m.reply("Ваш заказ зарегистрирован. Для завершения заказа нажмите /final_order.")

@dp.message_handler(commands=['final_order'])
async def cmd_final(m: types.Message):
    if m.from_user.id != order_initiator:
        await m.reply("Только тот, кто начал заказ, может завершить его.")
        return

    # Формируем итоговый заказ с подсчётом количества продуктов
    summary = {}
    total_sum = 0
    for uid, o in orders.items():
        for shawarma, count in o['shawarma'].items():
            summary[shawarma] = summary.get(shawarma, 0) + count
        total_sum += o['total']

    text = "Итоговый заказ:\n"
    for shawarma, count in summary.items():
        text += f"{shawarma}: {count} шт.\n"
    text += f"Общая сумма: {total_sum}₽"

    # Отправляем итоговый заказ в личные сообщения инициатору и админу
    await bot.send_message(order_initiator, text)
    await bot.send_message(admin_id, text)
    await m.reply("Заказ завершён!")

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
