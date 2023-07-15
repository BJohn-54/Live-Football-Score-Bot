from bot import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils import get_matches
import asyncio

if __name__ == "__main__":
    app = Bot()
    scheduler = AsyncIOScheduler()
    # asyncio.run(get_matches())
    scheduler.add_job(get_matches, "interval", minutes=1)
    scheduler.start()
    app.run()
