import re
import arrow
import requests
import asyncio
import datetime
from aiogram import types, executor, Bot, Dispatcher
from aiogram.types import CallbackQuery
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

from bot_postgre import *
from bot_token import TOKEN_API, client_id, client_secret, redirect_uri
from bot_keyboard import url, url_pass, reactivate_kb, get_kb, get_owner_choice_kb, get_day_choice_kb

storage = MemoryStorage()
bot = Bot(TOKEN_API)
dp = Dispatcher(bot, storage=storage)


class UserStates(StatesGroup):
    ACTIVE = State()
    INACTIVE = State() 


class ProfileStatesGroup(StatesGroup):
    code = State()
    code_2 = State()
    email_rec = State()
    email_cal_rec = State()


Action_for_start = """
    Дорбро пожаловать!\nЧтобы привязать ваш аккаунт, нажмите - <b>/Authorize</b>"""

Action_for_user = """
    Давайте перейдём к календарю.\nЧтобы запросить доступ к чужому календарю, нажмите \n<b>/Ask_for_access</b>\nЧтобы получить свой - <b>/Check_Calendar</b>\nЧтобы проверить предоставленные доступы - <b>/Check_Accesses</b>"""

Action_for_non_auth = """
    Вы не авторизованы, поэтому я не могу запросить доступ к каледнарю.\nПожалуйста авторизуйтесь - <b>/Authorize</b> или остановите бота - <b>/Cancel</b>"""

Action_for_reset = """
    Вы прервали работу Бота!\nБот приостановлен, для перезапуска нажмите кнопку ниже ↓"""

Text_for_Ask = """
    Вы отправили запрос на доступ\nОжидайте ответ от пользователя"""


async def on_startup(dp):
    print('Bot has been started')


@dp.message_handler(commands=['Cancel'])
async def cmd_cancel(message: types.Message):
    await message.reply(text=Action_for_reset, parse_mode='HTML', reply_markup= reactivate_kb)
    await UserStates.INACTIVE.set()


@dp.message_handler(commands=['Reactivate_bot'], state=UserStates.INACTIVE)
async def reactivate_bot(message: types.Message):
    await message.answer('Бот перезапущен')
    user_id = int(message.from_user.id)
    if check_telegram_id(user_id):
        await message.answer(text = Action_for_user, parse_mode='HTML', reply_markup=get_kb(1))
    else:
        await message.answer(text = Action_for_start, parse_mode='HTML', reply_markup=get_kb(0))
    await UserStates.ACTIVE.set()


@dp.message_handler(commands=['Start'])
async def cmd_start(message: types.Message) -> None:
    user_id = int(message.from_user.id)
    if check_telegram_id(user_id):
        await message.answer(text = Action_for_user, parse_mode='HTML', reply_markup=get_kb(1))
    else:
        await message.answer(text = Action_for_start, parse_mode='HTML', reply_markup=get_kb(0))


@dp.message_handler(commands=['Authorize'])
async def cmd_create(message: types.Message) -> None:
    user_id = int(message.from_user.id)
    if check_telegram_id(user_id):
        await message.answer("Вы уже подключены, авторизовываться не надо")
        await message.answer(text = Action_for_user, parse_mode='HTML', reply_markup=get_kb(1))
    else:
        await message.answer(text=f'Давайте привяжем вас к вашему аккаунту.\nДля этого авторизуйтесь:', reply_markup=url)
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
        user_info = response.json()
        add_info('customer', CUSTOMER_COLS, [message.from_user.id, access_token, user_info['default_email'], user_info['first_name'], user_info['last_name'], 'user', user_info['login']])
        await message.answer(text = Action_for_user, parse_mode='HTML', reply_markup=get_kb(1))
        await state.finish()
    else:
        await message.answer(text='Неверный код')
        await state.finish()



