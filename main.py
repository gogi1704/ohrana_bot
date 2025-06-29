import asyncio

import util_funs
import re
from agents.agent_prompts import *
from agents.agents_utils import get_gpt_answer, make_vector_store, get_chunks_filtered , get_question_category
import resources
import db.user_history_db as data_base



async def init_docs():
    await get_gpt_answer("test","test")
    docs_text = util_funs.download_gdoc(url = resources.baza_answers_url_2)
    await make_vector_store(docs_text)


async def start(user_id):
    user_name = await data_base.get_user_name(user_id)
    if user_name:
        await data_base.add_or_update_message(user_id, f"Я сказал: {resources.start_text_without_name_to_dialog}")
        return user_name
    else:
        await data_base.add_user(user_id= user_id,user_name= "new_account")
        await data_base.add_or_update_message(user_id,f"Я сказал: {resources.start_text}")
        return None

async def get_hello_dialog_answer(user_id, user_say):
    dialog_text = await data_base.get_history_by_id(user_id)
    dialog_text.append(f"Пользователь сказал : {user_say}.\n")
    user_prompt = check_name_user_prompt.format(dialog="\n".join(dialog_text))
    user_name_from_dialog = await get_gpt_answer(system_prompt= check_name_system_prompt,
                                        user_prompt= user_prompt)
    print(f"Имя пользователя : {user_name_from_dialog}")
    if user_name_from_dialog == "empty":
        user_prompt = name_dialog_user_prompt.format(user_say=user_say,
                                                     dialog = "\n".join(dialog_text))
        agent_answer = await get_gpt_answer(system_prompt= name_dialog_system_prompt,
                                            user_prompt= user_prompt)

        dialog_text.append(f"Я сказал : {agent_answer}.\n")
        await data_base.add_or_update_message(user_id=user_id,
                                        message="\n".join(dialog_text))
        return agent_answer

    elif user_name_from_dialog == "name_false":
        await data_base.add_user(user_id = user_id,
                           user_name= "отказался назвать имя")
        await data_base.remove_history_by_id(user_id)
        return resources.get_state_complete_key(state= "hello")

    else:
        await data_base.add_user(user_id = user_id,
                           user_name= user_name_from_dialog)
        await data_base.add_or_update_message(user_id= user_id, message= resources.get_company_text)
        return resources.get_state_complete_key(state= "hello")

async def get_consult_answer(user_id,user_say):
    dialog_text = await data_base.get_history_by_id(user_id)
    dialog_text.append(f"Пользователь сказал : {user_say}.\n")
    question_category_dict = await get_question_category(dialog= "\n".join(dialog_text),
                                                   user_say= user_say)
    print(f"Category : {question_category_dict}")

    if question_category_dict["category"] == "company_que":
        question = question_category_dict["question"]
        if question is None:
            question = user_say

        texts_list = await get_chunks_filtered(question)
        if len(texts_list) == 0 and question_category_dict["question"] is not None:
            asyncio.create_task(data_base.add_question_without_answer_to_sheet(question))
            free_user_prompt = free_bot_user_prompt.format(dialog= "\n".join(dialog_text))
            answer = await get_gpt_answer(system_prompt= free_bot_system_prompt, user_prompt= free_user_prompt )
            consult_answer = f"#Взято_из_сети\n{answer}"

        else:
            text_to_prompt = re.sub(r'\n{2}', ' ', '\n '.join([f'\nдокумент №{i+1}\n=====================' + doc + '\n' for i, doc in enumerate(texts_list)]))
            user_prompt = consult_user_prompt.format(question=user_say,
                                                     dialog = "\n".join(dialog_text),
                                                     docs = text_to_prompt)

            consult_answer = await  get_gpt_answer(system_prompt= consult_system_prompt,
                                                    user_prompt= user_prompt)
            print(consult_answer)
            if consult_answer == "empty":
                asyncio.create_task(data_base.add_question_without_answer_to_sheet(question))
                free_user_prompt = free_bot_user_prompt.format(dialog="\n".join(dialog_text))
                answer = await get_gpt_answer(system_prompt=free_bot_system_prompt, user_prompt=free_user_prompt)

                consult_answer = f"#Взято_из_сети\n{answer}"


    elif question_category_dict["category"] == "manager_que":
        consult_answer = resources.tg_states["manager"]
        await data_base.add_or_update_message(user_id=user_id, message="\n".join(dialog_text))
        return consult_answer

    elif question_category_dict["category"] == "transfer_que":
        consult_answer = f"state: {resources.tg_states['transfer']} | date:{question_category_dict['question']}"
        await data_base.add_or_update_message(user_id=user_id, message="\n".join(dialog_text))
        return consult_answer

    else:
        consult_answer = "Error category"

    dialog_text.append(f"Консультант сказал : {consult_answer}.\n")
    await data_base.add_or_update_message(user_id= user_id,
                                    message= "\n".join(dialog_text))
    return consult_answer

