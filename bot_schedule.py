import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot_db import refresh_requests

async def run_scheduler():
  scheduler = AsyncIOScheduler()
  scheduler.add_job(refresh_requests, 'cron', day_of_week='*', hour=0, minute=0, second=1)
  scheduler.start()

  while True:
    await asyncio.sleep(1)


if __name__ == '__main__':
  asyncio.run(run_scheduler())