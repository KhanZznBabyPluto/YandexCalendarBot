from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher.filters import Text
from bot_mongo import *

def get_kb(flag, flag_access) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('/Authorize'))
    if flag:
        if flag_access:
            kb.add(KeyboardButton('/Check_Calendar'))
            kb.add(KeyboardButton('/Check_Accesses'))
        else:
            kb.add(KeyboardButton('/Ask_for_Access'))
    kb.add(KeyboardButton('/Cancel'))
    
    return kb


def get_owner_choice_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(row_width=1)
    button = InlineKeyboardButton(text='Предоставить слоты, не показывая чем вы заняты', callback_data='encrypted')
    kb.add(button)
    button = InlineKeyboardButton(text='Предоставить полноценный доступ к просмотру', callback_data='full_access')
    kb.add(button)

    return kb


reactivate_kb = ReplyKeyboardMarkup(resize_keyboard=True)
reactivate_kb.add(KeyboardButton('/Reactivate_bot'))