@dp.message_handler(commands=['Check_Calendar'])
async def check_calendar(message: types.Message, state: FSMContext):
    user_dict = get_user_by_telegram(message.from_user.id)
    if user_dict['password'] is None:
        await message.answer(text='Для того, чтобы получить календарь, перейдите по ссылке, установите пароль на календарь:', reply_markup=url_pass)
        await message.answer(text=f'Далее отправьте мне код для подтверждения')
        await ProfileStatesGroup.code_2.set()
    else:
        info_dict = get_event_info(user_dict['email'], user_dict['login'], user_dict['password'])
        if info_dict is not None:
            if len(info_dict) != 0:
                string = ''
                i = 1
                for event in info_dict:
                    name = event['event']
                    name = name.encode('latin-1').decode('utf-8')
                    start = event['start']
                    start = arrow.get(start).format("HH:mm")
                    end = event['end']
                    end = arrow.get(end).format("HH:mm")
                    string += f'{i}: {name} с {start} до {end}\n'
                    i += 1
                await message.answer(text=string)
                await state.finish()
            else:
                await message.answer(text='Запланированных дел нет')
                await state.finish()
        else:
            await message.answer(text='Вы зарегистрировались через неправильный пароль. Введите его ещё раз')
            await ProfileStatesGroup.code_2.set()


@dp.message_handler(state=ProfileStatesGroup.code_2)
async def login_handler(message: types.Message, state: FSMContext):
    user_cust = get_cust_by_tel(message.from_user.id)
    add_password(user_cust, message.text)
    await message.answer(text='Пароль добавлен, теперь нажмите <b>/Check_Calendar</b> ещё раз', parse_mode='HTML', reply_markup=get_kb(1))
    await state.finish()


@dp.message_handler(commands=['Check_Accesses'])
async def check_own_access(message: types.Message):
    user_dict = get_user_by_telegram(message.from_user.id)
    accesses_dict = get_accesses(user_dict['customer_id'])
    if accesses_dict is not None:
        string = 'Вот список доступов:\n'
        for access in accesses_dict:
            name, surname, email, type_access, date = access['name'], access['surname'], access['email'], access['type'], access['end_time']
            if type_access == 'enc':
                string += f'{name} {surname}, {email}. Неполный доступ до {date}\n'
            else:
                string += f'{name} {surname}, {email}. Полный доступ до {date}\n'
        await message.answer(text=string)
    else:
        await message.answer(text='Вы никому доступа не давали')



@dp.message_handler(commands=['Ask_for_Access'])
async def ask_for_access(message: types.Message):
    await message.answer(text='К чьему календарю вы хотите получить доступ? Отпрайте email')
    await ProfileStatesGroup.email_rec.set()


@dp.message_handler(state=ProfileStatesGroup.email_rec)
async def email_handler(message: types.Message, state: FSMContext):
    if not validate_email(message.text):
        await message.answer(text='Неправильный формат, повторите ввод')
        await ProfileStatesGroup.email_rec.set()
    else:
        rec_dict = get_customer_by_email(message.text)
        if rec_dict is not None:
            await bot.send_message(chat_id=rec_dict['telegram_id'], text=Text_for_Ask, reply_markup=get_owner_choice_kb(message.from_user.id))
            await message.answer(text='Ожидайте подтверждения от пользователя')
            await state.finish()
        else:
            await message.answer(text='Данный пользователь не зарегистрирован в боте')
            await state.finish()



@dp.message_handler(commands='Get_User_Calendar')
async def director_calendar(message: types.Message):
    await message.answer(text='Чей календарь вы хотите получить? Отправьте почту')
    await ProfileStatesGroup.email_cal_rec.set()