async def manager_get_info(user_id, user_say):
    dialog_text = await data_base.get_history_by_id(user_id)
    dialog_text.append(f"Пользователь сказал : {user_say}.\n")
    user_prompt = manager_get_info_user_prompt.format(dialog="\n".join(dialog_text))
    manager_say = await get_gpt_answer(system_prompt=manager_get_info_system_prompt,
                                       user_prompt=user_prompt)
    if manager_say == "manager_stop":
        manager_answer = "manager_stop"
        dialog_text.clear()
        dialog_text.append(f"Консультант сказал : {resources.stop_manager_text}.\n")
    elif "manager_complete" in manager_say:
        manager_answer = manager_say
        dialog_text.clear()
        dialog_text.append(f"Консультант сказал : {resources.complete_manager_text}.\n")
    else:
        manager_answer = manager_say
        dialog_text.append(f"Консультант сказал : {manager_answer}.\n")

    await data_base.add_or_update_message(user_id= user_id,
                                    message= "\n".join(dialog_text))
    return manager_answer

async def get_prev_consult_answer(user_id,user_say):
    dialog_text = await data_base.get_history_by_id(user_id)
    dialog_text.append(f"Пользователь сказал : {user_say}.\n")
    user_prompt = prev_consult_user_prompt.format(user_say = user_say, dialog = "\n".join(dialog_text))
    prev_consult_answer = await get_gpt_answer(system_prompt= prev_consult_system_prompt,
                                               user_prompt= user_prompt)
    if prev_consult_answer == resources.get_state_complete_key(state= "prev_consult"):
        dialog_text.append(f"Консультант сказал : {resources.prev_consult_text}.")
    else:
        dialog_text.append(f"Консультант сказал : {prev_consult_answer}.\n")
    return prev_consult_answer

async def transfer_get_date(user_id, user_say):
    dialog_text = await data_base.get_history_by_id(user_id)
    dialog_text.append(f"Пользователь сказал : {user_say}.\n")
    user_prompt = transfer_get_date_user_prompt.format(dialog="\n".join(dialog_text))
    get_date_answer = await get_gpt_answer(system_prompt=transfer_get_date_system_prompt, user_prompt= user_prompt)
    parsed = util_funs.parse_transfer_response(get_date_answer)
    if parsed is not None:
        result, date = parsed

        if result == "complete":
            dialog_text.clear()
            dialog_text.append(f"Консультант сказал : {resources.transfer_complete_text}.")

        elif result == "error":
            dialog_text.clear()
            dialog_text.append(f"Консультант сказал : {resources.transfer_error_text}.\n")

    await data_base.add_or_update_message(user_id= user_id,
                                    message= "\n".join(dialog_text))
    return get_date_answer

async def get_final_question(user_id, user_say):
    dialog_text = await data_base.get_history_by_id(user_id)
    user_prompt = manager_human_create_final_user_prompt.format(dialog= "\n".join(dialog_text))
    return await get_gpt_answer(system_prompt= manager_human_create_final_question_system_prompt, user_prompt= user_prompt)

async def get_company(user_id,user_say):
    dialog_text = await data_base.get_history_by_id(user_id)
    dialog_text.append(f"Пользователь сказал : {user_say}.\n")
    user_prompt = check_company_user_prompt.format(dialog="\n".join(dialog_text))
    company_info = await get_gpt_answer(system_prompt= check_company_system_prompt,
                                        user_prompt= user_prompt)
    user_name = await data_base.get_user_name(user_id= user_id)
    print(f"Предприятие : {company_info}")
    if company_info == "empty":
        user_prompt = company_dialog_user_prompt.format(user_say=user_say,
                                                     dialog = "\n".join(dialog_text))
        agent_answer = await get_gpt_answer(system_prompt= company_dialog_system_prompt,
                                            user_prompt= user_prompt)

        dialog_text.append(f"Я сказал : {agent_answer}.\n")
        await data_base.add_or_update_message(user_id=user_id,
                                        message="\n".join(dialog_text))
        return agent_answer

    elif company_info == "company_false":
        await data_base.add_user(user_id = user_id,
                                 user_name= user_name,
                                 company= "Отказ давать данные")
        await data_base.remove_history_by_id(user_id)
        return resources.get_state_complete_key(state= "company")

    else:
        await data_base.add_user(user_id = user_id,
                                 user_name=user_name,
                                 company= company_info)
        user_name_from_dialog = await data_base.get_user_name(user_id)
        await data_base.add_or_update_message(user_id= user_id, message= f"Консультант сказал: {resources.get_first_text_after_hello_true(user_name= user_name_from_dialog)}.")
        return resources.get_state_complete_key(state= "company")

async def update_state(user_id, state):
    await data_base.update_state(user_id= user_id, state= state)
    return "ок"

async def get_state(user_id):
    state = await data_base.get_state(user_id= user_id)
    return state

# async def test_dialog():
#     init_docs()
#     get_chunks(user_question= "Где посмотреть отзывы?")
#     await data_base.init_db()
#
#
#
#
# if __name__ == "__main__":
#     asyncio.run(test_dialog())
