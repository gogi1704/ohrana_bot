from telegram.ext import Application,CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from dotenv import load_dotenv
import os
from tg.tg_bot_navigation import start, handle_message, handle_manager_reply, handle_send_answer, handle_to_life_questions, handle_all_questions_buttons, handle_reply_button_pressed, handle_user_text_reply
import resources


load_dotenv()
TOKEN = os.environ.get("TG_TOKEN")
REPLY_TO_MANAGER = range(1)


def main():
    application = Application.builder().token(TOKEN).concurrent_updates(True).build()
    print('Бот запущен...')

    start_handler = CommandHandler('start', start, block=False)

    text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message, block=False)
    manager_handler = MessageHandler(filters.Chat(int(resources.GROUP_CHAT_ID)) & filters.REPLY, handle_manager_reply)
    button_to_life_question_handler = MessageHandler(filters.TEXT & filters.Regex("^Житейские вопросы$"), handle_to_life_questions)

    button_send_answer_handler = CallbackQueryHandler(handle_send_answer, pattern=r"^send_answer\|")
    buttons_all_life_questions_handler = CallbackQueryHandler(handle_all_questions_buttons)

    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(handle_reply_button_pressed, pattern=r"^reply_to_manager\|")
        ],
        states={
            REPLY_TO_MANAGER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_text_reply)],
        },
        fallbacks=[],
    )


    # exit_button_handler = MessageHandler(filters.TEXT & filters.Regex("^Выйти из режима$"), handle_exit_from_keyboard)
    # to_question_button_handler = MessageHandler(filters.TEXT & filters.Regex("^Задать вопрос менеджеру$"), handle_to_question_from_keyboard)

    # application.add_handler(exit_button_handler)
    # application.add_handler(to_question_button_handler)


    # application.add_handler(buttons_life_questions_handler)

    application.add_handler(start_handler)

    application.add_handler(conv_handler)

    application.add_handler(button_send_answer_handler)
    application.add_handler(buttons_all_life_questions_handler)

    application.add_handler(button_to_life_question_handler)
    application.add_handler(manager_handler)
    application.add_handler(text_handler)


    application.run_polling()
    print('Бот остановлен')


if __name__ == "__main__":
    main()