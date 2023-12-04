TOKEN_API = '6982560139:AAH57duxVrpv-synRhyxxvVvZhoNcPTuXGM'
client_id = '68864fc64a7842c1948567f02d1bdf4c'
client_secret = '9f10504cfd3d41e5a5650b277ddae6d7'
redirect_uri = 'https://oauth.yandex.ru/verification_code'
CUSTOMER_COLS = ['telegram_id', 'oauth_token', 'email', 'name', 'surname', 'role', 'login']
ACCESS_COLS = ['customer_id', 'allowed_customer_id', 'type', 'end_time']

_dbname = 'calendar-bot'
_user = 'test'
_password = 'test'
_host = '213.139.209.8'
_port = '5432'

#example:
# email = 'imsobaka01@yandex.kz'
# username = 'imsobaka01'
# password = 'qwskexkijcawqtie' # - он заправшивается у пользователя. Сделать его нужно в настройках яндекс аккаунта -> сделать пароль приложения и отправить в чат
# print(get_event_info(email, username, password))