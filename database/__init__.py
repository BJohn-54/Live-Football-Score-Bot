from .ticker import TickerDatabase
from bot.config import Config


class Database:
    def __init__(self, uri, database_name):
        self.ticker = TickerDatabase(uri, database_name)


db = Database(Config.DATABASE_URL, Config.DATABASE_NAME)