@dp.message_handler(state=ProfileStatesGroup.email_cal_rec)
async def email_cal_rec(message:types.Message, state: FSMContext):
    if not validate_email(message.text):
        await message.answer(text='Неправильный формат, повторите ввод либо нажмите - <b>/Cancel</b>', parse_mode='HTML')
        await ProfileStatesGroup.email_cal_rec.set()
    else:
        rec_dict = get_customer_by_email(message.text)
        if rec_dict is not None:
            user_dict = get_user_by_telegram(message.from_user.id)
            if user_dict['password'] is None:
                await message.answer(text='Пользователь не добавил свой календарь')
                await state.finish()
            else:
                access = check_access(rec_dict['customer_id'], user_dict['customer_id'])
                end = access['end_time']
                if datetime.datetime.now() > end:
                    await message.answer(text='Ваш доступ истёк. Запросите ещё раз через - <b>/Ask_for_Access</b>', parse_mode='HTML')
                    await state.finish()
                else:
                    if access is not None:
                        info_dict = get_event_info(rec_dict['email'], rec_dict['login'], rec_dict['password'])
                        if len(info_dict) != 0:
                            if access['type'] == 'enc':
                                string = ''
                                i = 1
                                for event in info_dict:
                                    start = event['start']
                                    start = arrow.get(start).format("HH:mm")
                                    end = event['end']
                                    end = arrow.get(end).format("HH:mm")
                                    string += f'{i}: С {start} до {end}\n'
                                    i += 1
                                await message.answer(text=string)
                                await state.finish()
                            else:
                                string = ''
                                i = 1
                                for event in info_dict:
                                    name = event['event']
                                    name = name.encode('latin-1').decode('utf-8')
                                    start = event['start']
                                    start = arrow.get(start).format("HH:mm")
                                    end = event['end']
                                    end = arrow.get(end).format("HH:mm")
                                    string += f'{i}: {name} с {start} до {end}\n'
                                    i += 1
                                await message.answer(text=string)
                                await state.finish()
                        else:
                            await message.answer(text='У пользователя запланированных дел нет')
                            await state.finish()
                    else:
                        await message.answer(text='У вас нет доступа')
                        await state.finish()
        else:
            await message.answer(text='Данный пользователь ещё не зарегестрировался в боте')
            await state.finish()





@dp.callback_query_handler(text_startswith='no_access:')
async def no_access_handler(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)
    user_id = callback.data.split(":")[1]
    await bot.send_message(chat_id=callback.message.chat.id, text='Вы не предоставили доступ')
    await bot.send_message(chat_id=user_id, text='Доступ не предоставлен')


@dp.callback_query_handler(text_startswith='encrypted:')
async def encrypted_handler(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)
    user_id = callback.data.split(":")[1]
    await bot.send_message(chat_id=callback.message.chat.id, text=f'На сколько дней вы хотите дать доступ?', reply_markup=get_day_choice_kb(user_id, 'enc'))


@dp.callback_query_handler(text_startswith='full_access:')
async def full_access_handler(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)
    user_id = callback.data.split(":")[1]
    await bot.send_message(chat_id=callback.message.chat.id, text=f'На сколько дней вы хотите дать доступ?', reply_markup=get_day_choice_kb(user_id, 'full'))



@dp.callback_query_handler(lambda c: c.data.startswith('one'))
async def one_day_handler(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)

    user_id, type_access, days = callback.data.split(':')[1:]
    user_cust = get_cust_by_tel(user_id)
    owner_cust = get_cust_by_tel(callback.message.chat.id)
    end_dt = datetime.datetime.now() + datetime.timedelta(days=int(days))
    end_date = end_dt.date()

    await bot.send_message(chat_id=callback.message.chat.id, text=f'Вы предоставили доступ до {end_date}')
    await bot.send_message(chat_id=user_id, text=f'Вам предоставлен доступ до {end_date}')
    access = check_access(owner_cust, user_cust)
    if access is not None:
        update_access_end_time(owner_cust, user_cust, type_access, end_date)
    else:
        add_info('access', ACCESS_COLS, [owner_cust, user_cust, type_access, end_date])


