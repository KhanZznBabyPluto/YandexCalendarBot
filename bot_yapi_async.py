import aiohttp
import caldav
import ics
import datetime

async def get_event_yandex_info(email: str, username: str, password: str):
    res = []

    try:
        parse_email = email.replace('@','%40')
        url = f'https://caldav.yandex.ru/calendars/{parse_email}/'
        async with aiohttp.ClientSession(auth=aiohttp.BasicAuth(username, password)) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    calendars = caldav.DAVClient(url, username=username, password=password).principal().calendars()
                    today = datetime.datetime.now()
                    start_date = today
                    end_date = datetime.datetime.combine(today.date(), datetime.time(23, 59))
                    event_urls = []

                    for calendar in calendars:
                        events = calendar.date_search(start=start_date, end=end_date)
                        for event in events:
                            event_urls.append(str(event)[7:])

                    for event_url in event_urls:
                        async with session.get(event_url) as event_resp:
                            if event_resp.status == 200:
                                ics_content = await event_resp.text()
                                calendar = ics.Calendar(ics_content)

                                for event in calendar.events:
                                    tmp = {}
                                    tmp['uid'] = event.uid
                                    tmp['event'] = event.name
                                    tmp['start'] = event.begin.datetime
                                    tmp['end'] = event.end.datetime
                                    tmp['last_modified'] = event.last_modified.datetime
                                    res.append(tmp)
                            else:
                                print(f'Проблемы с доступом к календарю по url: {event_url}\nПользователь: {username}.\nКод ошибки:', event_resp.status)
                else:
                    print(f'Проблемы с доступом к календарям по url: {url}\nПользователь: {username}.\nКод ошибки:', resp.status)
        return res
    except caldav.lib.error.AuthorizationError as e:
        print(f'Неправильный пароль приложения у пользователя {username}')
        return None
