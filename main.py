from bot import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils import get_matches

from utils.helpers import check_match_status

if __name__ == "__main__":
    app = Bot()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(get_matches, "interval", minutes=1)
    scheduler.add_job(check_match_status, "interval", minutes=1, args=[app])
    scheduler.start()
    app.run()
