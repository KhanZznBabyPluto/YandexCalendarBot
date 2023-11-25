from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher.filters import Text
from bot_postgre import *
from bot_token import client_secret, client_id, redirect_uri

def get_kb(flag, flag_access) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('/Authorize'))
    if flag:
        kb.add(KeyboardButton('/Check_Calendar'))
        if flag_access:
            kb.add(KeyboardButton('/Check_Accesses'))
        else:
            kb.add(KeyboardButton('/Ask_for_Access'))
    kb.add(KeyboardButton('/Cancel'))
    
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
    button_5 = InlineKeyboardButton(text='Свой промежуток', callback_data=f'own_choice:{user_id}:{type_access}')
    kb.add(button_1, button_2, button_3, button_4, button_5)

    return kb


url = InlineKeyboardMarkup()
auth_url = f'https://oauth.yandex.ru/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}'
url_button = InlineKeyboardButton(text="Перейти по ссылке", url=auth_url)
url.add(url_button)



reactivate_kb = ReplyKeyboardMarkup(resize_keyboard=True)
reactivate_kb.add(KeyboardButton('/Reactivate_bot'))
