import aiohttp
import requests
import os
import resources
import json
import html
import re
from collections import Counter


def download_gdoc(url: str) :
    # Создаём папку docs, если её нет
    os.makedirs('docs', exist_ok=True)

    # Извлекаем document_id
    match = re.search(r'/document/d/([a-zA-Z0-9_-]+)', url)
    if not match:
        raise ValueError("Не удалось извлечь document_id из ссылки.")
    document_id = match.group(1)

    # Скачиваем документ в формате .txt
    export_url = f"https://docs.google.com/document/d/{document_id}/export?format=txt"
    response = requests.get(export_url)

    if response.status_code == 200:
        file_path = resources.path_baza_answers
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(response.text)
        print(f"Документ сохранён в: {file_path}")
    else:
        raise Exception(f"Не удалось загрузить документ. Код ответа: {response.status_code}")
    return response.text


def get_text_from_txt_file(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл {file_path} не найден. Сначала скачайте документ.")

    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

async def send_request(url, payload):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(sock_connect=90, sock_read=120)) as session:
        async with session.post(url= url, json=payload) as resp:
            text_json = await resp.json()
            return text_json['message']


def split_qa_pairs(text):
    pattern = r'Вопрос:(.*?)Ответ:(.*?)(?=Вопрос:|$)'
    matches = re.findall(pattern, text, re.DOTALL)
    return [f"Вопрос:{q.strip()}\nОтвет:{a.strip()}" for q, a in matches]



def parse_category_json(response_text: str) -> dict:
    try:
        data = json.loads(response_text)

        category = data.get("category")
        question = data.get("question", None)

        if category not in {"company_que", "manager_que", "transfer_que"}:
            raise ValueError(f"Некорректная категория: {category}")

        return {
            "category": category,
            "question": question
        }

    except json.JSONDecodeError:
        return {
            "error": "Невалидный JSON"
        }
    except Exception as e:
        return {
            "error": str(e)
        }

def parse_manager_response(response: str):
    if not response.startswith("manager_complete;"):
        return None, None  # или можно выбросить ошибку

    try:
        # Разделяем строку по частям
        parts = response.split(";")
        contact_part = next(p for p in parts if "Способ связи:" in p)

        # Извлекаем значения
        contact = contact_part.split("Способ связи:")[1].strip()

        return contact
    except Exception as e:
        print("Error in parse_manager_response:", e)
        return  None

def parse_transfer_response(json_string: str) -> tuple[str, str] | None:
    try:
        data = json.loads(json_string)
        if isinstance(data, dict):
            result = data.get("result")
            date = data.get("date")
            if isinstance(result, str) and isinstance(date, str):
                return result, date
    except json.JSONDecodeError:
        pass
    return None




def highlight(text: str, style: str = "bold", mode: str = "HTML") -> str:
    """
    Оборачивает текст в нужный тег или маркер для Telegram-разметки.

    :param text: Текст для выделения.
    :param style: 'bold', 'italic', 'code', 'pre', 'underline'
    :param mode: 'HTML' или 'MarkdownV2'
    :return: Размеченный текст.
    """
    if mode.upper() == "HTML":
        escaped = html.escape(text)
        tags = {
            "bold": f"<b>{escaped}</b>",
            "italic": f"<i>{escaped}</i>",
            "code": f"<code>{escaped}</code>",
            "pre": f"<pre>{escaped}</pre>",
            "underline": f"<u>{escaped}</u>",
        }
        return tags.get(style, escaped)

    elif mode.upper() == "MARKDOWNV2":
        # Экранируем спецсимволы Markdown V2
        def escape_md(text):
            return re.sub(r'([_*[\]()~`>#+\-=|{}.!])', r'\\\1', text)

        escaped = escape_md(text)
        tags = {
            "bold": f"*{escaped}*",
            "italic": f"_{escaped}_",
            "code": f"`{escaped}`",
            "pre": f"```{escaped}```",
            "underline": f"__{escaped}__",
        }
        return tags.get(style, escaped)

    else:
        return text  # если mode неизвестен — вернём без изменений

def get_prikaz_29_punkts_from_name(name):
    final_res = []
    # Абсолютный путь к текущему файлу (util_funs.py)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'docs', 'dogma_full_dump.json')

    # Проверка, существует ли файл
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Файл не найден по пути: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    result = []
    query = name.lower()

    for key, items in data.items():
        if query.lower() in key.lower():
            result.extend(items)

    for item in result:
        final_res.append(item["пункт_приказа"])

    return final_res


def get_doctors_by_punkts(points):
    doctors = set()
    tests = set()
    # Абсолютный путь к текущему файлу (util_funs.py)
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Путь до корня проекта (если util_funs.py лежит в корне проекта, то current_dir — уже корень)
    file_path = os.path.join(current_dir, 'docs', 'table_prilozhenie_1.json')

    # Проверка, существует ли файл
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Файл не найден по пути: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
       json_data = json.load(f)

    # Убираем "п." и пробелы для корректного сравнения
    cleaned_points = [p.replace("п.", "").strip('.') for p in points]

    for item in json_data:
        n_pp_clean = item.get("N п/п", "").strip()
        if n_pp_clean in cleaned_points:
            # Добавляем врачей
            doctor_field = item.get("Участие врачей-специалистов", "")
            if doctor_field:
                doctors.update(line.strip() for line in doctor_field.split('\n') if line.strip())

            # Добавляем исследования
            tests_field = item.get("Лабораторные и функциональные исследования", "")
            if tests_field:
                tests.update(line.strip() for line in tests_field.split('\n') if line.strip())

    return list(doctors), list(tests)



def normalize(text):
    return text.strip().lower()

def get_unique_counts_safe(nested_lists):
    flat_list = [
        item.strip() for sublist in nested_lists
        for item in sublist
        if isinstance(item, str) and item.strip()
    ]

    normalized_map = {}
    for item in flat_list:
        key = normalize(item)
        if key not in normalized_map:
            normalized_map[key] = item.strip()  # Сохраняем первое "нормальное" представление

    # Подсчёт количества по нормализованным значениям
    counts = Counter(normalize(item) for item in flat_list)

    # Финальное представление: уникальные нормализованные значения (с заглавной буквы) и количество
    unique_items = [normalized_map[k].capitalize() for k in counts]
    counted_items = {normalized_map[k].capitalize(): v for k, v in counts.items()}

    return unique_items, counted_items

def get_base_doctors_or_tests(peoples_group, count):
    result = {item: count for item in peoples_group}
    return result

def get_text_test_or_doctors(start_text, list_doctors_or_tests):

    for item, count in list_doctors_or_tests.items():
        start_text += f"– {item}: {count} шт.\n"

    return start_text



# points = get_prikaz_29_punkts_from_name("автоклавер | больницы")
# print(get_doctors_by_punkts(points))


