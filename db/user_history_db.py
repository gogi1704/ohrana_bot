from typing import Optional, List
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio
import aiosqlite
import os
from dotenv import load_dotenv
from gspread_asyncio import AsyncioGspreadClientManager


load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "users_history.db")

SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
CREDS_PATH = "docs/ohrananeurobot-83be3456de6a.json"  # путь к JSON-файлу сервисного аккаунта
SPREADSHEET_NAME = "users_history"

def get_sheet():
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_PATH, SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME)
    return {
        "users_data": sheet.worksheet("users_data"),
        "messages": sheet.worksheet("messages"),
        "message_links": sheet.worksheet("message_links"),
        "api_keys": sheet.worksheet("api_keys"),
        "user_questions": sheet.worksheet("user_questions"),
    }

def get_creds():
    return ServiceAccountCredentials.from_json_keyfile_name(CREDS_PATH, SCOPE)

async def add_question_without_answer_to_sheet(question):
    try:
        async_client = AsyncioGspreadClientManager(get_creds)
        client = await async_client.authorize()
        spreadsheet = await client.open("questions_answers")
        worksheet = await spreadsheet.get_worksheet(0)
        records = await worksheet.get_all_records()
        last_number = records[-1]["Номер"] if records else 0
        new_number = last_number + 1

        await worksheet.append_row([new_number, question, ""])
        print(f"✅ Добавлен вопрос #{new_number}: {question}")

    except Exception as e:
        print(e)

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                user_id INTEGER PRIMARY KEY,
                message TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users_data (
                user_id INTEGER PRIMARY KEY,
                user_name TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS message_links (
                group_message_id INTEGER PRIMARY KEY,
                user_id INTEGER
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                key TEXT PRIMARY KEY,
                is_active BOOLEAN DEFAULT 1
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_questions (
                user_id INTEGER PRIMARY KEY,
                questions TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS last_buttons (
                user_id INTEGER PRIMARY KEY,
                message_id INTEGER,
                text TEXT
            )
        """)
        await  db.execute("""
            CREATE TABLE IF NOT EXISTS user_reply_states  (
                user_id INTEGER PRIMARY KEY,
                manager_msg_id  INTEGER
            )
        """)

        try:
            await db.execute("ALTER TABLE users_data ADD COLUMN company TEXT")
        except aiosqlite.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise  # Только если колонка уже есть — игнорируем
        try:
            await db.execute("ALTER TABLE users_data ADD COLUMN state TEXT DEFAULT NULL")
        except aiosqlite.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise  # Только если колонка уже есть — игнорируем
        try:
            await db.execute("ALTER TABLE users_data ADD COLUMN life_que_keyboard TEXT DEFAULT NULL")
        except aiosqlite.OperationalError as e:
            if "duplicate column name" not in str(e):
                raise  # Только если колонка уже есть — игнорируем

        await db.commit()
    await sync_from_google_sheets()

async def sync_from_google_sheets():
    sheets = get_sheet()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM users_data")
        await db.execute("DELETE FROM messages")
        await db.execute("DELETE FROM message_links")
        await db.execute("DELETE FROM api_keys")
        await db.execute("DELETE FROM user_questions")

        api_keys = sheets["api_keys"].get_all_values()[1:]  # пропустить заголовок
        for row in api_keys:
            key, is_active = row
            await db.execute(
                "INSERT OR IGNORE INTO api_keys (key, is_active) VALUES (?, ?)",
                (key.strip(), is_active.strip() == "TRUE")
            )

        # users_data
        users = sheets["users_data"].get_all_values()[1:]
        for row in users:
            user_id, user_name, company, state = row
            await db.execute(
                "INSERT INTO users_data (user_id, user_name, company, state) VALUES (?, ?, ?, ?)",
                (int(user_id), user_name, company, state)
            )

        # messages
        messages = sheets["messages"].get_all_values()[1:]
        for row in messages:
            user_id, message = row
            await db.execute(
                "INSERT INTO messages (user_id, message) VALUES (?, ?)",
                (int(user_id), message)
            )

        # message_links
        links = sheets["message_links"].get_all_values()[1:]
        for row in links:
            group_message_id, user_id = row
            await db.execute(
                "INSERT INTO message_links (group_message_id, user_id) VALUES (?, ?)",
                (int(group_message_id), int(user_id))
            )

        # user_questions
        questions = sheets["user_questions"].get_all_values()[1:]
        for row in questions:
            user_id, question = row
            await db.execute(
                "INSERT INTO user_questions (user_id, question) VALUES (?, ?)",
                (int(user_id), int(question))
            )
        await db.commit()

async def sync_to_google_sheets():
    sheets = get_sheet()

    async with aiosqlite.connect(DB_PATH) as db:
        # api_keys
        try:
            async with db.execute("SELECT * FROM api_keys") as cursor:
                keys = await cursor.fetchall()
            header = ["key", "is_active"]
            data = [[row[0], "TRUE" if row[1] else "FALSE"] for row in keys]
            sheet = sheets["api_keys"]
            sheet.clear()
            sheet.update('A1', [header] + data)
            print("[✅] api_keys обновлены")
        except Exception as e:
            print(f"[❌] Ошибка api_keys: {e}")

        # users_data
        try:
            async with db.execute("SELECT * FROM users_data") as cursor:
                users = await cursor.fetchall()
            header = ["user_id", "user_name", "company", "state"]
            data = [[str(r) if r is not None else "" for r in row] for row in users]
            sheet = sheets["users_data"]
            sheet.clear()
            sheet.update('A1', [header] + data)
            print("[✅] users_data обновлены")
        except Exception as e:
            print(f"[❌] Ошибка users_data: {e}")

        # messages
        try:
            async with db.execute("SELECT * FROM messages") as cursor:
                messages = await cursor.fetchall()
            header = ["user_id", "message"]
            data = [[str(r) for r in row] for row in messages]
            sheet = sheets["messages"]
            sheet.clear()
            sheet.update('A1', [header] + data)
            print("[✅] messages обновлены")
        except Exception as e:
            print(f"[❌] Ошибка messages: {e}")

        # message_links
        try:
            async with db.execute("SELECT * FROM message_links") as cursor:
                links = await cursor.fetchall()
            header = ["group_message_id", "user_id"]
            data = [[str(r) for r in row] for row in links]
            sheet = sheets["message_links"]
            sheet.clear()
            sheet.update('A1', [header] + data)
            print("[✅] message_links обновлены")
        except Exception as e:
            print(f"[❌] Ошибка message_links: {e}")

        # user_questions
        try:
            async with db.execute("SELECT * FROM user_questions") as cursor:
                rows = await cursor.fetchall()
            header = ["user_id", "questions"]
            data = [[str(row[0]), row[1]] for row in rows]
            sheet = sheets["user_questions"]
            sheet.clear()
            sheet.update('A1', [header] + data)
            print("[✅] user_questions обновлены")
        except Exception as e:
            print(f"[❌] Ошибка user_questions: {e}")

async def periodic_sync(interval: int = 900):  # 900 сек = 15 мин
    while True:
        await asyncio.sleep(interval)
        try:
            await sync_to_google_sheets()
            print(f"Успешная синхронизация.")
        except Exception as e:
            print(f"Ошибка при синхронизации в Google Sheets: {e}")




async def add_user(user_id: int, user_name: str, company: Optional[str] = None) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO users_data (user_id, user_name, company) VALUES (?, ?, ?)",
            (user_id, user_name, company)
        )
        await db.commit()

async def get_user_name(user_id: int) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_name FROM users_data WHERE user_id = ? LIMIT 1", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def add_or_update_message(user_id: int, message: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT 1 FROM messages WHERE user_id = ?", (user_id,)) as cursor:
            exists = await cursor.fetchone()

        if exists:
            await db.execute("UPDATE messages SET message = ? WHERE user_id = ?", (message, user_id))
        else:
            await db.execute("INSERT INTO messages (user_id, message) VALUES (?, ?)", (user_id, message))

        await db.commit()


async def get_history_by_id(user_id: int) -> List[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT message FROM messages WHERE user_id = ?", (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


async def remove_history_by_id(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
        await db.commit()


async def save_message_link(group_message_id: int, user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO message_links (group_message_id, user_id) VALUES (?, ?)",
            (group_message_id, user_id)
        )
        await db.commit()


async def get_user_id_by_group_message(group_message_id: int) -> Optional[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id FROM message_links WHERE group_message_id = ?",
            (group_message_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def update_state(user_id: int, state: Optional[str]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users_data SET state = ? WHERE user_id = ?",
            (state, user_id)
        )
        await db.commit()

async def get_state(user_id: int) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT state FROM users_data WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def get_active_keys() -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT key FROM api_keys WHERE is_active=1") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

async def deactivate_key(api_key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE api_keys SET is_active = 0 WHERE key=?", (api_key,))
        await db.commit()
    try:
        await sync_to_google_sheets()
    except Exception as e:
        print(f"Не удалось синхронизировать ключи: {e}")

async def save_user_questions(user_id: int, questions: List[str]) -> None:
    questions_json = json.dumps(questions, ensure_ascii=False)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO user_questions (user_id, questions) VALUES (?, ?)",
            (user_id, questions_json)
        )
        await db.commit()

async def get_user_questions(user_id: int) -> Optional[List[str]]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT questions FROM user_questions WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None

async def delete_user_questions(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM user_questions WHERE user_id = ?", (user_id,))
        await db.commit()



async def save_last_button(user_id: int, message_id: int, text: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO last_buttons (user_id, message_id, text)
            VALUES (?, ?, ?)
        """, (user_id, message_id, text))
        await db.commit()

async def get_last_button(user_id: int) -> Optional[tuple[int, str]]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT message_id, text FROM last_buttons WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row if row else None

async def delete_last_button(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM last_buttons WHERE user_id = ?", (user_id,))
        await db.commit()


async def get_life_que_keyboard(user_id: int) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT life_que_keyboard FROM users_data WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def save_life_que_keyboard(user_id: int, keyboard: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users_data (user_id, life_que_keyboard)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET life_que_keyboard = excluded.life_que_keyboard
            """,
            (user_id, keyboard)
        )
        await db.commit()

async def delete_life_que_keyboard(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users_data SET life_que_keyboard = NULL WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()




async def save_user_reply_state(user_id: int, manager_msg_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "REPLACE INTO user_reply_states (user_id, manager_msg_id) VALUES (?, ?)",
            (user_id, manager_msg_id)
        )
        await db.commit()

async def get_user_reply_state(user_id: int) -> int | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT manager_msg_id FROM user_reply_states WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None

async def delete_user_reply_state(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM user_reply_states WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()







