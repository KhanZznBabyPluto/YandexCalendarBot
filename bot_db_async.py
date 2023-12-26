import asyncpg
import datetime
import logging
import pytz
from tzlocal import get_localzone

logging.getLogger().handlers = []

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('bot.log', encoding='utf-8')

file_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(file_handler)

CUSTOMER_COLS = ['telegram_id', 'oauth_token', 'email', 'name', 'surname', 'login']
ACCESS_COLS = ['customer_id', 'allowed_customer_id', 'type', 'end_time']
EVENT_COLS = ['event_id', 'customer_id', 'event_name', 'event_start', 'event_end', 'last_modified']

# Параметры подключения к базе данных
_dbname = 'calendar-bot-new'
_user = 'test'
_password = 'test'
_host = '213.139.209.8'
_port = '5432'

async def connect_to_db():
  return await asyncpg.connect(
    database=_dbname,
    user=_user,
    password=_password,
    host=_host,
    port=_port
  )


#! For all

async def print_table(table_name: str):
  conn = await connect_to_db()

  try:
    query = f"SELECT * FROM {table_name}"
    rows = await conn.fetch(query)

    for row in rows:
      print(row)

  except asyncpg.exceptions.PostgresError as e:
    logging.error("Ошибка PostgreSQL: %s", e)
    return None

  except Exception as e:
    logging.error('Ошибка: %s', e)
    return None

  finally:
    await conn.close()


async def add_info(table_name: str, columns: list, values: list):
  conn = await connect_to_db()

  try:
    query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['$' + str(i+1) for i in range(len(values))])})"
    await conn.execute(query, *values)
    logging.info("Данные успешно добавлены в таблицу %s", table_name)

  except asyncpg.exceptions.PostgresError as e:
    logging.error("Ошибка PostgreSQL: %s", e)

  except Exception as e:
    logging.error('Ошибка: %s', e)

  finally:
    await conn.close()


#! for customer

async def get_customers():
    conn = await connect_to_db()

    try:
      query = 'SELECT * FROM customer'
      rows = await conn.fetch(query)

      if len(rows) > 0:
          res = [dict(zip(["customer_id"] + CUSTOMER_COLS + ["password"], row)) for row in rows]
          return res
      else:
          return []
      
    except asyncpg.exceptions.PostgresError as e:
      logging.error("Ошибка PostgreSQL: %s", e)
      return None

    except Exception as e:
      logging.error("Ошибка: %s", e)
      return None

    finally:
      await conn.close()


async def get_user_by_telegram(telegram_id: int):
  conn = await connect_to_db()

  try:
    query = 'SELECT * FROM customer WHERE telegram_id = $1'
    row = await conn.fetchrow(query, telegram_id)

    if row:
      res = dict(zip(['customer_id'] + CUSTOMER_COLS + ['password'], row))
      return res
    else:
      return None

  except asyncpg.exceptions.PostgresError as e:
    logging.error("Ошибка PostgreSQL: %s", e)
    return None

  except Exception as e:
    logging.error("Ошибка: %s", e)
    return None

  finally:
    await conn.close()


async def get_user_by_id(customer_id: int):
  try:
    conn = await connect_to_db()

    query = 'SELECT * FROM customer WHERE customer_id = $1'
    row = await conn.fetchrow(query, customer_id)

    if row:
      res = dict(zip(['customer_id'] + CUSTOMER_COLS + ['password'], row))
      return res
    else:
      return None

  except asyncpg.exceptions.PostgresError as e:
    logging.error("Ошибка PostgreSQL: %s", e)
    return None

  except Exception as ex:
    logging.error("Ошибка: %s", ex)
    return None

  finally:
    await conn.close()


async def check_telegram_id(telegram_id: int):
  try:
    conn = await connect_to_db()

    query = "SELECT * FROM customer WHERE telegram_id = $1"
    result = await conn.fetch(query, telegram_id)

    return len(result) > 0

  except asyncpg.exceptions.PostgresError as e:
    logging.error("Ошибка PostgreSQL: %s", e)
    return None

  except Exception as ex:
    logging.error("Ошибка: %s", ex)
    return None

  finally:
    await conn.close()


async def add_password(customer_id: int, password: str):
  try:
    conn = await connect_to_db()

    query = "UPDATE customer SET password = $1 WHERE customer_id = $2"
    await conn.execute(query, password, customer_id)
    return True

  except asyncpg.exceptions.PostgresError as e:
    logging.error("Ошибка PostgreSQL: %s", e)
    return False

  except Exception as ex:
    logging.error("Ошибка: %s", ex)
    return False

  finally:
    await conn.close()


async def get_customer_by_email(email: str):
  try:
    conn = await connect_to_db()

    query = 'SELECT * FROM customer WHERE email = $1'
    row = await conn.fetchrow(query, email)

    await conn.close()

    if row:
      res = dict(zip(['customer_id'] + CUSTOMER_COLS + ['password'], row))
      return res
    else:
      return None

  except asyncpg.exceptions.PostgresError as e:
    logging.error("Ошибка PostgreSQL: %s", e)
    return None

  except Exception as ex:
    logging.error("Ошибка: %s", ex)
    return None
  
  finally:
    await conn.close()



#! for event
async def get_events(customer_id: int):
  try:
    conn = await connect_to_db()

    query = 'SELECT * FROM event WHERE customer_id = $1 AND event_end > $2 ORDER BY event_start ASC'

    rows = await conn.fetch(query, customer_id, datetime.datetime.now(datetime.timezone.utc))

    if len(rows) > 0:
      moscow_timezone = pytz.timezone('Europe/Moscow')
      res = [dict(row) for row in rows]
      for el in res:
        el['event_start'] = el['event_start'].replace(tzinfo=pytz.utc).astimezone(moscow_timezone)
        el['event_end'] = el['event_end'].replace(tzinfo=pytz.utc).astimezone(moscow_timezone)
        el['last_modified'] = el['last_modified'].replace(tzinfo=pytz.utc).astimezone(moscow_timezone)
      return res
    else:
      return []
    
  except asyncpg.exceptions.PostgresError as e:
    logging.error("Ошибка PostgreSQL: %s", e)
    return None
  
  except Exception as ex:
    logging.error("Ошибка: %s", ex)
    return None
  
  finally:
    await conn.close()


