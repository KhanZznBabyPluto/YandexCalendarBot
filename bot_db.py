import psycopg2
import datetime
from tzlocal import get_localzone

CUSTOMER_COLS = ['telegram_id', 'oauth_token', 'email', 'name', 'surname', 'login']
ACCESS_COLS = ['customer_id', 'allowed_customer_id', 'type', 'end_time']
EVENT_COLS = ['event_id', 'customer_id', 'event_name', 'event_start', 'event_end', 'last_modified']

# Параметры подключения к базе данных
_dbname = 'calendar-bot-new'
_user = 'test'
_password = 'test'
_host = '213.139.209.8'
_port = '5432'


#! for all
def print_table(table_name: str):
  conn = psycopg2.connect(
    dbname=_dbname,
    user=_user,
    password=_password,
    host=_host,
    port=_port
  )

  cur = conn.cursor()

  try:
    query = f"SELECT * FROM {table_name}"

    cur.execute(query)

    rows = cur.fetchall()

    for row in rows:
      print(row)
      
  except psycopg2.Error as e:
    print("Ошибка PostgreSQL:", e)
    return None
  except Exception as ex:
    print("Ошибка:", ex)
    return None
  

def add_info(table_name: str, columns: list, values: list):
  conn = psycopg2.connect(
    dbname=_dbname,
    user=_user,
    password=_password,
    host=_host,
    port=_port
  )

  cur = conn.cursor()

  try:
    query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(values))})"
    print(query)
    
    cur.execute(query, values)
    
    conn.commit()
    
    print("Данные успешно добавлены в таблицу", table_name)
    
  except psycopg2.Error as e:
    conn.rollback()
    print("Ошибка при добавлении данных:", e)
    
  finally:
    cur.close()
    conn.close()


#! for customer
def get_customers():
  conn = psycopg2.connect(
    dbname=_dbname,
    user=_user,
    password=_password,
    host=_host,
    port=_port
  )

  cur = conn.cursor()
  try:
    query = 'SELECT * FROM customer'

    cur.execute(query)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    if len(rows) > 0:
      res = [dict(zip(["customer_id"] + CUSTOMER_COLS + ["password"], row)) for row in rows]
      return res
    else:
      return []

  except psycopg2.Error as e:
    print("Ошибка PostgreSQL:", e)
    return None
  except Exception as ex:
    print("Ошибка:", ex)
    return None


def get_user_by_telegram(telegram_id: int):
  conn = psycopg2.connect(
    dbname=_dbname,
    user=_user,
    password=_password,
    host=_host,
    port=_port
  )

  cur = conn.cursor()
  try:
    query = 'SELECT * FROM customer WHERE telegram_id = %s'

    cur.execute(query, (telegram_id, ))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    if len(rows) > 0:
      res = dict(zip(['customer_id'] + CUSTOMER_COLS + ['password'], rows[0]))
      return res
    else:
      return None

  except psycopg2.Error as e:
    print("Ошибка PostgreSQL:", e)
    return None
  except Exception as ex:
    print("Ошибка:", ex)
    return None
  

def get_user_by_id(customer_id: int):
  conn = psycopg2.connect(
    dbname=_dbname,
    user=_user,
    password=_password,
    host=_host,
    port=_port
  )

  cur = conn.cursor()
  try:
    query = 'SELECT * FROM customer WHERE customer_id = %s'

    cur.execute(query, (customer_id, ))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    if len(rows) > 0:
      res = dict(zip(['customer_id'] + CUSTOMER_COLS + ['password'], rows[0]))
      return res
    else:
      return None

  except psycopg2.Error as e:
    print("Ошибка PostgreSQL:", e)
    return None
  except Exception as ex:
    print("Ошибка:", ex)
    return None


def check_telegram_id(telegram_id: int):
  conn = psycopg2.connect(
    dbname=_dbname,
    user=_user,
    password=_password,
    host=_host,
    port=_port
  )

  cur = conn.cursor()

  try:
    query = "SELECT * FROM customer WHERE telegram_id = %s"

    cur.execute(query, (telegram_id, ))

    rows = cur.fetchall()

    return len(rows) > 0
  except psycopg2.Error as e:
    print("Ошибка PostgreSQL:", e)
    return None
  except Exception as ex:
    print("Ошибка:", ex)
    return None
  

def add_password(customer_id: int, password: str):
  conn = psycopg2.connect(
    dbname=_dbname,
    user=_user,
    password=_password,
    host=_host,
    port=_port
  )

  cur = conn.cursor()

  try:
    query = "UPDATE customer SET password = %s WHERE customer_id = %s"

    cur.execute(query, (password, customer_id))

    conn.commit()
      
  except psycopg2.Error as e:
    print("Ошибка PostgreSQL:", e)
    return None
  except Exception as ex:
    print("Ошибка:", ex)
    return None
  

def get_customer_by_email(email: str):
  conn = psycopg2.connect(
    dbname=_dbname,
    user=_user,
    password=_password,
    host=_host,
    port=_port
  )

  cur = conn.cursor()
  try:
    query = 'SELECT * FROM customer WHERE email = %s'

    cur.execute(query, (email, ))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    if len(rows) > 0:
      res = dict(zip(['customer_id'] + CUSTOMER_COLS + ['password'], rows[0]))
      return res
    else:
      return None

  except psycopg2.Error as e:
    print("Ошибка PostgreSQL:", e)
    return None
  except Exception as ex:
    print("Ошибка:", ex)
    return None
  

