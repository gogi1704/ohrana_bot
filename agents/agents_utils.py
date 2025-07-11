import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
import util_funs
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from agents import agent_prompts
import db.user_history_db as db

load_dotenv()

model_gpt4o_mini = "gpt-4.1-mini-2025-04-14"
model_gpt_4o = "gpt-4o-2024-08-06"
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
def update_openai_api_key(new_key: str, env_path: str = env_path):
    # Обновляем .env файл
    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    found = False
    for i, line in enumerate(lines):
        if line.startswith("OPENAI_API_KEY="):
            lines[i] = f"OPENAI_API_KEY={new_key}\n"
            found = True
            break
    if not found:
        lines.append(f"\nOPENAI_API_KEY={new_key}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    # Обновляем переменную окружения в процессе Python
    os.environ["OPENAI_API_KEY"] = new_key


async def call_openai_with_auto_key(system_prompt, user_prompt,client, model = model_gpt4o_mini):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    try:
        completion = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(e)
        return "error"

async def get_question_category(dialog, user_say):
    user_prompt = agent_prompts.check_category_question_user_prompt.format(dialog= dialog, user_say= user_say)
    category_json = await get_gpt_answer(system_prompt= agent_prompts.check_category_question_system_prompt,
                                user_prompt= user_prompt)
    print(category_json)
    return util_funs.parse_category_json(category_json)

async def make_vector_store(document_text):
    chunks = util_funs.split_qa_pairs(document_text)
    docs = [Document(page_content=chunk, metadata={"source": "baza"}) for chunk in chunks]
    embedding_model = OpenAIEmbeddings()
    vector_store = FAISS.from_documents(docs, embedding_model)
    vector_store.save_local("baza_answers")

def get_vector_store():
    embedding_model = OpenAIEmbeddings()
    return FAISS.load_local("baza_answers", embeddings=embedding_model,allow_dangerous_deserialization=True)

def get_chunks(user_question, chunks_count= 3):
    vector_store = get_vector_store()
    docs = vector_store.similarity_search(user_question, k=chunks_count)
    context = "\n\n".join([doc.page_content for doc in docs])


async def get_chunks_filtered(user_question: str):
    vector_store = get_vector_store()
    results = vector_store.similarity_search_with_score(user_question, k=6)  # k - количество топ-результатов
    threshold = 0.3
    filtered_chunks = [doc.page_content for doc, score in results if score < threshold]
    return filtered_chunks


async def get_gpt_answer(system_prompt, user_prompt):
    keys = await db.get_active_keys()
    answer = "api_error_Empty_keys"
    for key in keys:
        update_openai_api_key(new_key= key)
        load_dotenv(override=True)
        client = AsyncOpenAI(api_key=key)
        answer = await call_openai_with_auto_key(system_prompt=system_prompt, user_prompt=user_prompt, client=client)

        if answer == "error":
            await db.deactivate_key(key)
        else:
            return answer

    return answer



