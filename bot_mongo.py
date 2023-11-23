import psycopg2
from bot_classes import *

CUSTOMER_COLS = ['telegram_id', 'oauth_token', 'email', 'name', 'surname', 'role']
ACCESS_COLS = ['customer_id', 'allowed_customer_id', 'type', 'end_time']

# Параметры подключения к базе данных
_dbname = 'calendar-bot'
_user = 'test'
_password = 'test'
_host = '213.139.209.8'
_port = '5432'

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
      res = dict(zip(['customer_id'] + CUSTOMER_COLS, rows[0]))
      return res
    else:
      return None

  except psycopg2.Error as e:
    print("Ошибка PostgreSQL:", e)
    return None
  except Exception as ex:
    print("Ошибка:", ex)
    return None


def add_info(table_name: str, columns: list[str], values: list[str]):
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


def get_director():
  conn = psycopg2.connect(
    dbname=_dbname,
    user=_user,
    password=_password,
    host=_host,
    port=_port
  )

  cur = conn.cursor()
  try:
    query = "SELECT * FROM customer WHERE role = 'director'"

    cur.execute(query)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    if len(rows) > 0:
      return dict(zip(['customer_id'] + CUSTOMER_COLS, rows[0]))
    else:
      return None

  except psycopg2.Error as e:
    print("Ошибка PostgreSQL:", e)
    return None
  except Exception as ex:
    print("Ошибка:", ex)
    return
  

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

    cur.execute(query, telegram_id)

    rows = cur.fetchall()

    return len(rows) > 0
  except psycopg2.Error as e:
    print("Ошибка PostgreSQL:", e)
    return None
  except Exception as ex:
    print("Ошибка:", ex)
    return None
  

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
    query = "SELECT * FROM access WHERE customer_id = %s"

    cur.execute(query, customer_id)

    rows = cur.fetchall()

    if len(rows) > 0:
      return [dict(zip(['access_id'] + ACCESS_COLS, rows[i])) for i in range(len(rows))]
    else:
      return None
  except psycopg2.Error as e:
    print("Ошибка PostgreSQL:", e)
    return None
  except Exception as ex:
    print("Ошибка:", ex)
    return None


def director_create():
  Owner = Owner()
  dict = get_director()
  if dict is not None:
    Owner.load_info(dict['name'], dict['surname'], dict['oauth_token'], dict['email'], dict['telegram_id'])
    return Owner
  else:
    return None