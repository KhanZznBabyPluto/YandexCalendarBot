import re
from bot_db import *
from bot_yapi import *


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
    print(f'Неправильный пароль приложения у пользователя {username}')
    return False



async def update_if_changed(customer_id: int, email: str, username: str, password: str):
    await delete_timeout_events()

    ya_events = await get_event_yandex_info(email, username, password)

    if ya_events is None:
        return None

    db_events = await get_events(customer_id)

    if len(ya_events) < len(db_events):
        for db_event in db_events:
            is_in = False
            for ya_event in ya_events:
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
                    break
            if not is_in:
                await delete_event(db_event['event_id'])
        return True

    if len(ya_events) > len(db_events):
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
        return True

    flag = False

    for ya_event in ya_events:
        for db_event in db_events:
            if ya_event['uid'] == db_event['event_id']:
                if ya_event['last_modified'] != db_event['last_modified']:
                    await update_event(
                        ya_event['uid'],
                        ya_event['event'],
                        ya_event['start'],
                        ya_event['end'],
                        ya_event['last_modified']
                    )
                    flag = True
                break

    return flag