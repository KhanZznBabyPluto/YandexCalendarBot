import datetime
import calendar
import time
import threading
import pymongo
import pandas as pd
from copy import deepcopy
from bot_classes import Owner


def connect_collection(str):
  db_client = pymongo.MongoClient("mongodb+srv://andrey:28122011@cluster0.i2aesum.mongodb.net/")
  current_db = db_client['TeleBot']

  return current_db[str]

book = connect_collection('book')
users = connect_collection('users')
visits = connect_collection('visits')


#* Book
def free_washers():
  res = []
  for obj in book.find():
    time = list(obj['time'].values())
    if True in time:
      res.append(obj)
  
  return res

def free_time(_washer_id):
  res = []

  washer = book.find_one({"_id": _washer_id})
  for time in washer["time"].keys():
    if washer["time"][time]:
      res.append(time)

  return res

def change_free_time(_washer_id, time, boolValue):
  washer = book.find_one({ "_id": _washer_id })

  new_time_obj = deepcopy(washer["time"])
  new_time_obj[time] = boolValue

  book.update_one({ "_id": _washer_id }, { "$set": { "time" : new_time_obj } })


def change_free_time_by_first(time, boolValue):
  washers = free_washers()
  washer_id = 0

  for washer in washers:
    if washer['time'][time] != boolValue:
      change_free_time(washer['_id'], time, boolValue)
      washer_id = washer['_id']
      break
  
  return washer_id


def reset_washers():
  obj = {
    "9.00-10.10": True,
    "10.10-11.20": True,
    "11.20-12.30": True,
    "12.30-14.00": True,
    "14.00-15.10": True,
    "15.10-16.20": True
  }
  while True:
    now = datetime.datetime.now()

    # Если текущее время 18:00, меняем состояние всех машинок на True
    if now.hour == 18 and now.minute == 0:
      book.update_many({}, { "$set": { "time": obj } })

    # Ждем до следующего дня
    tomorrow = now + datetime.timedelta(days=1)
    reset_time = datetime.datetime(tomorrow.year, tomorrow.month, tomorrow.day, 18, 0, 0)
    time.sleep((reset_time - now).total_seconds())

def run_algorithm():
  obj = {
    "9.00-10.10": True,
    "10.10-11.20": True,
    "11.20-12.30": True,
    "12.30-14.00": True,
    "14.00-15.10": True,
    "15.10-16.20": True
  }
  book.update_many({}, { "$set": { "time": obj } })

def run_algorithm_daily():
  def thread_func():
    while True:
      now = datetime.datetime.now()

      if now.hour == 18 and now.minute == 0:
        t = threading.Thread(target=run_algorithm)
        t.start()

      # Wait for one hour before checking again
      time.sleep(3600)

  t = threading.Thread(target=thread_func)
  t.start()


#* Users
def check_key(keys, values):
  if (len(keys) != len(values)):
    return False
  filt = {}
  for i in range(len(keys)):
    filt[keys[i]] = values[i]

  obj = users.find_one(filt)
  if obj:
    return True
  return False 


def add_info(name, surname, company, telegram_id, class_name):
  users.update_one({ "$set": { "name": name, "surname": surname, "company": company, "id": telegram_id, "class": class_name} })

def give_user_number_orders(telegram_id):
  return users.find_one({ "id": telegram_id })['number_orders']

def change_number_orders(telegram_id, number):
  users.update_one({ "id": telegram_id }, { "$set": { "number_orders" : number } } )

def reset_orders():
  users.update_many({}, {"$set": { "number_orders": 4 } })

def reset_numbers_orders():
  def thread_func():
    while True:
      now = datetime.datetime.now()
      last_day = calendar.monthrange(now.year, now.month)[1]

      if now.day == last_day and now.hour == 18 and now.minute == 0:
        t = threading.Thread(target=reset_orders)
        t.start()

      # Wait for one hour before checking again
      time.sleep(3600)

  t = threading.Thread(target=thread_func)
  t.start()

#* Visits
def add_string(telegram_id, date, full_name, room, time):
  visits.insert_one({ "id": telegram_id, "date": date, "full_name": full_name, "room": room, "time": time })

def del_string(telegram_id, date, time):
  visits.delete_one({ "id": telegram_id, "date": date, "time": time })

def fill_doc(low_date = datetime.datetime.now() - datetime.timedelta(days=30), high_date = datetime.datetime.now()):
  # Get data from MongoDB
    data = list(visits.find({
      "date": {"$gte": low_date, "$lte": high_date}
    }))

    # Create a Pandas DataFrame from the data
    df = pd.DataFrame(data)


def get_user(telegram_id):
    # owner = Owner()
    # owner.load_info() 
    # return owner
    pass