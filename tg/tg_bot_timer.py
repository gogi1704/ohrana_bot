from asyncio import create_task, sleep
import resources
from db.user_history_db import *
from tg_bot_navigation import handle_to_life_questions

async def restart_user_inactivity_timers(context, update, user_id):
    await cancel_user_timers(user_id)
    resources.user_timers[user_id] = {}

    # === message_1 (если ещё не отправлено)
    if not await is_message_sent(user_id, "message_1"):
        async def message_1_timer():
            try:
                print("timer_1_start")
                await sleep(30)  # замените на 300 для реальных 5 минут
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=resources.five_minutes_text,
                    parse_mode="HTML"
                )

                dialog = await get_history_by_id(user_id)
                dialog.append(f"Консультант сказал : {resources.five_minutes_text}")
                await add_or_update_message(user_id=user_id, message="")
                await mark_message_sent(user_id, "message_1")

                # === Запускаем message_2 (если ещё не отправлено)
                if not await is_message_sent(user_id, "message_2"):
                    async def message_2_timer():
                        try:
                            print("timer_2_start")
                            await sleep(30)  # замените на 300 для реальных 5 минут
                            await handle_to_life_questions(update, context)
                            await mark_message_sent(user_id, "message_2")
                        except asyncio.CancelledError:
                            pass
                        finally:
                            resources.user_timers[user_id].pop("message_2", None)

                    resources.user_timers[user_id]["message_2"] = create_task(message_2_timer())

            except asyncio.CancelledError:
                pass
            finally:
                resources.user_timers[user_id].pop("message_1", None)

        resources.user_timers[user_id]["message_1"] = create_task(message_1_timer())

    # === Если message_1 уже отправлено, но message_2 ещё нет (в случае активности)
    elif await is_message_sent(user_id, "message_1") and not await is_message_sent(user_id, "message_2"):
        async def message_2_timer():
            try:
                print("timer_2_start (через активность)")
                await sleep(30)
                await handle_to_life_questions(update, context)
                await mark_message_sent(user_id, "message_2")
            except asyncio.CancelledError:
                pass
            finally:
                resources.user_timers[user_id].pop("message_2", None)

        resources.user_timers[user_id]["message_2"] = create_task(message_2_timer())


async def cancel_user_timers(user_id: int):
    timers = resources.user_timers.get(user_id, {})
    for name, task in timers.items():
        if task and not task.done():
            print(f"timer_cancel: {name}")
            task.cancel()
    resources.user_timers[user_id] = {}
