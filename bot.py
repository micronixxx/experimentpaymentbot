import asyncio
import json
import random
import string
from aiogram import Bot, Dispatcher, types
from aiogram.types import LabeledPrice, PreCheckoutQuery
from aiogram.filters import Command

# ===== КОНФИГУРАЦИЯ =====
BOT_TOKEN = "8643077565:AAHmpfnN7lPuWKdVcDw08TzOWbAtJCxBbr8"
ADMIN_ID = 6846103023  # Узнай через @userinfobot

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Цены в Stars (XTR) — 1 Star = 1 единица
PRICES = {
    "30days": 100,   # 100 Stars
    "90days": 150,   # 150 Stars
    "forever": 300   # 300 Stars
}

NAMES = {
    "30days": "Experiment Product - 30 дней",
    "90days": "Experiment Product - 90 дней",
    "forever": "Experiment Product - НАВСЕГДА"
}

# ===== КОМАНДА /start =====
@dp.message(Command("start"))
async def start(message: types.Message):
    args = message.text.split()
    
    # Если есть параметр (30days, 90days, forever) — сразу создаем инвойс
    if len(args) > 1 and args[1] in PRICES:
        sub_type = args[1]
        price = PRICES[sub_type]
        name = NAMES[sub_type]
        
        await bot.send_invoice(
            chat_id=message.chat.id,
            title=name,
            description="Доступ ко всем модулям Experiment Product",
            payload=json.dumps({
                "user_id": message.from_user.id,
                "username": message.from_user.username,
                "type": sub_type
            }),
            provider_token="",           # ⚠️ ВАЖНО: пустая строка для Stars!
            currency="XTR",              # ⚠️ ВАЖНО: именно XTR для Stars
            prices=[LabeledPrice(label=name, amount=price)],
            need_name=False,
            need_phone_number=False,
            need_email=False
        )
    else:
        # Меню выбора подписки
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="⭐ 30 дней (100 Stars)", callback_data="buy_30days")],
            [types.InlineKeyboardButton(text="⭐ 90 дней (150 Stars)", callback_data="buy_90days")],
            [types.InlineKeyboardButton(text="🔥 НАВСЕГДА (300 Stars)", callback_data="buy_forever")]
        ])
        await message.answer(
            "🌟 *Experiment Product*\n\nВыбери подписку и нажми на кнопку:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

# ===== ОБРАБОТКА КНОПОК =====
@dp.callback_query(lambda c: c.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery):
    sub_type = callback.data.replace("buy_", "")
    price = PRICES[sub_type]
    name = NAMES[sub_type]
    
    await bot.send_invoice(
        chat_id=callback.message.chat.id,
        title=name,
        description="Доступ ко всем модулям Experiment Product",
        payload=json.dumps({
            "user_id": callback.from_user.id,
            "username": callback.from_user.username,
            "type": sub_type
        }),
        provider_token="",      # Пустая строка для цифровых товаров [citation:7]
        currency="XTR",         # Обязательно XTR для Stars [citation:7]
        prices=[LabeledPrice(label=name, amount=price)]
    )
    await callback.answer()

# ===== ОБЯЗАТЕЛЬНАЯ ПРОВЕРКА ПЕРЕД ОПЛАТОЙ =====
@dp.pre_checkout_query(lambda q: True)
async def pre_checkout_query(pre_checkout_q: PreCheckoutQuery):
    # Всегда отвечаем OK для цифровых товаров [citation:7]
    await pre_checkout_q.answer(ok=True)

# ===== УСПЕШНАЯ ОПЛАТА =====
@dp.message(lambda m: m.successful_payment is not None)
async def successful_payment(message: types.Message):
    payment = message.successful_payment
    payload = json.loads(payment.invoice_payload)
    sub_type = payload["type"]
    username = payload["username"]
    
    # Отправляем запрос к твоему сайту
    import requests
    response = requests.post("https://experimentproduct.rf.gd/api/create_key.php", json={
        "username": username,
        "subscription_type": sub_type,
        "payment_id": payment.telegram_payment_charge_id
    })
    
    result = response.json()
    
    if result["success"]:
        key = result["key"]
        if sub_type == "forever":
            period = "НАВСЕГДА"
        elif sub_type == "90days":
            period = "90 дней"
        else:
            period = "30 дней"
        
        await message.answer(
            f"✅ *Оплата успешна!*\n\n"
            f"Подписка: {period}\n"
            f"⭐ {payment.total_amount} Stars\n\n"
            f"🎁 *Ваш ключ:* `{key}`\n\n"
            f"Активируйте ключ на сайте: experimentproduct.rf.gd/dashboard.php",
            parse_mode="Markdown"
        )
    else:
        await message.answer("❌ Ошибка при создании ключа. Напишите @fbikk")

# ===== ЗАПУСК =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
