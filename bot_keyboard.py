import logging
from bot_db import *
from bot_token import client_secret, client_id, redirect_uri
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

logging.getLogger().handlers = []

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('bot.log', encoding='utf-8')

file_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(file_handler)

def get_kb(flag) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    if flag:
        kb.add("/Check_Calendar", "/Check_Accesses")
        kb.add("/Get_User_Calendar", "/Ask_for_Access")
        kb.add("/Change_Access", "/Cancel")
    else:
        kb.add("/Authorize")
        kb.add("/Cancel")

    return kb

def get_owner_choice_kb(user_id, cmd, email='default') -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    button_1 = InlineKeyboardButton(text='Не предоставлять доступ', callback_data=f'no_access:{user_id}:{cmd}:{email}')
    button_2 = InlineKeyboardButton(text='Предоставить слоты, не показывая чем вы заняты', callback_data=f'encrypted:{user_id}:{cmd}:{email}')
    button_3 = InlineKeyboardButton(text='Предоставить полноценный доступ к просмотру', callback_data=f'full_access:{user_id}:{cmd}:{email}')
    kb.add(button_1, button_2, button_3)

    return kb

def get_day_choice_kb(user_id, type_access, cmd) -> InlineKeyboardButton:
    kb = InlineKeyboardMarkup(row_width=1)
    button_1 = InlineKeyboardButton(text='На 1 день', callback_data=f'one:{user_id}:{type_access}:1:{cmd}')
    button_2 = InlineKeyboardButton(text='На 7 дней', callback_data=f'seven:{user_id}:{type_access}:7:{cmd}')
    button_3 = InlineKeyboardButton(text='На 14 дней', callback_data=f'fourteen:{user_id}:{type_access}:14:{cmd}')
    button_4 = InlineKeyboardButton(text='На 30 дней', callback_data=f'thirty:{user_id}:{type_access}:30:{cmd}')
    # button_5 = InlineKeyboardButton(text='Свой промежуток', callback_data=f'own_choice:{user_id}:{type_access}')
    kb.add(button_1, button_2, button_3, button_4)

    return kb
            

def generate_inline_keyboard(buttons, cmd, current_page, buttons_per_page=10):
    start_idx = (current_page - 1) * buttons_per_page
    end_idx = start_idx + buttons_per_page
    current_buttons = buttons[start_idx:end_idx]

    keyboard = InlineKeyboardMarkup(row_width=2)
    for button in current_buttons:
        string = button
        string += f':{cmd}'
        keyboard.add(InlineKeyboardButton(text=button, callback_data=string))

    navigation_buttons = []
    if current_page > 1:
        navigation_buttons.append(InlineKeyboardButton(text="Назад", callback_data=f"prev_page_{current_page}"))
    if end_idx < len(buttons):
        navigation_buttons.append(InlineKeyboardButton(text="Вперед", callback_data=f"next_page_{current_page}"))

    if navigation_buttons:
        keyboard.add(*navigation_buttons)

    return keyboard

def get_accesses_kb(accesses_dict, cmd, current_page=1):
    buttons = [access['email'] for access in accesses_dict if access['type'] != 'no']
    return generate_inline_keyboard(buttons, cmd, current_page)



url = InlineKeyboardMarkup()
auth_url = f'https://oauth.yandex.ru/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}'
url_button = InlineKeyboardButton(text="Перейти по ссылке", url=auth_url)
url.add(url_button)

url_pass = InlineKeyboardMarkup()
pass_url = 'https://id.yandex.ru/security/app-passwords'
url_pass_button = InlineKeyboardButton(text="Перейти по ссылке", url=pass_url)
url_pass.add(url_pass_button)