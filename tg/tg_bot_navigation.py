import resources
import util_funs
from resources import tg_states , get_state_complete_key, get_url_by_command, api_commands
from util_funs import send_request
from telegram import Update,  Message
from db.user_history_db import save_message_link, get_user_id_by_group_message, get_user_name
from telegram.ext import (ContextTypes)
from telegram.constants import ChatAction


async def start(update, context)->int:
    user_id = update.message.from_user.id
    payload = {"text_answer":"ok",
               "user_id":user_id
               }
    text = await send_request(url=get_url_by_command(api_command= "start") , payload= payload)

    if text == "empty":
        await send_request(get_url_by_command("update_state"), {"user_id": user_id, "state": tg_states['hello']})
        answer = resources.start_text
    else:
        await send_request(get_url_by_command("update_state"), {"user_id": user_id, "state": tg_states['consult']})
        answer = resources.get_start_text_with_name(user_name= text)

    if update.message:
        await update.message.reply_text(answer)
    elif update.callback_query:
        await update.callback_query.message.reply_text(answer)


async def handle_message(update, context) -> int:
    text_message = update.message.text
    user_id = update.message.from_user.id
    payload = {"text_answer": text_message,
               "user_id": user_id
               }
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    # Получаем текущее состояние пользователя с сервера
    current_state = await send_request(get_url_by_command("get_state"), {"user_id": user_id, "state": "empty"})

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

    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

async def handle_manager(update, context, payload,user_id) -> int:
    text = await send_request(url=get_url_by_command(api_command="manager"),
                              payload=payload)
    print(text)
    if "manager_complete" in text:
        await send_request(get_url_by_command("update_state"), {"user_id": user_id, "state": tg_states['consult']})
        user_name = await get_user_name(user_id=int(user_id))
        contact = util_funs.parse_manager_response(text)
        message_text = f"Обращение.\nПользователь: {user_name}.\nКак связаться: {contact}."
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