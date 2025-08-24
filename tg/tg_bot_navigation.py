import resources
import util_funs
from resources import tg_states , get_state_complete_key, get_url_by_command
from util_funs import send_request, highlight
from telegram import Update,  Message
from db.user_history_db import save_message_link, get_user_id_by_group_message, get_user_name, delete_last_button, get_last_button, save_last_button, get_life_que_keyboard , save_life_que_keyboard , save_user_reply_state, get_user_reply_state, delete_user_reply_state, save_user_entry
from telegram.ext import (ContextTypes, ConversationHandler)
from telegram.constants import ChatAction
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from tg import tg_keyboards as keyboards
import asyncio
from tg import tg_bot_timer as tg_timer

REPLY_TO_MANAGER = range(1)

to_life_question_keyboard = ReplyKeyboardMarkup(
    keyboards.base_keyboard_to_life_question,
    resize_keyboard=True,
    one_time_keyboard=False  # Кнопка остаётся, пока не сменится состояние
    )

life_categories_question_keyboard = InlineKeyboardMarkup(keyboards.inline_keyboard_categories_life_questions)

async def start(update, context)->int:
    user_id = update.effective_user.id
    payload = {"text_answer":"ok",
               "user_id":user_id
               }

    text = await send_request(url=get_url_by_command(api_command= "start") , payload= payload)

    if text == "empty":
        await send_request(get_url_by_command("update_state"), {"user_id": user_id, "state": tg_states['hello']})
        answer = resources.start_text
        if update.message:
            await update.message.reply_text(answer)
        elif update.callback_query:
            await update.callback_query.message.reply_text(answer)

    else:
        await send_request(get_url_by_command("update_state"), {"user_id": user_id, "state": tg_states['consult']})
        answer = resources.get_start_text_with_name(user_name= text)

        if update.message:
            await update.message.reply_text(answer, reply_markup=to_life_question_keyboard)
        elif update.callback_query:
            await update.callback_query.message.reply_text(answer, reply_markup=to_life_question_keyboard)

    args = context.args  # Здесь будут параметры после /start
    utm_code = args[0] if args else None
    print(utm_code)
    if utm_code is not None:
        await save_user_entry(user_id, utm_code)


async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.web_app_data:
        data = update.message.web_app_data.data
        print("📨 Получены данные из WebApp:", data)
        await update.message.reply_text(f"Вы выбрали: {data}")

async def handle_message(update, context) -> int:
    text_message = update.message.text
    user_id = update.message.from_user.id
    payload = {"text_answer": text_message,
               "user_id": user_id
               }
    asyncio.create_task(
        context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    )
    # Получаем текущее состояние пользователя с сервера
    current_state = await send_request(get_url_by_command("get_state"), {"user_id": user_id, "state": "empty"})

    last_button = await get_last_button(user_id)
    if last_button:
        message_id, _ = last_button
        try:
            await context.bot.edit_message_reply_markup(
                chat_id=update.effective_chat.id,
                message_id=message_id,
                reply_markup=None
            )
        except Exception as e:
            print(f"❌ Не удалось удалить кнопку: {e}")
        await delete_last_button(user_id)

    if current_state == tg_states['hello']:
        await handle_hello(update, context, payload, user_id)

    elif current_state == tg_states['company']:
        await handle_company(update, context, payload, user_id)

    # elif current_state == tg_states['prev_consult']:
    #     await handle_prev_consult(update, context, payload, user_id)

    elif current_state == tg_states['consult']:
        await handle_consult(update, context, payload, user_id)

    elif current_state == tg_states['manager']:
        await handle_manager(update, context, payload, user_id)

    elif current_state == tg_states['transfer']:
        await handle_transfer(update, context, payload, user_id)

    # elif current_state == tg_states['manager_human']:
    #     await handle_manager_human(update, context, payload, user_id)


