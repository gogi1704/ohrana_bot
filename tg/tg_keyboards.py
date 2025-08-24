from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton , InlineKeyboardButton, WebAppInfo
import resources

base_keyboard_to_life_question = [[KeyboardButton("Житейские вопросы")]]

inline_keyboard_categories_life_questions= [
    [InlineKeyboardButton("📌 Долги и займы", callback_data="btn_category_life_1")],
    [InlineKeyboardButton("🏠 Недвижимость и земля", callback_data="btn_category_life_2")],
    [InlineKeyboardButton("👨‍👩‍👧‍👦 Семья и наследство", callback_data="btn_category_life_3")],
    [InlineKeyboardButton("🚗 Авто и ДТП", callback_data="btn_category_life_4")],
    [InlineKeyboardButton("⚖ Судебные споры и налоги", callback_data="btn_category_life_5")],
    [InlineKeyboardButton("🛒 Потребительские права", callback_data="btn_category_life_6")],
    [InlineKeyboardButton("🏥 Медицина и ЖКХ", callback_data="btn_category_life_7")],
    [InlineKeyboardButton("💼 Работа и увольнение", callback_data="btn_category_life_8")],
    [InlineKeyboardButton("Закрыть", callback_data="btn_life_exit")],
]

inline_keyboard_life_questions_cat_1 = [
[InlineKeyboardButton("Как правильно дать в долг", callback_data="btn_category_1_que_1")],
[InlineKeyboardButton("Перевёл деньги другу и пришло письмо из налоговой", callback_data="btn_category_1_que_2")],
[InlineKeyboardButton("Банк подал в суд за просрочку.Что делать?", callback_data="btn_category_1_que_3")],
[InlineKeyboardButton("Дали деньги в долг или подарили — что указывать в переводе?", callback_data="btn_category_1_que_4")],
[InlineKeyboardButton("Назад", callback_data="btn_back_from_life_question")],
]

inline_keyboard_life_questions_cat_2 = [
[InlineKeyboardButton("Наследство — не только квартиры, но и долги. Как не попасть?", callback_data="btn_category_2_que_1")],
[InlineKeyboardButton("Земля 'от бабушки', а документов нет. Что делать?", callback_data="btn_category_2_que_2")],
[InlineKeyboardButton("Сосед залез на ваш участок — как защитить границы?", callback_data="btn_category_2_que_3")],
[InlineKeyboardButton("Как продать квартиру без обмана и нервов", callback_data="btn_category_2_que_4")],
[InlineKeyboardButton("Сдаёте квартиру без договора? Вот чем это может закончиться", callback_data="btn_category_2_que_5")],
[InlineKeyboardButton("Можно ли оформить дом на земле ИЖС без разрешения на строительство?", callback_data="btn_category_2_que_6")],
[InlineKeyboardButton("Сняли жильё, а арендодатель требует съехать — законно ли это?", callback_data="btn_category_2_que_7")],
[InlineKeyboardButton("Назад", callback_data="btn_back_from_life_question")],
]

inline_keyboard_life_questions_cat_3 = [
[InlineKeyboardButton("Хочу оформить опеку над бабушкой или племянником. Как?", callback_data="btn_category_3_que_1")],
[InlineKeyboardButton("Как оформить доверенность на бабушку или дедушку", callback_data="btn_category_3_que_2")],
[InlineKeyboardButton("Как составить завещание, чтобы потом не было скандалов", callback_data="btn_category_3_que_3")],
[InlineKeyboardButton("Дарственная или завещание — что лучше?", callback_data="btn_category_3_que_4")],
[InlineKeyboardButton(" Делаете ремонт в квартире, купили машину — а деньги дал кто-то из родителей?", callback_data="btn_category_3_que_5")],
[InlineKeyboardButton("Материнский капитал в 2025 году — на что можно потратить и как оформить", callback_data="btn_category_3_que_6")],
[InlineKeyboardButton("Назад", callback_data="btn_back_from_life_question")],
]

