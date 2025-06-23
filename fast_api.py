from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import main
import db.user_history_db as sql_db
import asyncio



async def lifespan(app: FastAPI):
    # инициализация перед запуском
    await sql_db.init_db()
    await main.init_docs()
    yield
    # тут можно делать действия при завершении, если нужно
app = FastAPI(lifespan = lifespan)

# asyncio.create_task(sql_db.periodic_sync())

# настройки для работы запросов
app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnswerRequest(BaseModel):
    text_answer: str
    user_id: int

class StateRequest(BaseModel):
    user_id: int
    state: str


@app.post("/api/manager_get_info")
async def get_manager_info(request: AnswerRequest):
    try:
        consult_answer = await main.manager_get_info(user_id= request.user_id,
                                                       user_say= request.text_answer)
        return {"message": consult_answer}
    except Exception as e:
        return {"message": "Error "+ str(e)}

@app.post("/api/hello_dialog")
async def hello_dialog(request: AnswerRequest):
    try:
        hello_answer = await main.get_hello_dialog_answer(user_id= request.user_id,
                                                       user_say= request.text_answer)
        return {"message": hello_answer}
    except Exception as e:
        return {"message": "Error "+ str(e)}


@app.post("/api/get_consult")
async def get_consult(request: AnswerRequest):
    try:
        consult_answer = await main.get_consult_answer(user_id= request.user_id,
                                                       user_say= request.text_answer)
        return {"message": consult_answer}
    except Exception as e:
        return {"message": "Error "+ str(e)}

@app.post("/api/get_company")
async def get_company(request: AnswerRequest):
    try:
        consult_answer = await main.get_company(user_id= request.user_id,
                                                user_say= request.text_answer)

        return {"message": consult_answer}
    except Exception as e:
        return {"message": "Error "+ str(e)}

@app.post("/api/get_prev_consult")
async def get_prev_consult(request: AnswerRequest):
    try:
        consult_answer = await main.get_prev_consult_answer(user_id= request.user_id,user_say= request.text_answer)

        return {"message": consult_answer}
    except Exception as e:
        return {"message": "Error "+ str(e)}

@app.post("/api/transfer_get_date")
async def transfer_get_date(request: AnswerRequest):
    try:
        consult_answer = await main.transfer_get_date(user_id= request.user_id,user_say= request.text_answer)

        return {"message": consult_answer}
    except Exception as e:
        return {"message": "Error "+ str(e)}

@app.post("/api/manager_human_dialog")
async def manager_human_dialog(request: AnswerRequest):
    try:
        consult_answer = await main.manager_human_dialog(user_id= request.user_id,user_say= request.text_answer)
        return {"message": consult_answer}
    except Exception as e:
        return {"message": "Error "+ str(e)}

@app.post("/api/get_final_question")
async def get_final_question(request: AnswerRequest):
    try:
        consult_answer = await main.get_final_question(user_id= request.user_id,user_say= request.text_answer)
        return {"message": consult_answer}
    except Exception as e:
        return {"message": "Error "+ str(e)}


@app.post("/api/start")
async def start_command(request: AnswerRequest):
    try:
        result = await main.start(request.user_id)
        if result:
            return {"message": result}
        else:
            return {"message": "empty"}
    except Exception as e:
        return {"message": "Error "+ str(e)}

@app.post("/api/update_state")
async def update_state(request: StateRequest):
    try:
        result = await main.update_state(user_id= request.user_id, state= request.state)
        if result:
            return {"message": result}
        else:
            return {"message": "empty"}
    except Exception as e:
        return {"message": "Error "+ str(e)}

@app.post("/api/get_state")
async def get_state(request: StateRequest):
    try:
        result = await main.get_state(user_id= request.user_id)
        if result:
            return {"message": result}
        else:
            return {"message": "empty"}
    except Exception as e:
        return {"message": "Error "+ str(e)}