async def handle_hello(update, context, payload,user_id) -> int:
    text = await send_request(url=get_url_by_command(api_command="hello_dialog"),
                              payload=payload)
    user_name = await get_user_name(user_id= int(user_id))

    if text == get_state_complete_key(state="hello"):
        await send_to_chat_user_in_bot(context= context,user_name= user_name,user_id = user_id)
        await send_request(get_url_by_command("update_state"), {"user_id": user_id, "state": tg_states['company']})
        text = resources.get_company_text

    await context.bot.send_message(chat_id=update.effective_chat.id, text= text)

async def handle_company(update, context, payload,user_id) -> int:
    text = await send_request(url=get_url_by_command(api_command= "get_company" ),
                              payload=payload)
    user_name = await get_user_name(user_id=int(user_id))

    if text == get_state_complete_key(state="company"):
        await send_request(get_url_by_command("update_state"), {"user_id": user_id, "state": tg_states['consult']})
        await tg_timer.restart_user_inactivity_timers(update= update, context= context, user_id= user_id)
        text = resources.get_first_text_after_hello_true(user_name=user_name)
    await context.bot.send_message(chat_id=update.effective_chat.id, text= text)

# async def handle_prev_consult(update, context, payload,user_id) -> int:
#     text = await send_request(url=get_url_by_command(api_command= "get_prev_consult" ),
#                               payload=payload)
#     if text == get_state_complete_key(state="prev_consult"):
#         await send_request(get_url_by_command("update_state"), {"user_id": user_id, "state": tg_states['consult']})
#         text = resources.prev_consult_text
#     await context.bot.send_message(chat_id=update.effective_chat.id, text= text)

async def handle_consult(update, context, payload,user_id) -> int:
    await tg_timer.restart_user_inactivity_timers(update= update, context= context, user_id= user_id)
    text = await send_request(url=get_url_by_command(api_command="get_consult"),
                              payload=payload)
    if text == tg_states["manager"]:
        await send_request(get_url_by_command("update_state"), {"user_id": user_id, "state": tg_states['manager']})
        text = await send_request(url=get_url_by_command(api_command="manager"),
                                  payload=payload)

        if "manager_complete" in text:
            await send_request(get_url_by_command("update_state"), {"user_id": user_id, "state": tg_states['consult']})
            user_name = await get_user_name(user_id=int(user_id))
            contact = util_funs.parse_manager_response(text)
            message_text = f"#Диалог_с_{user_id}\nИмя пользователя: {user_name}\n\nКак связаться:{contact}"
            await send_to_chat(update, context, message_text)
            text = resources.complete_manager_text

    elif tg_states["transfer"] in text:
        await send_request(url= get_url_by_command(api_command="update_state"),
                           payload= {"user_id": user_id, "state": tg_states['transfer']})
        text = await send_request(url = get_url_by_command(api_command="transfer"),
                                  payload=payload)

    if text.startswith("#Взято_из_сети"):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Отправить менеджеру", callback_data=f"send_answer|{user_id}")]
        ])
        comment = highlight(
            text="Ответ сформирован с помощью сети интернет. Если вы не доверяете этому ответу, и хотите получить информацию от нашего менеджера, то нажмите соответствующую кнопку.",
            style="italic",
            mode="HTML"
        )

        result = f"{text}\n\n{comment}"

        sent = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=result,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        await save_last_button(user_id, sent.message_id, result)

    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup= to_life_question_keyboard)

async def handle_manager(update, context, payload,user_id) -> int:
    text = await send_request(url=get_url_by_command(api_command="manager"),
                              payload=payload)
    print(text)
    if "manager_complete" in text:
        await send_request(get_url_by_command("update_state"), {"user_id": user_id, "state": tg_states['consult']})
        user_name = await get_user_name(user_id=int(user_id))
        contact = util_funs.parse_manager_response(text)
        message_text = f"#Диалог_с_{user_id}\nИмя пользователя: {user_name}\n\nКак связаться:{contact}"
        await send_to_chat(update,context,message_text)
        text = resources.complete_manager_text

    elif text == "manager_stop":
        await send_request(get_url_by_command("update_state"), {"user_id": user_id, "state": tg_states['consult']})
        text = resources.stop_manager_text

    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

