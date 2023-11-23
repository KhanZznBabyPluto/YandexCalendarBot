import requests
import datetime
from aiogram import types, executor, Bot, Dispatcher
from aiogram.types import CallbackQuery
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode

from bot_token import TOKEN_API
from bot_classes import User, Owner
from bot_postgre import *
from bot_keyboard import get_kb, get_owner_choice_kb, get_day_choice_kb, reactivate_kb

user = User()

flag = 0

client_id = '68864fc64a7842c1948567f02d1bdf4c'
client_secret = '9f10504cfd3d41e5a5650b277ddae6d7'
redirect_uri = 'https://oauth.yandex.ru/verification_code'
storage = MemoryStorage()
bot = Bot(TOKEN_API)
dp = Dispatcher(bot, storage=storage)


class UserStates(StatesGroup):
    ACTIVE = State()
    INACTIVE = State() 

class ProfileStatesGroup(StatesGroup):
    code = State()
    keyword = State()


Action_for_start = """
    Дорбро пожаловать!\nЧтобы привязать ваш аккаунт, нажмите - <b>/Authorize</b>"""

Action_for_owner = """
    Давайте перейдём к планированию. Вы - Директор.\nЧтобы просмотреть ваш календарь на сегодня, нажмите - <b>/Check_Calendar</b>\nЧтобы просмотреть у кого есть доступ к вашему календарю, нажмите - <b>/Check_Accesses</b>"""

Action_for_user = """
    Давайте перейдём к календарю.\nЧтобы запросить доступ к календарю директора, нажмите - <b>/Ask_for_access</b>"""

Action_for_non_auth = """
    Вы не авторизованы, поэтому я не могу запросить доступ к каледнарю.\nПожалуйста авторизуйтесь - <b>/Authorize</b> или остановите бота - <b>/Cancel</b>"""

Action_for_reset = """
    Вы прервали работу Бота!\nБот приостановлен, для перезапуска нажмите кнопку ниже ↓"""

Text_for_Ask = """
    Вы отправили запрос на доступ\nОжидайте ответ от Директора"""


@dp.message_handler(commands=['Cancel'])
async def cmd_cancel(message: types.Message):
    await message.reply(text=Action_for_reset, parse_mode='HTML', reply_markup= reactivate_kb)
    await UserStates.INACTIVE.set()


@dp.message_handler(commands=['Reactivate_bot'], state=UserStates.INACTIVE)
async def reactivate_bot(message: types.Message):
    await message.answer('Бот перезапущен')
    await message.answer(text= Action_for_start, parse_mode = 'HTML', reply_markup=get_kb(0,0))
    await UserStates.ACTIVE.set()


@dp.message_handler(commands=['Start'])
async def cmd_start(message: types.Message) -> None:
    await message.answer(text = Action_for_start, parse_mode='HTML', reply_markup=get_kb(0, 0))


@dp.message_handler(commands=['Authorize'])
async def cmd_create(message: types.Message) -> None:
    global user
    user = User()
    user_id = int(message.from_user.id)

    if check_telegram_id(user_id):
        await message.answer("Вы уже подключены, авторизовываться не надо")
        user_dict = get_user_by_telegram(user_id)
        user.update_all(user_dict['name'], user_dict['surname'], user_dict['oauth_token'], user_dict['email'], user_id)

        if user_dict['role'] == 'director':
            global owner
            owner = user.change_for_owner()
            await message.answer(text = Action_for_owner, parse_mode='HTML', reply_markup=get_kb(1, 1))
        else:
            await message.answer(text = Action_for_user, parse_mode='HTML', reply_markup=get_kb(1, 0))

    else:
        auth_url = f'https://oauth.yandex.ru/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}'
        await message.answer(text=f'Давайте привяжем вас к вашему аккаунту.\nДля этого авторизуйтесь по ссылке:\n{auth_url}')
        await message.answer(text=f'Далее отправьте мне код для подтверждения') 
        await ProfileStatesGroup.code.set()


@dp.message_handler(lambda message: not message.text.isdigit() or int(message.text) < 1000000 or int(message.text) > 9999999, state=ProfileStatesGroup.code)
async def code_error_handler(message: types.Message) -> None:
    await message.answer(text='Неправильный формат ввода')


