from telegram.ext import ContextTypes
from telegram import Update
from db import user_history_db

ADMIN_ID = 1106334332  # Замени на свой Telegram user_id

async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    post = update.channel_post

    # Получаем всех пользователей из базы
    user_ids = await user_history_db.get_all_user_ids()

    success_count = 0
    fail_count = 0
    failed_users = []

    # Рассылка сообщений
    for user_id in user_ids:
        try:
            if post.text:
                await context.bot.send_message(chat_id=user_id, text=post.text)
            elif post.photo:
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=post.photo[-1].file_id,
                    caption=post.caption or ""
                )
            elif post.document:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=post.document.file_id,
                    caption=post.caption or ""
                )
            else:
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
        report += "\nСписок неудачных отправок:\n"
        for uid, err in failed_users:
            report += f"- {uid}: {err}\n"

    # Отправляем отчет администратору
    await context.bot.send_message(chat_id=ADMIN_ID, text=report)