async def handle_transfer(update, context, payload,user_id) -> int:
    text = await send_request(url=get_url_by_command(api_command="transfer"),
                              payload=payload)
    parsed = util_funs.parse_transfer_response(text)
    if parsed is not None:
        result, date = parsed

        if result == "complete":
            await send_request(get_url_by_command("update_state"), {"user_id": user_id, "state": tg_states['consult']})
            user_name = await get_user_name(user_id=int(user_id))
            message_text = f"#Диалог_с_{user_id}\nВозможна ли дата приезда.\nИмя пользователя: {user_name}.\nО каких датах речь: {date}."
            await send_to_chat(update, context, message_text)
            text = resources.transfer_complete_text
        elif result == "error":
            await send_request(get_url_by_command("update_state"), {"user_id": user_id, "state": tg_states['consult']})
            text = resources.transfer_error_text

    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

# async def handle_manager_human(update, context, payload,user_id) -> int:
#     text = await send_request(url=get_url_by_command(api_command="manager_human_dialog"),
#                               payload=payload)

    if text == "que_exit":
        await send_request(get_url_by_command("update_state"), {"user_id": user_id, "state": tg_states['consult']})
        text = resources.human_manager_exit_text
        # await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=to_question_keyboard)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    elif text == "que_complete":
        await send_request(get_url_by_command("update_state"), {"user_id": user_id, "state": tg_states['consult']})
        final_question = await send_request(get_url_by_command("get_final_question"), payload= payload)
        user_name = await get_user_name(user_id=int(user_id))
        text_to_chat = f"#Диалог_с_{user_id}\nИмя пользователя: {user_name}.\n\nВопрос: {final_question}"
        await send_to_chat(update, context, text_to_chat)
        text = resources.human_manager_complete_text
        # await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=to_question_keyboard)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


async def handle_send_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    asyncio.create_task(
        context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    )
    query = update.callback_query
    await query.answer()

    # Извлечь user_id из callback_data
    data = query.data
    _, user_id = data.split("|")
    user_id = int(user_id)
    user_name = await get_user_name(user_id)
    # Получить текст вопроса из базы
    last_button = await get_last_button(user_id)
    if not last_button:
        await query.edit_message_text("Произошла ошибка. Не удалось найти текст вопроса.")
        return

    message_id, text_answer = last_button
    # Формируем payload и получаем финальный вопрос
    payload = {
        "text_answer": text_answer,
        "user_id": user_id
    }

    question = await send_request(
        url=get_url_by_command("get_final_question"),
        payload=payload
    )
    final_text = f"#Диалог_с_{user_id}\nИмя пользователя: {user_name}\n\n{question}"
    # Отправляем в групповой чат
    await send_to_chat(update, context, final_text)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Отправлено)")

    # Удаляем кнопку
    await query.edit_message_reply_markup(reply_markup=None)

    # Удаляем запись из базы
    await delete_last_button(user_id)

async def send_to_chat(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text):
    user = update.effective_user
    sent: Message = await context.bot.send_message(chat_id= resources.GROUP_CHAT_ID, text=message_text)

    # Сохраняем связь между сообщением в группе и пользователем
    await save_message_link(sent.message_id, user.id)

async def send_to_chat_user_in_bot(context: ContextTypes.DEFAULT_TYPE, user_name, user_id):
    text = f"👤 Пользователь: {user_name} (ID: {user_id})\n  Посетил бот."

    # Отправляем сообщение в группу
    sent: Message = await context.bot.send_message(chat_id= resources.GROUP_CHAT_ID, text=text)

    # Сохраняем связь между сообщением в группе и пользователем
    await save_message_link(sent.message_id, user_id)

