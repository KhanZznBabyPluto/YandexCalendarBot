import asyncio
import hashlib
import requests
import datetime
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.dispatcher import FSMContext
from aiogram import types, executor, Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State

from bot_db import *
from bot_func import *
from bot_yapi import *
from bot_token import TOKEN_API, client_id, client_secret, redirect_uri
from bot_keyboard import url, url_pass, get_kb, get_owner_choice_kb, get_day_choice_kb, get_accesses_kb

logging.basicConfig(filename='bot.log', level=logging.INFO)

storage = MemoryStorage()
bot = Bot(TOKEN_API)
dp = Dispatcher(bot, storage=storage)

users_calls = {}

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
    Давайте перейдём к календарю.\nЧтобы получить свой - <b>/Check_Calendar</b>\nЧтобы проверить предоставленные доступы - <b>/Check_Accesses</b>\nЧтобы запросить доступ к чужому календарю, нажмите <b>/Ask_for_access</b>\nЧтобы получить календарь другого пользователя - <b>/Get_User_Calendar</b>\nЧтобы изменить предоставленный доступ - <b>/Change_Access</b>"""

Action_for_non_auth = """
    Вы не авторизованы, поэтому я не могу запросить доступ к каледнарю.\nПожалуйста авторизуйтесь - <b>/Authorize</b> или остановите бота - <b>/Cancel</b>"""

Action_for_reset = """
    Вы прервали работу Бота!\nБот приостановлен, для перезапуска нажмите кнопку ниже ↓"""

Text_for_Ask = """
    Вы отправили запрос на доступ\nОжидайте ответ от пользователя"""

Text_Wrong_Format = """
    Неправильный формат. Повторите ввод"""

Text_Wrong_Password = """
    Вы зарегистрировались через неправильный пароль. Введите его ещё раз или введите <b>/Cancel</b>"""



@dp.message_handler(commands=['Cancel'])
async def cmd_cancel(message: types.Message):
    await message.answer('Дейтсвие отменено!')
    # await UserStates.INACTIVE.set()
    user_id = message.from_user.id
    if await check_telegram_id(user_id):
        await message.answer(text = Action_for_user, parse_mode='HTML', reply_markup=get_kb(1))
    else:
        await message.answer(text = Action_for_start, parse_mode='HTML', reply_markup=get_kb(0))
    # await UserStates.ACTIVE.set()


@dp.message_handler(commands=['Start'])
async def cmd_start(message: types.Message) -> None:
    user_id = message.from_user.id
    if await check_telegram_id(user_id):
        await message.answer(text = Action_for_user, parse_mode='HTML', reply_markup=get_kb(1))
    else:
        await message.answer(text = Action_for_start, parse_mode='HTML', reply_markup=get_kb(0))


@dp.message_handler(commands=['Authorize'])
async def cmd_create(message: types.Message) -> None:
    user_id = message.from_user.id
    if await check_telegram_id(user_id):
        await message.answer("Вы уже подключены, авторизовываться не надо")
        await message.answer(text = Action_for_user, parse_mode='HTML', reply_markup=get_kb(1))
    else:
        await message.answer(text=f'Давайте привяжем вас к вашему аккаунту.\nДля этого авторизуйтесь:', reply_markup=url)
        await message.answer(text=f'Далее отправьте мне код для подтверждения') 
        await ProfileStatesGroup.code.set()


@dp.message_handler(lambda message: not message.text.isdigit() or int(message.text) < 1000000 or int(message.text) > 9999999, state=ProfileStatesGroup.code)
async def code_error_handler(message: types.Message) -> None:
    await message.answer(text=Text_Wrong_Format, parse_mode='HTML')

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
        await add_info('customer', CUSTOMER_COLS, [message.from_user.id, access_token, user_info['default_email'], user_info['first_name'], user_info['last_name'], user_info['login']])
        await message.answer(text = Action_for_user, parse_mode='HTML', reply_markup=get_kb(1))
        await state.finish()
    else:
        await message.answer(text='Неверный код')
        await state.finish()



@dp.message_handler(commands=['Check_Calendar'])
async def check_calendar(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_dict = await get_user_by_telegram(user_id)
    if user_dict['password'] is None:
        await message.answer(text='Для того, чтобы получить календарь, перейдите по ссылке, установите пароль на календарь:', reply_markup=url_pass)
        await message.answer(text=f'Далее отправьте мне код для подтверждения')
        await ProfileStatesGroup.code_2.set()
    else:
        info_dict = await get_events(user_dict['customer_id'])
        if len(info_dict) != 0:
            string = 'Список дел на сегодня:\n'
            i = 1
            for event in info_dict:
                name = event['event_name']
                # name = name.encode('latin-1').decode('utf-8')
                start = event['event_start'].strftime("%H:%M")
                end = event['event_end'].strftime("%H:%M")
                string += f'{i}: {name} с {start} до {end}\n'
                i += 1
            await message.answer(text=string)
            await state.finish()
        else:
            await message.answer(text='Запланированных дел нет')
            await state.finish()



@dp.message_handler(commands=['Cancel'], state=ProfileStatesGroup.code_2)
async def cmd_cancel_code_2(message: types.Message, state: FSMContext):
    await message.answer('Дейтсвие отменено!')
    # await UserStates.INACTIVE.set()
    user_id = message.from_user.id
    if await check_telegram_id(user_id):
        await message.answer(text = Action_for_user, parse_mode='HTML', reply_markup=get_kb(1))
    else:
        await message.answer(text = Action_for_start, parse_mode='HTML', reply_markup=get_kb(0))
    await state.finish()
    # await UserStates.ACTIVE.set()


@dp.message_handler(state=ProfileStatesGroup.code_2)
async def login_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_dict = await get_user_by_telegram(user_id)
    user_hash = hashlib.md5(str(user_id).encode()).hexdigest()
    res = await get_event_yandex_info(user_dict['email'], user_dict['login'], message.text)
    if res is None:
        await message.answer(text=Text_Wrong_Password, parse_mode='HTML')
        await ProfileStatesGroup.code_2.set()
    else:
        today = datetime.date.today()
        res = 'ok'
        if user_hash not in users_calls:
            users_calls[user_hash] = today
            res = await update_if_changed(user_dict['customer_id'], user_dict['email'], user_dict['login'], message.text)
        elif users_calls[user_hash] < today:
            users_calls[user_hash] = today
            res = await update_if_changed(user_dict['customer_id'], user_dict['email'], user_dict['login'], message.text)
        if res == None:
            await message.answer(text=Text_Wrong_Password, parse_mode='HTML')
            await ProfileStatesGroup.code_2.set()
        else:
          await add_password(user_dict['customer_id'], message.text)
          await message.answer(text='Пароль добавлен')
          info_dict = await get_events(user_dict['customer_id'])
          if len(info_dict) != 0:
              string = 'Список дел на сегодня:\n'
              i = 1
              for event in info_dict:
                  name = event['event_name']
                  # name = name.encode('latin-1').decode('utf-8')
                  start = event['event_start'].strftime("%H:%M")
                  end = event['event_end'].strftime("%H:%M")
                  string += f'{i}: {name} с {start} до {end}\n'
                  i += 1
              await message.answer(text=string)
              await state.finish()
          else:
              await message.answer(text='Запланированных дел нет')
              await state.finish()



@dp.message_handler(commands=['Check_Accesses'])
async def check_own_access(message: types.Message):
    user_dict = await get_user_by_telegram(message.from_user.id)
    accesses_dict = await get_accesses(user_dict['customer_id'])
    if accesses_dict is not None:
        flag = 1
        for access in accesses_dict:
            if access['type'] != 'no':
                flag = 0
                break
        if not flag:
            string = 'Вот список доступов:\n'
            for access in accesses_dict:
                name, surname, email, type_access, date, user_id = access['name'], access['surname'], access['email'], access['type'], access['end_time'], access['telegram_id']
                username = await get_username_by_id(user_id)
                if username:
                    if type_access == 'enc':
                        string += f'{name} {surname}, {email}, @{username}.\nНеполный доступ до {date}\n'
                    elif type_access == 'full':
                        string += f'{name} {surname}, {email}, @{username}.\nПолный доступ до {date}\n'
                else:
                    if type_access == 'enc':
                        string += f'{name} {surname}, {email}.\nНеполный доступ до {date}\n'
                    elif type_access == 'full':
                        string += f'{name} {surname}, {email}.\nПолный доступ до {date}\n'
        else:
            string = 'Вы никому доступа не давали'
        await message.answer(text=string)
    else:
        await message.answer(text='Вы никому доступа не давали')



@dp.message_handler(commands=['Ask_for_Access'])
async def ask_for_access(message: types.Message):
    await message.answer(text='К чьему календарю вы хотите получить доступ? Отправьте почту')
    await ProfileStatesGroup.email_rec.set()


@dp.message_handler(commands=['Cancel'], state=ProfileStatesGroup.email_rec)
async def cmd_cancel_email(message: types.Message, state: FSMContext):
    await message.answer('Дейтсвие отменено!')
    # await UserStates.INACTIVE.set()
    user_id = message.from_user.id
    if await check_telegram_id(user_id):
        await message.answer(text = Action_for_user, parse_mode='HTML', reply_markup=get_kb(1))
    else:
        await message.answer(text = Action_for_start, parse_mode='HTML', reply_markup=get_kb(0))
    await state.finish()
    # await UserStates.ACTIVE.set()


@dp.message_handler(state=ProfileStatesGroup.email_rec)
async def email_handler(message: types.Message, state: FSMContext):
    if not validate_email(message.text):
        await message.answer(text='Неправильный формат, повторите ввод либо нажмите - <b>/Cancel</b>', parse_mode='HTML')
        await ProfileStatesGroup.email_rec.set()
    else:
        rec_dict = await get_customer_by_email(message.text)
        send_dict = await get_user_by_telegram(message.from_user.id)
        if rec_dict is not None:
            name, surname, email = send_dict['name'], send_dict['surname'], send_dict['email']
            await bot.send_message(chat_id=rec_dict['telegram_id'], text=f'Вам пришёл запрос на доступ к вашему календарю от {name} {surname}, {email}', reply_markup=get_owner_choice_kb(message.from_user.id, 'give_access'))
            await message.answer(text=Text_for_Ask)
            await state.finish()
        else:
            await message.answer(text='Данный пользователь не зарегистрирован в боте')
            await state.finish()



@dp.callback_query_handler(text_startswith='no_access:')
async def no_access_handler(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)
    user_id, cmd, email = callback.data.split(":")[1:]
    today = datetime.date.today()
    type_access = 'no'

    if cmd == 'change_access':
        accesser_dict = await get_customer_by_email(email)
        accesser_id = accesser_dict['telegram_id']
        accesser_cust = accesser_dict['customer_id']
        my_dict = await get_user_by_telegram(callback.message.chat.id)
        my_cust = my_dict['customer_id']
        await update_requested(my_cust, accesser_cust)

        my_name, my_surname, my_email = my_dict['name'], my_dict['surname'], my_dict['email']

        await bot.send_message(chat_id=callback.message.chat.id, text='Вы закрыли доступ')
        await bot.send_message(chat_id=accesser_id, text=f'Пользователь {my_name} {my_surname}, {my_email} закрыл  вашдоступ')
            
        await update_access_end_time(my_cust, accesser_cust, type_access, today)


    else:
        await bot.send_message(chat_id=callback.message.chat.id, text='Вы не предоставили доступ')
        await bot.send_message(chat_id=user_id, text='Доступ не предоставлен')
        
        user_cust = await get_user_by_telegram(user_id)
        user_cust = user_cust['customer_id']
        owner_cust = await get_user_by_telegram(callback.message.chat.id)
        owner_cust = owner_cust['customer_id']


        access = await check_access(owner_cust, user_cust)
        if access is not None:
            await update_access_end_time(owner_cust, user_cust, type_access, today)
        else:
            await add_info('access', ACCESS_COLS, [owner_cust, user_cust, type_access, today])



@dp.callback_query_handler(text_startswith='encrypted:')
async def encrypted_handler(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)
    user_id, cmd, email = callback.data.split(":")[1:]
    if cmd == 'change_access':
        accesser_dict = await get_customer_by_email(email)
        accesser_id = accesser_dict['telegram_id']
        await bot.send_message(chat_id=user_id, text=f'На сколько дней вы хотите дать доступ?', reply_markup=get_day_choice_kb(accesser_id, 'enc', cmd))
    else:
        await bot.send_message(chat_id=callback.message.chat.id, text=f'На сколько дней вы хотите дать доступ?', reply_markup=get_day_choice_kb(user_id, 'enc', cmd))


@dp.callback_query_handler(text_startswith='full_access:')
async def full_access_handler(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)
    user_id, cmd, email = callback.data.split(":")[1:]
    if cmd == 'change_access':
        accesser_dict = await get_customer_by_email(email)
        accesser_id = accesser_dict['telegram_id']
        await bot.send_message(chat_id=user_id, text=f'На сколько дней вы хотите дать доступ?', reply_markup=get_day_choice_kb(accesser_id, 'full', cmd))
    else:
        await bot.send_message(chat_id=callback.message.chat.id, text=f'На сколько дней вы хотите дать доступ?', reply_markup=get_day_choice_kb(user_id, 'full', cmd))



@dp.callback_query_handler(lambda c: c.data.startswith('one'))
async def one_day_handler(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)

    user_id, type_access, days, cmd = callback.data.split(':')[1:]
    if cmd == 'change_access':
        my_dict = await get_user_by_telegram(callback.message.chat.id)
        my_cust = my_dict['customer_id']
        accesser_dict = await get_user_by_telegram(int(user_id))
        accesser_cust = accesser_dict['customer_id']
        end_dt = datetime.datetime.now() + datetime.timedelta(days=int(days))
        end_date = end_dt.date()
        await update_requested(my_cust, accesser_cust)

        my_name, my_surname, my_email = my_dict['name'], my_dict['surname'], my_dict['email']

        if type_access == 'enc':
            await bot.send_message(chat_id=callback.message.chat.id, text=f'Вы изменили доступ на неполный до {end_date}')
            await bot.send_message(chat_id=user_id, text=f'Пользователь {my_name} {my_surname}, {my_email} изменил ваш доступ на неполный до {end_date}')
        else:
            await bot.send_message(chat_id=callback.message.chat.id, text=f'Вы изменили доступ на полный до {end_date}')
            await bot.send_message(chat_id=user_id, text=f'Пользователь {my_name} {my_surname}, {my_email} изменил ваш доступ на полный до {end_date}')
        
        await update_access_end_time(my_cust, accesser_cust, type_access, end_date)

    else:
        user_cust = await get_user_by_telegram(int(user_id))
        user_cust = user_cust['customer_id']
        owner_cust = await get_user_by_telegram(callback.message.chat.id)
        owner_cust = owner_cust['customer_id']
        end_dt = datetime.datetime.now() + datetime.timedelta(days=int(days))
        end_date = end_dt.date()
        await update_requested(owner_cust, user_cust)

        await bot.send_message(chat_id=callback.message.chat.id, text=f'Вы предоставили доступ до {end_date}')
        await bot.send_message(chat_id=user_id, text=f'Вам предоставлен доступ до {end_date}')
        access = await check_access(owner_cust, user_cust)
        if access is not None:
            await update_access_end_time(owner_cust, user_cust, type_access, end_date)
        else:
            await add_info('access', ACCESS_COLS, [owner_cust, user_cust, type_access, end_date])


@dp.callback_query_handler(lambda c: c.data.startswith('seven'))
async def seven_days_handler(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)

    user_id, type_access, days, cmd = callback.data.split(':')[1:]
    if cmd == 'change_access':
        my_dict = await get_user_by_telegram(callback.message.chat.id)
        my_cust = my_dict['customer_id']
        accesser_dict = await get_user_by_telegram(int(user_id))
        accesser_cust = accesser_dict['customer_id']
        end_dt = datetime.datetime.now() + datetime.timedelta(days=int(days))
        end_date = end_dt.date()
        await update_requested(my_cust, accesser_cust)

        my_name, my_surname, my_email = my_dict['name'], my_dict['surname'], my_dict['email']

        if type_access == 'enc':
            await bot.send_message(chat_id=callback.message.chat.id, text=f'Вы изменили доступ на неполный до {end_date}')
            await bot.send_message(chat_id=user_id, text=f'Пользователь {my_name} {my_surname}, {my_email} изменил ваш доступ на неполный до {end_date}')
        else:
            await bot.send_message(chat_id=callback.message.chat.id, text=f'Вы изменили доступ на полный до {end_date}')
            await bot.send_message(chat_id=user_id, text=f'Пользователь {my_name} {my_surname}, {my_email} изменил ваш доступ на полный до {end_date}')
            
        await update_access_end_time(my_cust, accesser_cust, type_access, end_date)

    else:
        user_cust = await get_user_by_telegram(int(user_id))
        user_cust = user_cust['customer_id']
        owner_cust = await get_user_by_telegram(callback.message.chat.id)
        owner_cust = owner_cust['customer_id']
        end_dt = datetime.datetime.now() + datetime.timedelta(days=int(days))
        end_date = end_dt.date()
        await update_requested(owner_cust, user_cust)

        await bot.send_message(chat_id=callback.message.chat.id, text=f'Вы предоставили доступ до {end_date}')
        await bot.send_message(chat_id=user_id, text=f'Вам предоставлен доступ до {end_date}')
        access = await check_access(owner_cust, user_cust)
        if access is not None:
            await update_access_end_time(owner_cust, user_cust, type_access, end_date)
        else:
            await add_info('access', ACCESS_COLS, [owner_cust, user_cust, type_access, end_date])


@dp.callback_query_handler(lambda c: c.data.startswith('fourteen'))
async def fourteen_days_handler(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)

    user_id, type_access, days, cmd = callback.data.split(':')[1:]
    if cmd == 'change_access':
        my_dict = await get_user_by_telegram(callback.message.chat.id)
        my_cust = my_dict['customer_id']
        accesser_dict = await get_user_by_telegram(int(user_id))
        accesser_cust = accesser_dict['customer_id']
        end_dt = datetime.datetime.now() + datetime.timedelta(days=int(days))
        end_date = end_dt.date()
        await update_requested(my_cust, accesser_cust)

        my_name, my_surname, my_email = my_dict['name'], my_dict['surname'], my_dict['email']

        if type_access == 'enc':
            await bot.send_message(chat_id=callback.message.chat.id, text=f'Вы изменили доступ на неполный до {end_date}')
            await bot.send_message(chat_id=user_id, text=f'Пользователь {my_name} {my_surname}, {my_email} изменил ваш доступ на неполный до {end_date}')
        else:
            await bot.send_message(chat_id=callback.message.chat.id, text=f'Вы изменили доступ на полный до {end_date}')
            await bot.send_message(chat_id=user_id, text=f'Пользователь {my_name} {my_surname}, {my_email} изменил ваш доступ на полный до {end_date}')
            
        await update_access_end_time(my_cust, accesser_cust, type_access, end_date)

    else:
        user_cust = await get_user_by_telegram(int(user_id))
        user_cust = user_cust['customer_id']
        owner_cust = await get_user_by_telegram(callback.message.chat.id)
        owner_cust = owner_cust['customer_id']
        end_dt = datetime.datetime.now() + datetime.timedelta(days=int(days))
        end_date = end_dt.date()
        await update_requested(owner_cust, user_cust)

        await bot.send_message(chat_id=callback.message.chat.id, text=f'Вы предоставили доступ до {end_date}')
        await bot.send_message(chat_id=user_id, text=f'Вам предоставлен доступ до {end_date}')
        access = await check_access(owner_cust, user_cust)
        if access is not None:
            await update_access_end_time(owner_cust, user_cust, type_access, end_date)
        else:
            await add_info('access', ACCESS_COLS, [owner_cust, user_cust, type_access, end_date])


@dp.callback_query_handler(lambda c: c.data.startswith('thirty'))
async def thirty_days_handler(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)

    user_id, type_access, days, cmd = callback.data.split(':')[1:]
    if cmd == 'change_access':
        my_dict = await get_user_by_telegram(callback.message.chat.id)
        my_cust = my_dict['customer_id']
        accesser_dict = await get_user_by_telegram(int(user_id))
        accesser_cust = accesser_dict['customer_id']
        end_dt = datetime.datetime.now() + datetime.timedelta(days=int(days))
        end_date = end_dt.date()
        await update_requested(my_cust, accesser_cust)

        my_name, my_surname, my_email = my_dict['name'], my_dict['surname'], my_dict['email']

        if type_access == 'enc':
            await bot.send_message(chat_id=callback.message.chat.id, text=f'Вы изменили доступ на неполный до {end_date}')
            await bot.send_message(chat_id=user_id, text=f'Пользователь {my_name} {my_surname}, {my_email} изменил ваш доступ на неполный до {end_date}')
        else:
            await bot.send_message(chat_id=callback.message.chat.id, text=f'Вы изменили доступ на полный до {end_date}')
            await bot.send_message(chat_id=user_id, text=f'Пользователь {my_name} {my_surname}, {my_email} изменил ваш доступ на полный до {end_date}')
            
        await update_access_end_time(my_cust, accesser_cust, type_access, end_date)

    else:
        user_cust = await get_user_by_telegram(int(user_id))
        user_cust = user_cust['customer_id']
        owner_cust = await get_user_by_telegram(callback.message.chat.id)
        owner_cust = owner_cust['customer_id']
        end_dt = datetime.datetime.now() + datetime.timedelta(days=int(days))
        end_date = end_dt.date()
        await update_requested(owner_cust, user_cust)

        await bot.send_message(chat_id=callback.message.chat.id, text=f'Вы предоставили доступ до {end_date}')
        await bot.send_message(chat_id=user_id, text=f'Вам предоставлен доступ до {end_date}')
        access = await check_access(owner_cust, user_cust)
        if access is not None:
            await update_access_end_time(owner_cust, user_cust, type_access, end_date)
        else:
            await add_info('access', ACCESS_COLS, [owner_cust, user_cust, type_access, end_date])



@dp.message_handler(commands=['Change_Access'])
async def change_access(message: types.Message):
    user_dict = await get_user_by_telegram(message.from_user.id)
    accesses_dict = await get_accesses(user_dict['customer_id'])
    if accesses_dict is not None:
        flag = 1
        for access in accesses_dict:
            if access['type'] != 'no':
                flag = 0
                break
        if not flag:
            await message.answer(text='Чей доступ вы хотите изменить?', reply_markup=get_accesses_kb(accesses_dict, 'change_access'))
        else:
            await message.answer(text='Вы не можете изменить доступы, так как вы доступ никому не давали')    
    else:
        await message.answer(text='Вы не можете изменить доступы, так как вы доступ никому не давали')



@dp.message_handler(commands='Get_User_Calendar')
async def other_user_calendar(message: types.Message):
    user_dict = await get_user_by_telegram(message.from_user.id)
    user_cust = user_dict['customer_id']
    accesses_dict = await get_accesses_allowed(user_cust)
    if accesses_dict is not None:
        flag = 1
        for access in accesses_dict:
            if access['type'] != 'no':
                flag = 0
                break
        if not flag:
            await message.answer(text='Чей календарь вы хотите получить?', reply_markup=get_accesses_kb(accesses_dict, 'give_access'))
        else:
            await message.answer(text='У вас нет доступа ни к чьему календарю.')
    else:
        await message.answer(text='У вас нет доступа ни к чьему календарю.')


@dp.callback_query_handler(lambda callback_query: True)
async def handle_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    chosen_email, cmd = callback_query.data.split(':')
    rec_dict = await get_customer_by_email(chosen_email)
    rec_name, rec_surname, rec_email = rec_dict['name'], rec_dict['surname'], rec_dict['email']
    if cmd == 'change_access':
        await bot.send_message(chat_id=user_id, text=f'Какой доступ вы хотите дать пользователю {rec_name} {rec_surname}, {rec_email}?', reply_markup=get_owner_choice_kb(user_id, cmd, chosen_email))
    else:
        if rec_dict is not None:
            user_dict = await get_user_by_telegram(user_id)
            if rec_dict['password'] is None:
                await bot.send_message(chat_id=user_id, text='Пользователь не добавил свой календарь')
                await state.finish()
            else:
                access = await check_access(rec_dict['customer_id'], user_dict['customer_id'])
                end = access['end_time']
                if datetime.datetime.now() > end:
                    await bot.send_message(chat_id=user_id, text='Ваш доступ истёк. Запросите ещё раз через - <b>/Ask_for_Access</b>', parse_mode='HTML')
                    await state.finish()
                else:
                    info_dict = await get_events(rec_dict['customer_id'])
                    await update_requested(rec_dict['customer_id'], user_dict['customer_id'])
                    if len(info_dict) != 0:
                        if access['type'] == 'enc':
                            string = ''
                            i = 1
                            for event in info_dict:
                                start = event['event_start'].strftime("%H:%M")
                                end = event['event_end'].strftime("%H:%M")
                                string += f'{i}: Занят с {start} до {end}\n'
                                i += 1
                            await bot.send_message(chat_id=user_id, text=string)
                            await state.finish()
                        elif access['type'] == 'full':
                            string = 'Список дел на сегодня:\n'
                            i = 1
                            for event in info_dict:
                                name = event['event_name']
                                # name = name.encode('latin-1').decode('utf-8')
                                start = event['event_start'].strftime("%H:%M")
                                end = event['event_end'].strftime("%H:%M")
                                string += f'{i}: {name} с {start} до {end}\n'
                                i += 1
                            await bot.send_message(chat_id=user_id, text=string)
                            await state.finish()
                    else:
                        await bot.send_message(chat_id=user_id, text='У пользователя запланированных дел нет')
                        await state.finish()

async def updater_call():
    customers = await get_customers()
    for customer in customers:
        if customer['password'] is None:
            return
        flag = await update_if_changed(customer['customer_id'], customer['email'], customer['login'], customer['password'])

        if flag == None:
            return
        elif flag == True:
            accesses = await get_accesses(customer['customer_id'])
            if accesses is not None:
                customer_name = customer['name']
                customer_surname = customer['surname']
                customer_email = customer['email']
                for access in accesses:
                    if access['requested'] == True:
                        user_id = access['telegram_id']
                        if datetime.datetime.now() <= access['end_time']:
                            info_dict = await get_events(customer['customer_id'])
                            if len(info_dict) != 0:
                                if access['type'] == 'enc':
                                    string = ''
                                    i = 1
                                    for event in info_dict:
                                        start = event['event_start'].strftime("%H:%M")
                                        end = event['event_end'].strftime("%H:%M")
                                        string += f'{i}: С {start} до {end}\n'
                                        i += 1
                                elif access['type'] == 'full':
                                    string = ''
                                    i = 1
                                    for event in info_dict:
                                        name = event['event_name']
                                        # name = name.encode('latin-1').decode('utf-8')
                                        start = event['event_start'].strftime("%H:%M")
                                        end = event['event_end'].strftime("%H:%M")
                                        string += f'{i}: {name} с {start} до {end}\n'
                                        i += 1
                                await bot.send_message(chat_id=user_id, text=f'События у пользователя {customer_name} {customer_surname}, {customer_email} были изменены.\nВот новые:\n{string}')
                            else:
                                await bot.send_message(chat_id=user_id, text=f'События у пользователя {customer_name} {customer_surname}, {customer_email} были изменены. У пользователя запланированных дел нет')


async def scheduler():
    while True:
        await updater_call()
        await asyncio.sleep(60)


async def run_scheduler():
  scheduler = AsyncIOScheduler()
  scheduler.add_job(refresh_requests, 'cron', day_of_week='*', hour=0, minute=0, second=1)
  scheduler.start()

  while True:
    await asyncio.sleep(1)


async def on_startup(dispatcher):
    loop = asyncio.get_event_loop()
    loop.create_task(scheduler())
    loop.create_task(run_scheduler())



async def get_username_by_id(user_id):
    try:
        user = await bot.get_chat_member(chat_id=user_id, user_id=user_id)
        username = user.user.username
        return username
    except Exception as e:
        logging.error(f"Error getting username: {e}")
        return None




if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(on_startup(dp))
    executor.start_polling(dp, skip_updates=True)