import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

API_TOKEN = os.getenv("API_TOKEN")  # Добавь переменную в Render

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

menu = {
    "Шаурма куриная": 200,
    "Шаурма говяжья": 250,
    "Фалафель": 180
}

add_ons = {
    "Сыр": 30,
    "Острый соус": 20,
    "Халапеньо": 25
}

drinks = {
    "Кола": 50,
    "Спрайт": 50,
    "Вода": 30
}

orders = {}
current_leader = None

def get_keyboard(options):
    return ReplyKeyboardMarkup(resize_keyboard=True).add(*[KeyboardButton(opt) for opt in options])

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.reply("Привет! Чтобы начать сбор заказа, напиши /начатьзаказ")

@dp.message_handler(commands=['начатьзаказ'])
async def start_order(message: types.Message):
    global current_leader, orders
    if current_leader:
        await message.reply(f"Сбор заказа уже начат пользователем {current_leader}.")
    else:
        current_leader = message.from_user.id
        orders = {}
        await message.reply("Сбор заказа начат! Используйте /заказать, чтобы добавить свой заказ.")

@dp.message_handler(commands=['заказать'])
async def order_cmd(message: types.Message):
    if not current_leader:
        await message.reply("Сбор заказа ещё не начат. Напиши /начатьзаказ.")
        return

    kb = get_keyboard(list(menu.keys()))
    await message.reply("Выбери основное блюдо:", reply_markup=kb)

@dp.message_handler(lambda msg: msg.text in menu)
async def handle_main(msg: types.Message):
    user_id = msg.from_user.id
    orders.setdefault(user_id, {"name": msg.from_user.full_name, "items": [], "total": 0})
    orders[user_id]["items"].append(msg.text)
    orders[user_id]["total"] += menu[msg.text]

    kb = get_keyboard(list(add_ons.keys()) + ["Без добавок", "Готово"])
    await msg.reply("Добавки?", reply_markup=kb)

@dp.message_handler(lambda msg: msg.text in add_ons or msg.text == "Без добавок")
async def handle_addons(msg: types.Message):
    user_id = msg.from_user.id
    if msg.text in add_ons:
        orders[user_id]["items"].append(f"Добавка: {msg.text}")
        orders[user_id]["total"] += add_ons[msg.text]
        await msg.reply("Ещё добавка или нажми 'Готово'")
    else:
        kb = get_keyboard(list(drinks.keys()) + ["Без напитка", "Завершить"])
        await msg.reply("Напитки?", reply_markup=kb)

@dp.message_handler(lambda msg: msg.text in drinks or msg.text == "Без напитка")
async def handle_drinks(msg: types.Message):
    user_id = msg.from_user.id
    if msg.text in drinks:
        orders[user_id]["items"].append(f"Напиток: {msg.text}")
        orders[user_id]["total"] += drinks[msg.text]
    await msg.reply("Готово! Если хочешь изменить заказ, напиши /заказать.")

@dp.message_handler(commands=['итог'])
async def summary_cmd(message: types.Message):
    if message.from_user.id != current_leader:
        await message.reply("Только инициатор заказа может видеть итог.")
        return

    result = "Итоговый заказ:\n\n"
    total_sum = 0
    for data in orders.values():
        result += f"{data['name']}:\n"
        for item in data["items"]:
            result += f" - {item}\n"
        result += f"Итого: {data['total']} руб\n\n"
        total_sum += data["total"]

    result += f"Общая сумма: {total_sum} руб"
    await message.reply(result)

@dp.message_handler(commands=['сброс'])
async def reset_cmd(message: types.Message):
    global current_leader, orders
    if message.from_user.id == current_leader:
        current_leader = None
        orders = {}
        await message.reply("Сбор заказа сброшен.")
    else:
        await message.reply("Только лидер заказа может сбросить его.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
