import aiohttp
import caldav
import ics
import datetime
import logging
import pytz

logging.getLogger().handlers = []

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('bot.log', encoding='utf-8')

file_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(file_handler)


async def get_event_yandex_info(email: str, username: str, password: str):
    res = []

    try:
        parse_email = email.replace('@','%40')
        url = f'https://caldav.yandex.ru/calendars/{parse_email}/'
        async with aiohttp.ClientSession(auth=aiohttp.BasicAuth(username, password)) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    client = caldav.DAVClient(url, username=username, password=password)
                    principal = client.principal()
                    calendars = principal.calendars()
                    moscow_tz = pytz.timezone('Europe/Moscow')
                    today = datetime.datetime.now(moscow_tz)
                    start_date = datetime.datetime.combine(today.date(), datetime.time(00, 00))
                    end_date = datetime.datetime.combine(today.date(), datetime.time(23, 59))
                    event_urls = []

                    for calendar in calendars:
                        events = calendar.date_search(start=start_date, end=end_date)
                        for event in events:
                            event_urls.append(str(event.url))

                    for event_url in event_urls:
                        async with session.get(event_url) as event_resp:
                            if event_resp.status == 200:
                                ics_content = await event_resp.text()
                                calendar = ics.Calendar(ics_content)



                                for event in calendar.events:
                                    if (event.end.datetime < today):
                                        continue
                                    tmp = {}
                                    tmp['uid'] = event.uid
                                    tmp['event'] = event.name
                                    tmp['start'] = event.begin.datetime
                                    tmp['end'] = event.end.datetime
                                    tmp['last_modified'] = event.last_modified.datetime
                                    res.append(tmp)
                            else:
                                logging.error(f'Проблемы с доступом к календарю по url: {event_url}\nПользователь: {username}.\nКод ошибки:', event_resp.status)
                else:
                    logging.error(f'Проблемы с доступом к календарям по url: {url}\nПользователь: {username}.\nКод ошибки:', resp.status)
        return res
    except caldav.lib.error.AuthorizationError as e:
        logging.error(f'Неправильный пароль приложения у пользователя {username}')
        return None