@dp.callback_query_handler(lambda c: c.data.startswith('seven'))
async def seven_days_handler(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)

    user_id, type_access, days = callback.data.split(':')[1:]
    user_cust = get_cust_by_tel(user_id)
    owner_cust = get_cust_by_tel(callback.message.chat.id)
    end_dt = datetime.datetime.now() + datetime.timedelta(days=int(days))
    end_date = end_dt.date()

    await bot.send_message(chat_id=callback.message.chat.id, text=f'Вы предоставили доступ до {end_date}')
    await bot.send_message(chat_id=user_id, text=f'Вам предоставлен доступ до {end_date}')
    access = check_access(owner_cust, user_cust)
    if access is not None:
        update_access_end_time(owner_cust, user_cust, type_access, end_date)
    else:
        add_info('access', ACCESS_COLS, [owner_cust, user_cust, type_access, end_date])


@dp.callback_query_handler(lambda c: c.data.startswith('fourteen'))
async def fourteen_days_handler(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)
    
    user_id, type_access, days = callback.data.split(':')[1:]
    user_cust = get_cust_by_tel(user_id)
    owner_cust = get_cust_by_tel(callback.message.chat.id)
    end_dt = datetime.datetime.now() + datetime.timedelta(days=int(days))
    end_date = end_dt.date()

    await bot.send_message(chat_id=callback.message.chat.id, text=f'Вы предоставили доступ до {end_date}')
    await bot.send_message(chat_id=user_id, text=f'Вам предоставлен доступ до {end_date}')
    access = check_access(owner_cust, user_cust)
    if access is not None:
        update_access_end_time(owner_cust, user_cust, type_access, end_date)
    else:
        add_info('access', ACCESS_COLS, [owner_cust, user_cust, type_access, end_date])


@dp.callback_query_handler(lambda c: c.data.startswith('thirty'))
async def thirty_days_handler(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)
    
    user_id, type_access, days = callback.data.split(':')[1:]
    user_cust = get_cust_by_tel(user_id)
    owner_cust = get_cust_by_tel(callback.message.chat.id)
    end_dt = datetime.datetime.now() + datetime.timedelta(days=int(days))
    end_date = end_dt.date()   

    await bot.send_message(chat_id=callback.message.chat.id, text=f'Вы предоставили доступ до {end_date}')
    await bot.send_message(chat_id=user_id, text=f'Вам предоставлен доступ до {end_date}')
    access = check_access(owner_cust, user_cust)
    if access is not None:
        update_access_end_time(owner_cust, user_cust, type_access, end_date)
    else:
        add_info('access', ACCESS_COLS, [owner_cust, user_cust, type_access, end_date])


@dp.callback_query_handler(lambda c: c.data.startswith('own_choice'))
async def own_choice_handler(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)
    # await callback.reply(text='На сколько дней вы хотите дать доступ? Введите количество дней.')
    await callback.reply(text='This feature is coming soon!')



# @dp.message_handler(lambda message: not message.text.isdigit())
# async def own_choice_message_handler(message: types.Message):
#     await message.reply(text=f'Доступ предоставлен на {message.text} дня/дней', reply_markup= None)
    
#     user_id, type_access = callback.data.split(':')[1:]
#     user_cust = get_cust_by_tel(user_id)
#     director_cust = get_cust_by_tel(callback.message.chat.id)
#     end_dt = datetime.now() + timedelta(days=30)   

#     add_info('access', ACCESS_COLS, [director_cust, user_cust, type_access, end_dt])
    
#     await state.finish()


# @dp.message_handler(state=ProfileStatesGroup.send)
# async def access_handler(self, update, context, user_id, type_access, end_dt, state : FSMContext):
#     await bot.send_message(chat_id=user_id, text=f'Вам дан доступ {type_access} до {end_dt}')
#     await state.finish()



if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(on_startup(dp))
    executor.start_polling(dp, skip_updates=True)