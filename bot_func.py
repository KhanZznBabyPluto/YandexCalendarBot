import re
import logging
from bot_db import *
from bot_yapi import *

logging.getLogger().handlers = []

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('bot.log', encoding='utf-8')

file_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(file_handler)

'''
def update_if_changed(customer_id) - апдейтит записи в events если 
  есть изменения. Если update был, то возращает True, иначе - False

'''

# ldrslvhwyabcvjio


def validate_email(email: str):
  pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
  
  if re.match(pattern, email):
      return True
  else:
      return False


def is_valid_password(email: str, username: str, password: str):
  try:
    parse_email = email.replace('@','%40')
    url = f'https://caldav.yandex.ru/calendars/{parse_email}/'
    caldav.DAVClient(url, username=username, password=password)
    return True
  except caldav.lib.error.AuthorizationError as e:
    logging.error(f'Неправильный пароль приложения у пользователя {username}')
    return False


def drop_array_el(array, id_name: str, id):
    return [el for el in array if el[id_name] != id]


async def update_if_changed(customer_id: int, email: str, username: str, password: str):
    await delete_timeout_events()

    ya_events = await get_event_yandex_info(email, username, password)

    if ya_events is None:
        return None

    db_events = await get_events(customer_id)

    res = False

    for db_event in db_events:
        is_in = False
        del_event_id = db_event['event_id']
        for ya_event in ya_events:
            if ya_event['uid'] == del_event_id:
                is_in = True
                if ya_event['last_modified'] != db_event['last_modified']:
                    await update_event(
                        ya_event['uid'],
                        ya_event['event'],
                        ya_event['start'],
                        ya_event['end'],
                        ya_event['last_modified']
                    )
                    res = True
                db_events = [el for el in db_events if el['event_id'] != del_event_id]
                ya_events = [el for el in ya_events if el['uid'] != del_event_id]
                break
        if not is_in:
            await delete_event(del_event_id)
            db_events = [el for el in db_events if el['event_id'] != del_event_id]
            res = True
    
    for ya_event in ya_events:
        is_in = False
        for db_event in db_events:
            if ya_event['uid'] == db_event['event_id']:
                is_in = True
                if ya_event['last_modified'] != db_event['last_modified']:
                    await update_event(
                        ya_event['uid'],
                        ya_event['event'],
                        ya_event['start'],
                        ya_event['end'],
                        ya_event['last_modified']
                    )
                    res = True
                break
        if not is_in:
            await add_info('event', EVENT_COLS, [
                ya_event['uid'],
                customer_id,
                ya_event['event'],
                ya_event['start'],
                ya_event['end'],
                ya_event['last_modified']
            ])
            res = True
    return res