async def update_event(event_id: str, event_name: str, event_start, event_end, event_last_modified):
  try:
    conn = await connect_to_db()

    query = "UPDATE event SET event_name = $1, event_start = $2, event_end = $3, last_modified = $4 WHERE event_id = $5"

    await conn.execute(query, event_name, event_start, event_end, event_last_modified, event_id)

  except asyncpg.exceptions.PostgresError as e:
    logging.error("Ошибка PostgreSQL: %s", e)
    return None
  
  except Exception as ex:
    logging.error("Ошибка: %s", ex)
    return None
  
  finally:
    await conn.close()


async def delete_timeout_events():
  try:
    conn = await connect_to_db()

    query = "DELETE FROM event WHERE event_end < $1"

    await conn.execute(query, datetime.datetime.now(datetime.timezone.utc))
  except asyncpg.exceptions.PostgresError as e:
    logging.error("Ошибка PostgreSQL: %s", e)
    return None
  except Exception as ex:
    logging.error("Ошибка: %s", ex)
    return None
  finally:
    await conn.close()


async def delete_event(event_id: str):
  try:
    conn = await connect_to_db()

    query = "DELETE FROM event WHERE event_id = $1"

    await conn.execute(query, event_id)

  except asyncpg.exceptions.PostgresError as e:
      logging.error("Ошибка PostgreSQL: %s", e)
      return None
  
  except Exception as ex:
      logging.error("Ошибка: %s", ex)
      return None
  
  finally:
      await conn.close()

  

#! for access

async def get_accesses(customer_id: int):
  try:
    conn = await connect_to_db()

    query = '''
      SELECT ac.allowed_customer_id, cu.name, cu.surname, cu.email, cu.telegram_id, ac.type, ac.end_time, ac.requested
      FROM "access" as ac 
      JOIN customer as cu ON ac.allowed_customer_id = cu.customer_id 
      WHERE ac.customer_id = $1
    '''

    rows = await conn.fetch(query, customer_id)

    if len(rows) > 0:
      columns = ['allowed_customer_id', 'name', 'surname', 'email', 'telegram_id', 'type', 'end_time', 'requested']
      return [dict(zip(columns, row)) for row in rows]
    else:
      return None
  
  except asyncpg.exceptions.PostgresError as e:
    logging.error("Ошибка PostgreSQL: %s", e)
    return None
  
  except Exception as ex:
    logging.error("Ошибка: %s", ex)
    return None
  
  finally:
    await conn.close()


async def get_accesses_allowed(allowed_customer_id: int):
  try:
    conn = await connect_to_db()

    query = '''
      SELECT cu.customer_id, cu.name, cu.surname, cu.email, cu.telegram_id, ac.type, ac.end_time, ac.requested
      FROM "access" as ac
      JOIN customer as cu ON ac.customer_id = cu.customer_id 
      WHERE ac.allowed_customer_id = $1
    '''

    rows = await conn.fetch(query, allowed_customer_id)

    if len(rows) > 0:
      columns = ['customer_id', 'name', 'surname', 'email', 'telegram_id', 'type', 'end_time', 'requested']
      return [dict(zip(columns, row)) for row in rows]
    else:
      return None
  
  except asyncpg.exceptions.PostgresError as e:
    logging.error("Ошибка PostgreSQL: %s", e)
    return None
  
  except Exception as ex:
    logging.error("Ошибка: %s", ex)
    return None
  
  finally:
    await conn.close()


async def update_requested(customer_id: int, allowed_customer_id: int):
  try:
    conn = await connect_to_db()

    query = "UPDATE access SET requested = true WHERE customer_id = $1 AND allowed_customer_id = $2"

    await conn.execute(query, customer_id, allowed_customer_id)
  
  except asyncpg.exceptions.PostgresError as e:
    logging.error("Ошибка PostgreSQL: %s", e)
    return None
  
  except Exception as ex:
    logging.error("Ошибка: %s", ex)
    return None
  
  finally:
    await conn.close()


async def check_access(customer_id: int, allowed_customer_id: int):
  accesses = await get_accesses(customer_id)

  if accesses is None:
    return None

  for access in accesses:
    if access['allowed_customer_id'] == allowed_customer_id:
      return access

  return None


async def update_access_end_time(customer_id: int, allowed_customer_id: int, type_access: str, end_time):
  try:
    conn = await connect_to_db()

    query = "UPDATE access SET type = $1, end_time = $2 WHERE customer_id = $3 AND allowed_customer_id = $4"

    await conn.execute(query, type_access, end_time, customer_id, allowed_customer_id)
  
  except asyncpg.exceptions.PostgresError as e:
    logging.error("Ошибка PostgreSQL: %s", e)
    return None
  
  except Exception as ex:
    logging.error("Ошибка: %s", ex)
    return None
  
  finally:
    await conn.close()

  
#! for schedule

async def refresh_requests():
  try:
    conn = await connect_to_db()

    query = "UPDATE access SET requested = false"

    await conn.execute(query)

  except asyncpg.exceptions.PostgresError as e:
    logging.error("Ошибка PostgreSQL: %s", e)
    return None
  
  except Exception as ex:
    logging.error("Ошибка: %s", ex)
    return None
  
  finally:
    await conn.close()