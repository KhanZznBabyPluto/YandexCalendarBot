# YandexCalendarBot

Есть 2 типа пользователя:

Director - на данный момент один человек, который ввёл правильное ключевое слово
User - любой пользователь

Возможности для пользователей:
  Director:
    /Check_Calendar - получить свой календарь на сегодня
    /Check_Accesses - получить список всех людей, кому мы дали доступ и какой
    При запросе от пользователя получить свой календарь, есть 3 варианта:
    1. Не предоставлять доступ
    2. Предоставить неполный доступ, где будут видны только занят или свободен временной слот
    3. Полный доступ, где будет видно чем заняты временные слоты
  User:
    /Check_Calendar - получить свой календарь на сегодня
    /Ask_for_Access - запрость у Director доступ к календарю. Ничего передавать не надо, т.к. Director всего один и он уже известен. После вызова надо будет ждать ответа.
    При 2 или 3 видах доступа, будут также приходить апдейты при изменении календаря.


Необходимые функции для БД:
def add_info(name, surname, company, telegram_id, class_name):
  users.update_one({ "$set": { "name": name, "surname": surname, "company": company, "id": telegram_id, "class": class_name} })

Пример вызова:
add_info(owner.name, owner.surname, owner.company, owner.id, 'owner'), где owner - объект внутри бота


def get_user(telegram_id) - получить всю информацию о пользователе.
Пример вызова: 
  name, surname, company, class_name = get_user(telegram_id)

Class_id - это или User или Director


у User и Owner классов одинаковые поля:
name, surname, company, id
