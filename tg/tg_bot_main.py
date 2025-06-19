from telegram.ext import Application,CommandHandler, MessageHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv
import os
from tg.tg_bot_navigation import start, handle_message, handle_manager_reply, handle_send_answer
import resources


load_dotenv()
TOKEN = os.environ.get("TG_TOKEN")


def main():
    application = Application.builder().token(TOKEN).concurrent_updates(True).build()
    print('Бот запущен...')

    start_handler = CommandHandler('start', start, block=False)
    text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message, block=False)
    manager_handler = MessageHandler(filters.Chat(int(resources.GROUP_CHAT_ID)) & filters.REPLY, handle_manager_reply)

    send_answer_handler = CallbackQueryHandler(handle_send_answer, pattern=r"^send_answer\|")
    # exit_button_handler = MessageHandler(filters.TEXT & filters.Regex("^Выйти из режима$"), handle_exit_from_keyboard)
    # to_question_button_handler = MessageHandler(filters.TEXT & filters.Regex("^Задать вопрос менеджеру$"), handle_to_question_from_keyboard)

    # application.add_handler(exit_button_handler)
    # application.add_handler(to_question_button_handler)
    application.add_handler(send_answer_handler)

    application.add_handler(manager_handler)
    application.add_handler(text_handler)
    application.add_handler(start_handler)


    application.run_polling()
    print('Бот остановлен')


if __name__ == "__main__":
    main()