import resources
import util_funs
from resources import tg_states , get_state_complete_key, get_url_by_command
from util_funs import send_request, highlight
from telegram import Update,  Message
from db.user_history_db import save_message_link, get_user_id_by_group_message, get_user_name, remove_history_by_id, delete_user_questions, delete_last_button, get_last_button, save_last_button
from telegram.ext import (ContextTypes)
from telegram.constants import ChatAction
from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio

# to_question_keyboard = ReplyKeyboardMarkup(
#     [[KeyboardButton("Задать вопрос менеджеру")]],
#     resize_keyboard=True,
#     one_time_keyboard=False  # Кнопка остаётся, пока не сменится состояние
#     )

# exit_keyboard = ReplyKeyboardMarkup(
#     [[KeyboardButton("Выйти из режима")]],
#     resize_keyboard=True,
#     one_time_keyboard=False  # Кнопка остаётся, пока не сменится состояние
#     )

# async def handle_to_question_from_keyboard(update, context):
#     user_id = update.message.from_user.id
#     await send_request(get_url_by_command("update_state"), {"user_id": user_id, "state": tg_states['manager_human']})
#     await remove_history_by_id(user_id)
#     await delete_user_questions(user_id)
#
#     await update.message.reply_text(
#         "Я помогу вам составить вопрос к нашему менеджеру. Если мне покажется , что вопрос будет не до конца понятен моему старшему менеджеру, то я могу уточнить некоторые моменты.Если вы не хотите задавать вопрос , то так и напишите или нажмите на соответствующую кнопку. Жду ваш вопрос...",
#         reply_markup= exit_keyboard
#     )


# async def handle_exit_from_keyboard(update, context):
#     await start(update, context)


async def start(update, context)->int:
    user_id = update.message.from_user.id
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
            # await update.message.reply_text(answer, reply_markup= to_question_keyboard )
            await update.message.reply_text(answer)
        elif update.callback_query:
            # await update.callback_query.message.reply_text(answer, reply_markup= to_question_keyboard )
            await update.callback_query.message.reply_text(answer)

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

    elif current_state == tg_states['prev_consult']:
        await handle_prev_consult(update, context, payload, user_id)

    elif current_state == tg_states['consult']:
        await handle_consult(update, context, payload, user_id)

    elif current_state == tg_states['manager']:
        await handle_manager(update, context, payload, user_id)

    elif current_state == tg_states['transfer']:
        await handle_transfer(update, context, payload, user_id)

    elif current_state == tg_states['manager_human']:
        await handle_manager_human(update, context, payload, user_id)


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
        await send_request(get_url_by_command("update_state"), {"user_id": user_id, "state": tg_states['prev_consult']})
        text = resources.get_first_text_after_hello_true(user_name=user_name)
    await context.bot.send_message(chat_id=update.effective_chat.id, text= text)

async def handle_prev_consult(update, context, payload,user_id) -> int:
    text = await send_request(url=get_url_by_command(api_command= "get_prev_consult" ),
                              payload=payload)
    if text == get_state_complete_key(state="prev_consult"):
        await send_request(get_url_by_command("update_state"), {"user_id": user_id, "state": tg_states['consult']})
        text = resources.prev_consult_text
    await context.bot.send_message(chat_id=update.effective_chat.id, text= text)

async def handle_consult(update, context, payload,user_id) -> int:
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
            message_text = f"Обращение.\nПользователь: {user_name}.\nКак связаться: {contact}."
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
        result = f"{text}\n\n{highlight(text= 'Ответ сформирован с помощью сети интернет. Если вы не доверяете этому ответу , и хотите получить информацию от нашего менеджера, то нажмите соответствующую кнопку.',
                                        style= 'italic',
                                        mode= 'HTML')}"

        sent = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=result,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        await save_last_button(user_id, sent.message_id, result)

        # await с конпкой
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

async def handle_manager(update, context, payload,user_id) -> int:
    text = await send_request(url=get_url_by_command(api_command="manager"),
                              payload=payload)
    print(text)
    if "manager_complete" in text:
        await send_request(get_url_by_command("update_state"), {"user_id": user_id, "state": tg_states['consult']})
        user_name = await get_user_name(user_id=int(user_id))
        contact = util_funs.parse_manager_response(text)
        message_text = f"#Обращение.\nПользователь: {user_name}.\nКак связаться: {contact}."
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
            message_text = f"Возможна ли дата приезда.\nПользователь: {user_name}.\nО каких датах речь: {date}."
            await send_to_chat(update, context, message_text)
            text = resources.transfer_complete_text
        elif result == "error":
            await send_request(get_url_by_command("update_state"), {"user_id": user_id, "state": tg_states['consult']})
            text = resources.transfer_error_text

    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

async def handle_manager_human(update, context, payload,user_id) -> int:
    text = await send_request(url=get_url_by_command(api_command="manager_human_dialog"),
                              payload=payload)

    if text == "que_exit":
        await send_request(get_url_by_command("update_state"), {"user_id": user_id, "state": tg_states['consult']})
        text = resources.human_manager_exit_text
        # await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=to_question_keyboard)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

    elif text == "que_complete":
        await send_request(get_url_by_command("update_state"), {"user_id": user_id, "state": tg_states['consult']})
        final_question = await send_request(get_url_by_command("get_final_question"), payload= payload)
        user_name = await get_user_name(user_id=int(user_id))
        text_to_chat = f"#Вопрос\nПользователь:\nId пользователя- {user_id}\nИмя пользователя- {user_name}.\n\nВопрос: {final_question}"
        await send_to_chat(update, context, text_to_chat)
        text = resources.human_manager_complete_text
        # await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=to_question_keyboard)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

async def handle_send_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    answer = f"Диалог_с_{user_id}\nИмя пользователя: {user_name}\n\n{text_answer}"
    # Формируем payload и получаем финальный вопрос
    payload = {
        "text_answer": text_answer,
        "user_id": user_id
    }

    question = await send_request(
        url=get_url_by_command("get_final_question"),
        payload=payload
    )

    # Отправляем в групповой чат
    await send_to_chat(update, context, question)

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
        await context.bot.send_message(
            chat_id=user_id,
            text=f"📩 Ответ от менеджера:\n\n{update.message.text}"
        )
        await update.message.reply_text("✅ Ответ отправлен пользователю.")
    else:
        await update.message.reply_text("⚠️ Не удалось найти пользователя по сообщению.")