inline_keyboard_life_questions_cat_4 = [
[InlineKeyboardButton("Покупаю авто с рук. Как не остаться без машины и денег?", callback_data="btn_category_4_que_1")],
[InlineKeyboardButton("Как оформить ДТП без ГИБДД и получить выплату", callback_data="btn_category_4_que_2")],
[InlineKeyboardButton("Штрафы ГИБДД пришли по ошибке — как обжаловать", callback_data="btn_category_4_que_3")],
[InlineKeyboardButton("Назад", callback_data="btn_back_from_life_question")],
]

inline_keyboard_life_questions_cat_5 = [
[InlineKeyboardButton("Что делать, если пришла повестка в суд, а вы ничего не знаете?", callback_data="btn_category_5_que_1")],
[InlineKeyboardButton("Мошенники оформили кредит на ваше имя — как действовать?", callback_data="btn_category_5_que_2")],
[InlineKeyboardButton("Мошенники оформили на вас ИП — что делать?", callback_data="btn_category_5_que_3")],
[InlineKeyboardButton("Кредит погашен, но банк не снял обременение — в чём риск?", callback_data="btn_category_5_que_4")],
[InlineKeyboardButton("Назад", callback_data="btn_back_from_life_question")],
]

inline_keyboard_life_questions_cat_6 = [
[InlineKeyboardButton("Купили товар, а он сломался — как вернуть деньги?", callback_data="btn_category_6_que_1")],
[InlineKeyboardButton("Сгорела техника из-за скачка напряжения — можно ли взыскать ущерб?", callback_data="btn_category_6_que_2")],
[InlineKeyboardButton("Соседи шумят по ночам — что реально можно сделать?", callback_data="btn_category_6_que_3")],
[InlineKeyboardButton("Назад", callback_data="btn_back_from_life_question")],
]

inline_keyboard_life_questions_cat_7 = [
[InlineKeyboardButton("В больнице отказали в бесплатной услуге — это законно?", callback_data="btn_category_7_que_1")],
[InlineKeyboardButton("Долг по ЖКХ — могут ли забрать квартиру?", callback_data="btn_category_7_que_2")],
[InlineKeyboardButton("Назад", callback_data="btn_back_from_life_question")],
]

inline_keyboard_life_questions_cat_8 = [
[InlineKeyboardButton("Уволили 'по соглашению сторон', но денег не дали — что делать?", callback_data="btn_category_8_que_1")],
[InlineKeyboardButton("Увольнение без отработки — возможно ли?", callback_data="btn_category_8_que_2")],
[InlineKeyboardButton("Назад", callback_data="btn_back_from_life_question")],
]


CATEGORY_KEYBOARDS = {
    "btn_category_life_1": inline_keyboard_life_questions_cat_1,
    "btn_category_life_2": inline_keyboard_life_questions_cat_2,
    "btn_category_life_3": inline_keyboard_life_questions_cat_3,
    "btn_category_life_4": inline_keyboard_life_questions_cat_4,
    "btn_category_life_5": inline_keyboard_life_questions_cat_5,
    "btn_category_life_6": inline_keyboard_life_questions_cat_6,
    "btn_category_life_7": inline_keyboard_life_questions_cat_7,
    "btn_category_life_8": inline_keyboard_life_questions_cat_8,
}

QUESTION_PREFIX = "btn_category_"
QUESTION_DATA = {
    f"{QUESTION_PREFIX}{i}_que_{j}": resources.life_questions.get(f"category_{i}_que_{j}")
    for i in range(1, 9)
    for j in range(1, 8)  # макс. 7 вопросов на категорию
    if resources.life_questions.get(f"category_{i}_que_{j}") is not None
}

web_app_keys = [
    [KeyboardButton("Чтобы выбрать из списка нажмите сюда", web_app=WebAppInfo(url=resources.web_app_url))]
]
web_app_keyboard = ReplyKeyboardMarkup(
    web_app_keys,
    resize_keyboard=True
)


