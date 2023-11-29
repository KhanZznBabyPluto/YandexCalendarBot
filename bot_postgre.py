import re
import ics
import caldav
import requests
import datetime
import psycopg2
from bot_token import *
from icalendar import Calendar
from caldav.elements import dav
from bot_token import _dbname, _user, _password, _host, _port

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
      return dict(zip(['customer_id'] + CUSTOMER_COLS + ['password'], rows[0]))
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

    cur.execute(query, (telegram_id, ))

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
    query = '''
      SELECT ac.allowed_customer_id, cu.name, cu.surname, cu.email, cu.telegram_id, ac.type, ac.end_time
      FROM "access" as ac 
      JOIN customer as cu ON ac.allowed_customer_id = cu.customer_id 
      WHERE ac.customer_id = %s
    '''

    cur.execute(query, (customer_id,))

    rows = cur.fetchall()

    if len(rows) > 0:
      columns = ['allowed_customer_id', 'name', 'surname', 'email', 'telegram_id', 'type', 'end_time']
      return [dict(zip(columns, row)) for row in rows]
    else:
      return None
  except psycopg2.Error as e:
    print("Ошибка PostgreSQL:", e)
    return None
  except Exception as ex:
    print("Ошибка:", ex)
    return None

  

def print_customer():
  conn = psycopg2.connect(
    dbname=_dbname,
    user=_user,
    password=_password,
    host=_host,
    port=_port
  )

  cur = conn.cursor()

  try:
    query = "SELECT * FROM customer"

    cur.execute(query)

    rows = cur.fetchall()

    for row in rows:
      print(row)

  except psycopg2.Error as e:
    print("Ошибка PostgreSQL:", e)
    return


def get_event_info(email: str, username: str, password: str):
  res = []

  try:
    parse_email = email.replace('@','%40')
    url = f'https://caldav.yandex.ru/calendars/{parse_email}/'
    client = caldav.DAVClient(url, username=username, password=password)

    principal = client.principal()
    calendars = principal.calendars()

    today = datetime.datetime.now()
    start_date = today
    end_date = datetime.datetime.combine(today.date(), datetime.time(23, 59))

    event_urls = []
    for calendar in calendars:
      events = calendar.date_search(start=start_date, end=end_date)
      for event in events:
        event_urls.append(str(event)[7:])

    for event_url in event_urls:
      response = requests.get(event_url, auth=(username, password))

      if response.status_code == 200:
        ics_content = response.text
        calendar = ics.Calendar(ics_content)

        for event in calendar.events:
          tmp = {}
          tmp['event'] = event.name
          tmp['start'] = event.begin
          tmp['end'] = event.end
          res.append(tmp)

      else:
        print(f'Проблемы с доступом к календарю по url: {event_url}\nПользователь: {username}.\nКод ошибки:', response.status_code)
    return res
  except caldav.lib.error.AuthorizationError as e:
    print(f'Неправильный пароль приложения у пользователя {username}')
    return None


  
def get_cust_by_tel(telegram_id: str):
  dict = get_user_by_telegram(telegram_id)
  if dict is not None:
    return dict['customer_id']
  else:
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
  
def check_access(customer_id: int, allowed_customer_id: int):
  accesses = get_accesses(customer_id)

  if accesses is None:
    return None
  
  for access in accesses:
    if access['allowed_customer_id'] == allowed_customer_id:
      return access
  
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


def validate_email(email):
  email_pattern = r'^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
  if re.search(email_pattern, email):
    return True
  else:
    return False

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

# update_access_end_time(27, 26, 'enc', datetime.datetime.now())
