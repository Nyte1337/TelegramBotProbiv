import os
import logging
import requests
from dotenv import load_dotenv
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    CallbackContext
)

# Настройка
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
NUMVERIFY_API_KEY = os.getenv("NUMVERIFY_API_KEY")  # Ключ от NumVerify

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Клавиатуры
def main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🔍 Проверить Telegram")],
        [KeyboardButton("📞 Проверить номер")],
        [KeyboardButton("ℹ️ Помощь")]
    ], resize_keyboard=True)

def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
    ])

# Проверка Telegram-аккаунта
async def check_telegram(update: Update, context: CallbackContext, query: str):
    try:
        if query.startswith('@'):
            user = await context.bot.get_chat(query)
        else:
            try:
                user_id = int(query)
                user = await context.bot.get_chat(user_id)
            except ValueError:
                await update.message.reply_text("❌ Введите корректный username (@user) или ID")
                return

        info = (
            f"👤 <b>Информация об аккаунте:</b>\n\n"
            f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
            f"👁 <b>Имя:</b> {user.first_name or '❌'}\n"
            f"📌 <b>Фамилия:</b> {user.last_name or '❌'}\n"
            f"🔗 <b>Username:</b> @{user.username or '❌'}\n"
            f"🌐 <b>Язык:</b> {user.language_code or '❌'}\n"
            f"🤖 <b>Бот:</b> {'✅' if user.is_bot else '❌'}\n"
            f"⭐ <b>Премиум:</b> {'✅' if user.is_premium else '❌'}"
        )

        try:
            photos = await context.bot.get_user_profile_photos(user.id, limit=1)
            if photos.photos:
                photo_file = await photos.photos[0][-1].get_file()
                await update.message.reply_photo(
                    photo=photo_file.file_id,
                    caption=info,
                    parse_mode='HTML',
                    reply_markup=back_keyboard()
                )
                return
        except Exception as e:
            logger.error(f"Ошибка при получении фото: {e}")

        await update.message.reply_text(info, parse_mode='HTML', reply_markup=back_keyboard())

    except Exception as e:
        logger.error(f"Ошибка проверки Telegram: {e}")
        await update.message.reply_text(
            "❌ Пользователь не найден или данные скрыты",
            reply_markup=back_keyboard()
        )

# Проверка номера через NumVerify
async def check_phone(update: Update, phone: str):
    if not NUMVERIFY_API_KEY:
        await update.message.reply_text("❌ API ключ для номеров не настроен")
        return

    try:
        response = requests.get(
            f"http://apilayer.net/api/validate?access_key={NUMVERIFY_API_KEY}&number={phone}"
        )
        data = response.json()

        if data.get('valid'):
            info = (
                f"📞 <b>Информация о номере:</b>\n\n"
                f"🔢 <b>Номер:</b> {phone}\n"
                f"🌍 <b>Страна:</b> {data.get('country_name', '❌')}\n"
                f"🏢 <b>Оператор:</b> {data.get('carrier', '❌')}\n"
                f"📟 <b>Тип:</b> {data.get('line_type', '❌')}\n"
                f"🌐 <b>Код страны:</b> +{data.get('country_code', '❌')}\n"
                f"✅ <b>Валидность:</b> {'Да' if data['valid'] else 'Нет'}"
            )
            await update.message.reply_text(info, parse_mode='HTML', reply_markup=back_keyboard())
        else:
            await update.message.reply_text(
                "❌ Номер недействителен или API недоступен",
                reply_markup=back_keyboard()
            )

    except Exception as e:
        logger.error(f"Ошибка проверки номера: {e}")
        await update.message.reply_text(
            "❌ Ошибка при проверке номера",
            reply_markup=back_keyboard()
        )

# Команды бота
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "🔍 <b>Бот для проверки:</b>\n\n"
        "• Telegram-аккаунтов\n"
        "• Номеров телефонов\n\n"
        "Выберите действие:",
        reply_markup=main_keyboard(),
        parse_mode='HTML'
    )

async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "📌 <b>Инструкция:</b>\n\n"
        "1. Для проверки <b>Telegram</b> отправьте:\n"
        "   • @username\n"
        "   • ID пользователя\n\n"
        "2. Для проверки <b>номера</b> введите:\n"
        "   • +79123456789\n\n"
        "Используется API NumVerify",
        parse_mode='HTML'
    )

async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text.strip()

    if text == "🔍 Проверить Telegram":
        await update.message.reply_text("Введите @username или ID пользователя:")
    
    elif text == "📞 Проверить номер":
        await update.message.reply_text("Введите номер телефона (+79123456789):")
    
    elif text == "ℹ️ Помощь":
        await help_command(update, context)
    
    elif text.startswith("@"):
        await check_telegram(update, context, text)
    
    elif text.startswith("+"):
        await check_phone(update, text)
    
    else:
        await update.message.reply_text("❌ Некорректный ввод. Нажмите /help")

async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_to_main":
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(
            "Выберите действие:",
            reply_markup=main_keyboard()
        )

# Запуск бота
def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    app.run_polling()

if __name__ == "__main__":
    main()
