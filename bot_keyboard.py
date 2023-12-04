from bot_db import *
from bot_token import client_secret, client_id, redirect_uri
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

def get_kb(flag) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    if flag:
        kb.add("/Check_Calendar", "/Check_Accesses")
        kb.add("/Get_User_Calendar", "/Ask_for_Access")
    else:
        kb.add("/Authorize")
    kb.add("/Cancel")

    return kb

def get_owner_choice_kb(user_id) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    button_1 = InlineKeyboardButton(text='Не предоставлять доступ', callback_data=f'no_access:{user_id}')
    button_2 = InlineKeyboardButton(text='Предоставить слоты, не показывая чем вы заняты', callback_data=f'encrypted:{user_id}')
    button_3 = InlineKeyboardButton(text='Предоставить полноценный доступ к просмотру', callback_data=f'full_access:{user_id}')
    kb.add(button_1, button_2, button_3)

    return kb

def get_day_choice_kb(user_id, type_access) -> InlineKeyboardButton:
    kb = InlineKeyboardMarkup(row_width=1)
    button_1 = InlineKeyboardButton(text='На 1 день', callback_data=f'one:{user_id}:{type_access}:1')
    button_2 = InlineKeyboardButton(text='На 7 дней', callback_data=f'seven:{user_id}:{type_access}:7')
    button_3 = InlineKeyboardButton(text='На 14 дней', callback_data=f'fourteen:{user_id}:{type_access}:14')
    button_4 = InlineKeyboardButton(text='На 30 дней', callback_data=f'thirty:{user_id}:{type_access}:30')
    # button_5 = InlineKeyboardButton(text='Свой промежуток', callback_data=f'own_choice:{user_id}:{type_access}')
    kb.add(button_1, button_2, button_3, button_4)

    return kb


def generate_inline_keyboard(buttons, current_page, buttons_per_page=10):
    start_idx = (current_page - 1) * buttons_per_page
    end_idx = start_idx + buttons_per_page
    current_buttons = buttons[start_idx:end_idx]

    keyboard = InlineKeyboardMarkup(row_width=2)
    for button in current_buttons:
        keyboard.add(InlineKeyboardButton(text=button, callback_data=button))

    navigation_buttons = []
    if current_page > 1:
        navigation_buttons.append(InlineKeyboardButton(text="Назад", callback_data=f"prev_page_{current_page}"))
    if end_idx < len(buttons):
        navigation_buttons.append(InlineKeyboardButton(text="Вперед", callback_data=f"next_page_{current_page}"))

    if navigation_buttons:
        keyboard.add(*navigation_buttons)

    return keyboard

def get_accesses_kb(accesses_dict, current_page=1):
    buttons = [access['email'] for access in accesses_dict]
    return generate_inline_keyboard(buttons, current_page)


url = InlineKeyboardMarkup()
auth_url = f'https://oauth.yandex.ru/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}'
url_button = InlineKeyboardButton(text="Перейти по ссылке", url=auth_url)
url.add(url_button)

url_pass = InlineKeyboardMarkup()
pass_url = 'https://id.yandex.ru/security/app-passwords'
url_pass_button = InlineKeyboardButton(text="Перейти по ссылке", url=pass_url)
url_pass.add(url_pass_button)

reactivate_kb = ReplyKeyboardMarkup(resize_keyboard=True)
reactivate_kb.add(KeyboardButton('/Reactivate_bot'))