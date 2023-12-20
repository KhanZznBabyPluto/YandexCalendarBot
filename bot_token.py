TOKEN_API = '6982560139:AAH57duxVrpv-synRhyxxvVvZhoNcPTuXGM'
client_id = '68864fc64a7842c1948567f02d1bdf4c'
client_secret = '9f10504cfd3d41e5a5650b277ddae6d7'
redirect_uri = 'https://oauth.yandex.ru/verification_code'
CUSTOMER_COLS = ['telegram_id', 'oauth_token', 'email', 'name', 'surname', 'login']
ACCESS_COLS = ['customer_id', 'allowed_customer_id', 'type', 'end_time']
EVENT_COLS = ['event_id', 'customer_id', 'event_name', 'event_start', 'event_end', 'last_modified']
TOKEN_API_TEST = '6830189372:AAHGHyzjbT2O35X5_SVl0BVlMRzpu9sgt8w'



# Параметры подключения к базе данных
_dbname = 'calendar-bot-new'
_user = 'test'
_password = 'test'
_host = '213.139.209.8'
_port = '5432'

#example:
# email = 'imsobaka01@yandex.kz'
# username = 'imsobaka01'
# password = 'qwskexkijcawqtie' # - он заправшивается у пользователя. Сделать его нужно в настройках яндекс аккаунта -> сделать пароль приложения и отправить в чат
# print(get_event_info(email, username, password))