#! for event
def get_events(customer_id: int):
  conn = psycopg2.connect(
    dbname=_dbname,
    user=_user,
    password=_password,
    host=_host,
    port=_port
  )

  cur = conn.cursor()
  try:
    query = 'SELECT * FROM event WHERE customer_id = %s AND event_end > %s ORDER BY event_start ASC'

    cur.execute(query, (customer_id, datetime.datetime.now(datetime.timezone.utc)))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    if len(rows) > 0:
      local_timezone = get_localzone()
      res = [dict(zip(EVENT_COLS, row)) for row in rows]
      for el in res:
        el['event_start'] = el['event_start'].astimezone(local_timezone)
        el['event_end'] = el['event_end'].astimezone(local_timezone)
        el['last_modified'] = el['last_modified'].astimezone(local_timezone)
      return res
    else:
      return []

  except psycopg2.Error as e:
    print("Ошибка PostgreSQL:", e)
    return None
  except Exception as ex:
    print("Ошибка:", ex)
    return None
  

def update_event(event_id: str, event_name: str, event_start, event_end, event_last_modified):
  conn = psycopg2.connect(
    dbname=_dbname,
    user=_user,
    password=_password,
    host=_host,
    port=_port
  )

  cur = conn.cursor()

  try:
    query = "UPDATE event SET event_name = %s, event_start = %s, event_end = %s, last_modified = %s WHERE event_id = %s"

    cur.execute(query, (event_name, event_start, event_end, event_last_modified, event_id))

    conn.commit()
      
  except psycopg2.Error as e:
    print("Ошибка PostgreSQL:", e)
    return None
  except Exception as ex:
    print("Ошибка:", ex)
    return None


def delete_timeout_events():
  conn = psycopg2.connect(
    dbname=_dbname,
    user=_user,
    password=_password,
    host=_host,
    port=_port
  )

  cur = conn.cursor()

  try:
    query = "DELETE FROM event WHERE event_end < %s"

    cur.execute(query, (datetime.datetime.now(datetime.timezone.utc), ))

    conn.commit()
      
  except psycopg2.Error as e:
    print("Ошибка PostgreSQL:", e)
    return None
  except Exception as ex:
    print("Ошибка:", ex)
    return None
  

def delete_event(event_id: str):
  conn = psycopg2.connect(
    dbname=_dbname,
    user=_user,
    password=_password,
    host=_host,
    port=_port
  )

  cur = conn.cursor()

  try:
    query = "DELETE FROM event WHERE event_id = %s"

    cur.execute(query, (event_id, ))

    conn.commit()
      
  except psycopg2.Error as e:
    print("Ошибка PostgreSQL:", e)
    return None
  except Exception as ex:
    print("Ошибка:", ex)
    return None

  
#! for access

def get_accesses(customer_id: int):
  conn = psycopg2.connect(
    dbname=_dbname,
    user=_user,
    password=_password,
    host=_host,
    port=_port
  )

  cur = conn.cursor()

  try:
    query = '''
      SELECT ac.allowed_customer_id, cu.name, cu.surname, cu.email, cu.telegram_id, ac.type, ac.end_time, ac.requested
      FROM "access" as ac 
      JOIN customer as cu ON ac.allowed_customer_id = cu.customer_id 
      WHERE ac.customer_id = %s
    '''

    cur.execute(query, (customer_id,))

    rows = cur.fetchall()

    if len(rows) > 0:
      columns = ['allowed_customer_id', 'name', 'surname', 'email', 'telegram_id', 'type', 'end_time', 'requested']
      return [dict(zip(columns, row)) for row in rows]
    else:
      return None
  except psycopg2.Error as e:
    print("Ошибка PostgreSQL:", e)
    return None
  except Exception as ex:
    print("Ошибка:", ex)
    return None


def update_requested(customer_id: int, allowed_customer_id: int):
  conn = psycopg2.connect(
    dbname=_dbname,
    user=_user,
    password=_password,
    host=_host,
    port=_port
  )

  cur = conn.cursor()

  try:
    query = "UPDATE access SET requested = true WHERE customer_id = %s AND allowed_customer_id = %s"

    cur.execute(query, (customer_id, allowed_customer_id))

    conn.commit()
      
  except psycopg2.Error as e:
    print("Ошибка PostgreSQL:", e)
    return None
  except Exception as ex:
    print("Ошибка:", ex)
    return None


def check_access(customer_id: int, allowed_customer_id: int):
  accesses = get_accesses(customer_id)

  if accesses is None:
    return None
  
  for access in accesses:
    if access['allowed_customer_id'] == allowed_customer_id:
      return access
  
  return None
  

def update_access_end_time(customer_id: int, allowed_customer_id: str, type_access: str, end_time):
  conn = psycopg2.connect(
    dbname=_dbname,
    user=_user,
    password=_password,
    host=_host,
    port=_port
  )

  cur = conn.cursor()

  try:
    query = "UPDATE access SET type = %s, end_time = %s WHERE customer_id = %s AND allowed_customer_id = %s"

    cur.execute(query, (type_access, end_time, customer_id, allowed_customer_id))

    conn.commit()
      
  except psycopg2.Error as e:
    print("Ошибка PostgreSQL:", e)
    return None
  except Exception as ex:
    print("Ошибка:", ex)
    return None
  




# ! For schedule

async def refresh_requests():
  conn = psycopg2.connect(
    dbname=_dbname,
    user=_user,
    password=_password,
    host=_host,
    port=_port
  )

  cur = conn.cursor()

  try:
    query = "UPDATE access SET requested = false"

    cur.execute(query)

    conn.commit()
      
  except psycopg2.Error as e:
    print("Ошибка PostgreSQL:", e)
    return None
  except Exception as ex:
    print("Ошибка:", ex)
    return None
  
print_table('access')