@dp.message_handler(state=ProfileStatesGroup.code)
async def code_handler(message: types.Message, state: FSMContext) -> None:
    await message.answer(text='Код обрабатывается')
    data = {
    'grant_type': 'authorization_code',
    'code': message.text,
    'client_id': client_id,
    'client_secret': client_secret,
    }
    token_url = 'https://oauth.yandex.ru/token'
    response = requests.post(token_url, data=data)
    token_data = response.json()
    access_token = token_data.get('access_token')
    headers = {
    'Authorization': f'OAuth {access_token}',
    }

    url = 'https://login.yandex.ru/info'

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        global user_info, user, flag
        user.update_token(access_token)
        user_info = response.json()
        if not flag:
            add_info('customer', CUSTOMER_COLS, [message.from_user.id, access_token, user_info['default_email'], user_info['first_name'], user_info['last_name'], 'director'])
            flag = 1
        else:
            add_info('customer', CUSTOMER_COLS, [message.from_user.id, access_token, user_info['default_email'], user_info['first_name'], user_info['last_name'], 'user'])
        await message.answer(text=f'{user_info}')
        director_id = get_director_id()
        if director_id is not None:
            if message.from_user.id == director_id:
                await message.answer(text = Action_for_owner, parse_mode='HTML', reply_markup=get_kb(1, 1))
            else:
                await message.answer(text = Action_for_user, parse_mode='HTML', reply_markup=get_kb(1, 0))
                await state.finish()
    else:
        await message.answer(text='Неверный код')
        await state.finish()



@dp.message_handler(commands=['Check_Calendar'])
async def check_calendar(message: types.Message):
    await message.reply(text='This feauture is coming soon!')
    pass

@dp.message_handler(commands=['Check_Accesses'])
async def check_access(message: types.Message):
    

    pass


@dp.message_handler(commands=['Ask_for_Access'])
async def ask_for_access(message: types.Message):
    global user
    global owner
    owner = director_create()
    if owner is not None:
        await message.answer(text=Text_for_Ask)
        await bot.send_message(chat_id = owner.id, text=f'Вам пришёл запрос на доступ к вашему графику от {user.name} {user.surname} из {user.company}, {user.id}', reply_markup=get_owner_choice_kb())
    else:
        await message.answer(text='Директора на данный момент в базе нет')


@dp.callback_query_handler(text='no_access')
async def nine_to_ten_handler(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)
    global owner


    await callback.answer()

@dp.callback_query_handler(text='encrypted')
async def encrypted_handler(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)
    # await message.reply(text=f'На сколько дней вы хотите дать доступ?', reply_markup=get_day_choice_kb())
    global owner


    await callback.answer()


@dp.callback_query_handler(text='full_access')
async def full_access_handler(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)
    # await message.reply(text=f'На сколько дней вы хотите дать доступ?', reply_markup=get_day_choice_kb())
    global owner


    await callback.answer()



@dp.callback_query_handler(text='one')
async def one_day_handler(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)
    

    await callback.answer()

@dp.callback_query_handler(text='seven')
async def seven_days_handler(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)
    

    await callback.answer()

@dp.callback_query_handler(text='fourteen')
async def fourteen_days_handler(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)
    

    await callback.answer()

@dp.callback_query_handler(text='thirty')
async def thirty_days_handler(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)
    

    await callback.answer()

@dp.callback_query_handler(text='own_choice')
async def own_choice_handler(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)
    await bot.send_message(text='На сколько дней вы хотите дать доступ?')

    await callback.answer()




@dp.message_handler(lambda message: not message.text.isdigit())
async def own_choice_message_handler(message: types.Message, state: FSMContext):
    await bot.send_message(text=f'Доступ предоставлен на {message.text} дня/дней', reply_markup= None)
    await state.finish()




# @dp.callback_query_handler(text='5')
# async def four_to_fif_handler(callback: types.CallbackQuery):
#     await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)
#     await callback.message.answer(text=f'Вы зарегистрировались на промежуток {times[5]}')

#     global user
#     user.orders = give_user_number_orders(callback.from_user.id)
#     user.orders -= 1
#     change_number_orders(callback.from_user.id, user.orders)
    
#     washer_id = change_free_time_by_first(times[5], False)
#     await callback.message.answer(text = f'Номер вашей машинки - {washer_id}')

#     await callback.answer()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)