from motor.motor_asyncio import AsyncIOMotorClient


class TickerDatabase:
    def __init__(self, uri, database_name):
        self._client = AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.matches = self.db["matches"]

    async def add_match(self, data):
        """
            {
            "match_id": match_id,
            "user_ids": [],
            "home_team": home_team,
            "away_team": away_team,
            "home_score": home_score,
            "away_score": away_score,
            "time_status": time_status,
            "home_corner_kick": home_corner_kick,
            "away_corner_kick": away_corner_kick,
            "home_red_card": home_red_card,
            "home_yellow_card": home_yellow_card,
            "away_red_card": away_red_card,
            "away_yellow_card": away_yellow_card,
        }"""
        await self.matches.insert_one(data)

    async def get_match(self, match_id):
        return await self.matches.find_one({"match_id": match_id})

    async def get_all_matches(self):
        return self.matches.find()

    async def delete_match(self, match_id):
        await self.matches.delete_one({"match_id": match_id})

    async def update_match(self, match_id, data, tag="set"):
        await self.matches.update_one({"match_id": match_id}, {f"${tag}": data})
