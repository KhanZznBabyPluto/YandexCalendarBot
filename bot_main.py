from aiogram import types, executor, Bot, Dispatcher
from aiogram.types import CallbackQuery
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from bot_keyboard import get_kb, get_owner_kb, get_owner_choice_kb, reactivate_kb

from bot_token import TOKEN_API
from bot_classes import User, Director
from bot_mongo import *


users_col = connect_collection("users")
book_col = connect_collection("book")
user = User()

storage = MemoryStorage()
# PROXY_URL = "http://proxy.server:3128"
# bot = Bot(token=TOKEN_API, proxy=PROXY_URL)
bot = Bot(TOKEN_API)
dp = Dispatcher(bot, storage=storage)


class UserStates(StatesGroup):
    ACTIVE = State()
    INACTIVE = State() 

class ProfileStatesGroup(StatesGroup):
    name = State()
    surname = State()
    company = State()


Action_for_start = """
    Дорбро пожаловать!\nЧтобы привязать ваш аккаунт, нажмите - <b>/Authorize</b>"""

Action_for_owner = """
    Давайте перейдём к планированию\nЧтобы просмотреть ваш календарь на сегодня, нажмите - <b>/Check_Calendar</b>\nЧтобы просмотреть у кого есть доступ к вашему календарю, нажмите - <b>/Check_Accesses</b>"""

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
    await message.answer(text= Action_for_start, parse_mode = 'HTML', reply_markup=get_kb())
    await UserStates.ACTIVE.set()


@dp.message_handler(commands=['Start'])
async def cmd_start(message: types.Message) -> None:
    await message.answer(text = Action_for_start, parse_mode='HTML', reply_markup=get_kb())


@dp.message_handler(commands=['Authorize'])
async def cmd_create(message: types.Message) -> None:
    global user
    user = User()
    if check_key(["id"], [message.from_user.id]):
        await message.answer("Вы уже подключены, авторизовываться не надо")
        user.update_name(give_name_by_id(message.from_user.id), message.from_user.id)

        if check_key(["id", "class"], [message.from_user.id, 'Director']):
            global owner
            owner = user.change_for_owner()
            await message.answer(text = Action_for_owner, parse_mode='HTML', reply_markup=get_kb(1, 1))
        else:
            await message.answer(text = Action_for_user, parse_mode='HTML', reply_markup=get_kb(1, 0))

    else:
        await message.answer("Давайте привяжем вас к вашему аккаунту. Введите ваше имя")
        await ProfileStatesGroup.name.set() 


@dp.message_handler(lambda message: not message.text, state=ProfileStatesGroup.name)
async def check_name(message: types.Message):
    await message.reply('Это не имя!')

@dp.message_handler(content_types=['text'], state=ProfileStatesGroup.name)
async def load_name(message: types.Message) -> None:
    global user
    user.update_name(message.text, message.from_user.id)
    await message.answer('Теперь отправьте свою фамилию')
    await ProfileStatesGroup.next()



@dp.message_handler(lambda message: not message.text, state=ProfileStatesGroup.surname)
async def check_surname(message: types.Message):
    await message.reply('Это не фамилия!')

@dp.message_handler(state=ProfileStatesGroup.surname)
async def load_surname(message: types.Message) -> None:
    global user
    user.update_surname(message.text)
    await message.answer('Введите название вашей компании')
    await ProfileStatesGroup.next()


@dp.message_handler(lambda message: not message.text, state=ProfileStatesGroup.company)
async def check_company(message: types.Message):
    await message.reply('Это не название!')

@dp.message_handler(state=ProfileStatesGroup.company)
async def load_company(message: types.Message) -> None:
    global user
    user.update_company(message.text)
    await message.answer('Если вы владелец календаря, введите кодовое слово')
    await ProfileStatesGroup.next()


@dp.message_handler(lambda message: message.text)
async def check_owner(message: types.Message, state: FSMContext) -> None:
    global user
    if message.text == 'Director':
        global owner
        owner = user.change_for_owner()
        add_info(owner.name, owner.surname, owner.company, owner.id, 'owner')
        await message.answer(text = Action_for_owner, parse_mode='HTML', reply_markup=get_kb(1, 1))
    else:
        add_info(user.name, user.surname, user.company, message.text, 'user')
        await message.answer(text = Action_for_user, parse_mode='HTML', reply_markup=get_kb(1, 0))

    await state.finish()



@dp.message_handler(commands=['Check_Calendar'])
async def check_calendar(message: types.Message):
    await message.answer(f'Оставшееся количество стирок: {give_user_number_orders(message.from_user.id)}\n')  

@dp.message_handler(commands=['Check_Accesses'])
async def check_access(message: types.Message):
    # if give_user_number_orders(message.from_user.id) <= 0:
    #     await message.answer('У вас закончились свободные стирки')
    #     await UserStates.INACTIVE.set()
    # else:
    #     await bot.send_message(chat_id = message.from_user.id, text='Выберите свободный промежуток для записи', reply_markup=get_ikb())
    pass


@dp.message_handler(commands=['Ask_for_Access'])
async def ask_for_access(message: types.Message):
    global user
    global owner
    owner = get_owner()
    await message.answer(text=Text_for_Ask)
    await bot.send_message(chat_id = owner.id, text=f'Вам пришёл запрос на доступ к вашему графику от {user.name} {user.surname} из {user.company}, {user.id}', reply_markup=get_owner_choice_kb())


@dp.callback_query_handler(text='no_access')
async def nine_to_ten_handler(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)
    global owner


    await callback.answer()

@dp.callback_query_handler(text='encrypted')
async def nine_to_ten_handler(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)
    global owner


    await callback.answer()

@dp.callback_query_handler(text='5')
async def four_to_fif_handler(callback: types.CallbackQuery):
    await bot.edit_message_reply_markup(chat_id = callback.message.chat.id, message_id = callback.message.message_id, reply_markup = None)
    await callback.message.answer(text=f'Вы зарегистрировались на промежуток {times[5]}')

    global user
    user.orders = give_user_number_orders(callback.from_user.id)
    user.orders -= 1
    change_number_orders(callback.from_user.id, user.orders)
    
    washer_id = change_free_time_by_first(times[5], False)
    await callback.message.answer(text = f'Номер вашей машинки - {washer_id}')

    await callback.answer()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)