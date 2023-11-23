from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher.filters import Text
from bot_postgre import *

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


def get_owner_choice_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    button_1 = InlineKeyboardButton(text='Не предоставлять доступ', callback_data='no_access')
    button_2 = InlineKeyboardButton(text='Предоставить слоты, не показывая чем вы заняты', callback_data='encrypted')
    button_3 = InlineKeyboardButton(text='Предоставить полноценный доступ к просмотру', callback_data='full_access')
    kb.add(button_1, button_2, button_3)

    return kb


def get_day_choice_kb() -> InlineKeyboardButton:
    kb = InlineKeyboardMarkup(row_width=1)
    button_1 = InlineKeyboardButton(text='На 1 день', callback_data='one')
    button_2 = InlineKeyboardButton(text='На 7 дней', callback_data='seven')
    button_3 = InlineKeyboardButton(text='На 14 дней', callback_data='fourteen')
    button_4 = InlineKeyboardButton(text='На 30 дней', callback_data='thirty')
    button_5 = InlineKeyboardButton(text='Свой промежуток', callback_data='own_choice')
    kb.add(button_1, button_2, button_3, button_4, button_5)

    return kb

reactivate_kb = ReplyKeyboardMarkup(resize_keyboard=True)
reactivate_kb.add(KeyboardButton('/Reactivate_bot'))