async def manager_from_chat_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return

    group_message_id = update.message.reply_to_message.message_id
    user_id = await get_user_id_by_group_message(group_message_id)

    if user_id:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"📩 Ответ от менеджера:\n{update.message.text}"
        )
    else:
        await update.message.reply_text("⚠️ Не удалось найти пользователя, связанного с этим сообщением.")

async def handle_manager_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Это не ответ на сообщение.")
        return

    # Получаем ID сообщения, на которое отвечает менеджер
    group_message_id = update.message.reply_to_message.message_id

    # Ищем связанного пользователя
    user_id = await get_user_id_by_group_message(group_message_id)

    if user_id:
        # Отправляем ответ менеджера пользователю
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("✉ Нажми чтобы ответить", callback_data=f"reply_to_manager|{update.message.message_id}")]]
        )

        await context.bot.send_message(
            chat_id=user_id,
            text=f"📩 Ответ от менеджера:\n\n{update.message.text}",
            reply_markup = reply_markup
        )
        await update.message.reply_text("✅ Ответ отправлен пользователю.")
    else:
        await update.message.reply_text("⚠️ Не удалось найти пользователя по сообщению.")


async def handle_reply_button_pressed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, manager_msg_id = query.data.split("|")
    user_id = query.from_user.id

    # ✅ Удаляем inline-кнопку из сообщения
    try:
        await context.bot.edit_message_reply_markup(
            chat_id=query.message.chat.id,
            message_id=query.message.message_id,
            reply_markup=None
        )
    except Exception as e:
        print(f"⚠️ Не удалось удалить кнопку: {e}")

    await save_user_reply_state(user_id, int(manager_msg_id))

    await context.bot.send_message(
        chat_id=user_id,
        text="✍️ Введите ваш ответ менеджеру:"
    )

    return REPLY_TO_MANAGER


async def handle_user_text_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    manager_msg_id = await get_user_reply_state(user_id)

    if not manager_msg_id:
        await update.message.reply_text("⚠️ Ошибка. Попробуйте начать заново.")
        return ConversationHandler.END

    await delete_user_reply_state(user_id)
    await send_to_chat(update, context, message_text= f"#Диалог_с_{user_id}\n📨Сказал:\n\n{text}")

    await update.message.reply_text("✅ Ваш ответ отправлен менеджеру.")
    return ConversationHandler.END



async def handle_all_questions_buttons(update, context):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()
    data = query.data

    # Кнопки категорий
    if data in keyboards.CATEGORY_KEYBOARDS:
        await query.edit_message_text(
            text="⬇️Выберите вопрос⬇️",
            reply_markup=InlineKeyboardMarkup(keyboards.CATEGORY_KEYBOARDS[data])
        )
        await save_life_que_keyboard(user_id, data)
        return

    # Выход из раздела
    if data == "btn_life_exit":
        try:
            await query.message.delete()
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")
        await start(update, context)
        return

    # Назад в список категорий
    if data == "btn_back_from_life_question":
        try:
            await query.message.delete()
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")
        await handle_to_life_questions(update, context)
        return

    # Ответ на конкретный вопрос
    if data in keyboards.QUESTION_DATA:
        text = keyboards.QUESTION_DATA[data]
        category = await get_life_que_keyboard(user_id)
        keyboard = keyboards.CATEGORY_KEYBOARDS.get(category)
        if keyboard:
            await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

async def handle_to_life_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id  # Работает и для сообщений, и для кнопок

    keyboard = life_categories_question_keyboard

    # Если это обычное сообщение — лучше ответить на него
    if update.message:
        await update.message.reply_text(resources.ten_minutes_text, reply_markup=keyboard)

    # Если это callback кнопка — отправим новое сообщение (или можно редактировать старое)
    elif update.callback_query:
        await context.bot.send_message(chat_id=chat_id, text=resources.ten_minutes_text, reply_markup=keyboard)