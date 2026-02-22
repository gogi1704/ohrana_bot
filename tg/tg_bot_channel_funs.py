from telegram.ext import ContextTypes
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from db import user_history_db

ADMIN_ID = 1106334332  # Замени на свой Telegram user_id
CHANNEL_LINK = "https://t.me/human3s"  # замени на свой канал


async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    post = update.channel_post

    if not post:
        return

    # Получаем пользователей
    user_ids = await user_history_db.get_all_user_ids()

    success_count = 0
    fail_count = 0
    failed_users = []

    # Создаем кнопку
    keyboard = [
        [InlineKeyboardButton("📢 Перейти в канал", url=CHANNEL_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Рассылка
    for user_id in user_ids:
        try:
            if post.text:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=post.text,
                    reply_markup=reply_markup
                )

            elif post.photo:
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=post.photo[-1].file_id,
                    caption=post.caption or "",
                    reply_markup=reply_markup
                )

            elif post.document:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=post.document.file_id,
                    caption=post.caption or "",
                    reply_markup=reply_markup
                )

            else:
                # если тип другой — просто пересылаем
                await context.bot.forward_message(
                    chat_id=user_id,
                    from_chat_id=post.chat_id,
                    message_id=post.message_id
                )

            success_count += 1

        except Exception as e:
            fail_count += 1
            failed_users.append((user_id, str(e)))

    # Формируем отчет
    report = (
        f"📢 Отчет о рассылке:\n"
        f"Всего получателей: {len(user_ids)}\n"
        f"✅ Успешно: {success_count}\n"
        f"❌ Ошибок: {fail_count}\n"
    )

    if failed_users:
        report += "\nСписок ошибок:\n"
        for uid, err in failed_users:
            report += f"- {uid}: {err}\n"

    # Отправляем отчет админу
    await context.bot.send_message(chat_id=ADMIN_ID, text=report)