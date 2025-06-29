from telegram.ext import Application,CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from dotenv import load_dotenv
import os
from tg.tg_bot_navigation import start, handle_message, handle_manager_reply, handle_send_answer, handle_to_life_questions, handle_all_questions_buttons, handle_reply_button_pressed, handle_user_text_reply, handle_web_app_data
import resources
from tg.tg_bot_navigation_make_prof_list import *


load_dotenv()
TOKEN = os.environ.get("TG_TOKEN")
REPLY_TO_MANAGER = range(1)
(
    ASK_MEN,
    ASK_MEN_40,
    ASK_WOMEN,
    ASK_WOMEN_40,
    SHOW_SUMMARY,
    WAIT_PROFESSION,
    WAIT_PROF_COUNT,
    PROFESSION_MENU
) = range(8)


def main():
    application = Application.builder().token(TOKEN).concurrent_updates(True).build()
    print('Бот запущен...')

    start_handler = CommandHandler('start', start, block=False)

    text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message, block=False)
    manager_handler = MessageHandler(filters.Chat(int(resources.GROUP_CHAT_ID)) & filters.REPLY, handle_manager_reply)
    button_to_life_question_handler = MessageHandler(filters.TEXT & filters.Regex("^Житейские вопросы$"), handle_to_life_questions)

    button_send_answer_handler = CallbackQueryHandler(handle_send_answer, pattern=r"^send_answer\|")
    buttons_all_life_questions_handler = CallbackQueryHandler(handle_all_questions_buttons)
    web_app_handler = MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data)
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(handle_reply_button_pressed, pattern=r"^reply_to_manager\|")
        ],
        states={
            REPLY_TO_MANAGER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_text_reply)],
        },
        fallbacks=[],
    )

    conv_handler_make_prof_list = ConversationHandler(
        entry_points=[CommandHandler("make_prof_list", start_make_list)],
        states={
            ASK_MEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_men_40)],
            ASK_MEN_40: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_women)],
            ASK_WOMEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_women_40)],
            ASK_WOMEN_40: [MessageHandler(filters.TEXT & ~filters.COMMAND, show_summary)],
            SHOW_SUMMARY: [CallbackQueryHandler(proceed_to_profession, pattern="^next$")],
            WAIT_PROFESSION: [MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_profession)],
            WAIT_PROF_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_profession_count)],
            PROFESSION_MENU: [CallbackQueryHandler(profession_menu_handler)]
        },
        fallbacks=[MessageHandler(filters.TEXT & filters.Regex(f"^{CANCEL}$"), cancel)]
    )

    application.add_handler(conv_handler_make_prof_list)


    application.add_handler(start_handler)
    application.add_handler(web_app_handler)

    application.add_handler(conv_handler)
    application.add_handler(conv_handler_make_prof_list)

    application.add_handler(button_send_answer_handler)
    application.add_handler(buttons_all_life_questions_handler)

    application.add_handler(button_to_life_question_handler)
    application.add_handler(manager_handler)
    application.add_handler(text_handler)


    application.run_polling()
    print('Бот остановлен')


if __name__ == "__main__":
    main()