import base64
from contextlib import suppress
import aiohttp
from bs4 import BeautifulSoup
from bot.config import Config
from pyrogram.types import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
import aiohttp
from database import db


async def prettify_table_to_markdown(html):
    data = []
    # sort by competition name
    html = sorted(html, key=lambda x: x["competition"]["name"])
    for h in html:
        competition = h["competition"]

        image = competition["thumbnail"]["alt_text"].replace("flag", "").strip()
        row_text = competition["name"]

        flag = FLAGS.get(image, "")
        row_text = f"{flag} {row_text.replace(' | ', ' ')} "
        if "International" in row_text:
            row_text = f"🗺️ {row_text}"
        if "UEFA" in row_text:
            row_text = f"⚽ {row_text}"
        data.append({"row_text": row_text, "href": ""})

        for match in h["matches"]:
            home_team = match["home_team"]["name"]
            away_team = match["away_team"]["name"]
            home_score = match["home_score"]
            away_score = match["away_score"]
            href = match["url"]
            row_text = f"{home_team} | {home_score} - {away_score} | {away_team}"
            data.append({"row_text": row_text, "href": href})

    return data or ""


async def set_commands(client):
    commands = [
        BotCommand(command="live", description="Get live matches"),
        BotCommand(command="search", description="Search for matches"),
    ]

    await client.set_bot_commands(commands)


async def get_source():
    i = 0
    sources = []
    endpoint = (
        "https://sportscore.io/api/v1/football/matches/?match_status=live&page={}"
    )
    api_key = "jbtmquwvjbtm3bwd32se8mry0fbqgk"
    headers = {"X-API-Key": api_key, "accept": "application/json"}
    while True:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{endpoint.format(i)}", headers=headers) as resp:
                if resp.status != 200:
                    print(f"Status code: {resp.status}")
                    print(resp.reason)
                    print(f"Broke at page {i}")
                    break
                data = await resp.json()
                if not data.get("match_groups", []):
                    break
                sources += data["match_groups"]
                i += 1

    return sources


async def get_matches():
    sources = await get_source()
    data = await prettify_table_to_markdown(sources)
    Config.MATCHES = data


async def get_match_summary(url):
    match_id = url.split("/")[-2]
    "/api/v1/football/match/{match_id}/"
    headers = {
        "X-API-Key": "jbtmquwvjbtm3bwd32se8mry0fbqgk",
        "accept": "application/json",
    }
    url = f"https://sportscore.io/api/v1/football/match/{match_id}/"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            print(await resp.text())
            data = await resp.json()
            home_team = data["home_team"]["name"]
            away_team = data["away_team"]["name"]
            home_score = data["home_score"]
            away_score = data["away_score"]
            time_status = data["state_display"]
            home_corner_kick = data["home_team_corners"]
            away_corner_kick = data["away_team_corners"]
            home_red_card = data["home_team_red_cards"]
            home_yellow_card = data["home_team_yellow_cards"]
            away_red_card = data["away_team_red_cards"]
            away_yellow_card = data["away_team_yellow_cards"]
            return {
                "match_id": match_id,
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
            }


def encode_base64(string):
    string_bytes = string.encode("utf-8")
    base64_bytes = base64.b64encode(string_bytes)
    return base64_bytes.decode("utf-8")


async def check_match_status(app):
    all_matches = await db.ticker.get_all_matches()
    # print(all_matches)
    for match in all_matches:
        match_summary = await get_match_summary(match["url"])

        data = next(
            (
                dat
                for dat in Config.MATCHES
                if dat["href"] and dat["href"].split("/")[-2] == match["match_id"]
            ),
            "",
        )

        if not data:
            await db.ticker.delete_match(match["match_id"])
            continue

        edata = encode_base64(data["row_text"])[::-1][:25]

        time_status = match_summary["time_status"].lower()
        text_to_sent = []
        markup = lambda user_id: InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "View Details",
                        callback_data=f"detail_view {match['match_id']} {edata} {user_id}",
                    )
                ]
            ]
        )

        if match["time_status"].lower() == "finished" and time_status != "finished":
            text = f"Match between {match_summary['home_team']} and {match_summary['away_team']} has finished!"
            text_to_sent.append(text)
        elif match["time_status"].lower() == "halftime" and time_status != "halftime":
            text = f"Match between {match_summary['home_team']} and {match_summary['away_team']} is in halftime!"
            text_to_sent.append(text)
        elif match["time_status"].lower() == "penalties" and time_status != "penalties":
            text = f"Match between {match_summary['home_team']} and {match_summary['away_team']} is in penalties!"
            text_to_sent.append(text)
        elif match["time_status"].lower() == "overtime" and time_status != "overtime":
            text = f"Match between {match_summary['home_team']} and {match_summary['away_team']} is in overtime!"
            text_to_sent.append(text)

        if match["home_score"] != match_summary["home_score"]:
            text = f"Goal ⚽ {match_summary['home_team']} scored against {match_summary['away_team']}!"
            text_to_sent.append(text)
        if match["away_score"] != match_summary["away_score"]:
            text = f"Goal ⚽ {match_summary['away_team']} scored against {match_summary['home_team']}!"
            text_to_sent.append(text)
        if match["home_corner_kick"] != match_summary["home_corner_kick"]:
            text = f"Corner Kick 🏁 {match_summary['home_team']} got a corner kick!"
            text_to_sent.append(text)
        if match["away_corner_kick"] != match_summary["away_corner_kick"]:
            text = f"Corner Kick 🏁 {match_summary['away_team']} got a corner kick!"
            text_to_sent.append(text)
        if match["home_red_card"] != match_summary["home_red_card"]:
            text = f"Red Card 🟥 {match_summary['home_team']} got a red card!"
            text_to_sent.append(text)
        if match["home_yellow_card"] != match_summary["home_yellow_card"]:
            text = f"Yellow Card 🟨 {match_summary['home_team']} got a yellow card!"
            text_to_sent.append(text)
        if match["away_red_card"] != match_summary["away_red_card"]:
            text = f"Red Card 🟥 {match_summary['away_team']} got a red card!"
            text_to_sent.append(text)
        if match["away_yellow_card"] != match_summary["away_yellow_card"]:
            text = f"Yellow Card 🟨 {match_summary['away_team']} got a yellow card!"
            text_to_sent.append(text)

        if text_to_sent:
            for user_id in match["users"]:
                for text in text_to_sent:
                    text = f'**{text}**\n\n{match_summary["home_team"]} {match_summary["home_score"]} - {match_summary["away_score"]} {match_summary["away_team"]}\nTime (minutes): {match_summary["time_status"]} 🕒'
                    with suppress(Exception):
                        await app.send_message(
                            user_id, text, reply_markup=markup(user_id)
                        )

        if match["time_status"].lower() == "finished":
            await db.ticker.delete_match(match["match_id"])
        else:
            await db.ticker.update_match(match["match_id"], match_summary)


FLAGS = {
    "Afghanistan": "🇦🇫",
    "Albania": "🇦🇱",
    "Algeria": "🇩🇿",
    "Andorra": "🇦🇩",
    "Angola": "🇦🇴",
    "Antigua & Barbuda": "🇦🇬",
    "Argentina": "🇦🇷",
    "Armenia": "🇦🇲",
    "Australia": "🇦🇺",
    "Austria": "🇦🇹",
    "Azerbaijan": "🇦🇿",
    "Bahamas": "🇧🇸",
    "Bahrain": "🇧🇭",
    "Bangladesh": "🇧🇩",
    "Barbados": "🇧🇧",
    "Belarus": "🇧🇾",
    "Belgium": "🇧🇪",
    "Belize": "🇧🇿",
    "Benin": "🇧🇯",
    "Bhutan": "🇧🇹",
    "Bolivia": "🇧🇴",
    "Bosnia & Herzegovina": "🇧🇦",
    "Botswana": "🇧🇼",
    "Brazil": "🇧🇷",
    "Brunei": "🇧🇳",
    "Bulgaria": "🇧🇬",
    "Burkina Faso": "🇧🇫",
    "Burundi": "🇧🇮",
    "Cambodia": "🇰🇭",
    "Cameroon": "🇨🇲",
    "Canada": "🇨🇦",
    "Cape Verde": "🇨🇻",
    "Central African Republic": "🇨🇫",
    "Chad": "🇹🇩",
    "Chile": "🇨🇱",
    "China": "🇨🇳",
    "Colombia": "🇨🇴",
    "Comoros": "🇰🇲",
    "Congo (Congo-Brazzaville)": "🇨🇬",
    "Costa Rica": "🇨🇷",
    "Croatia": "🇭🇷",
    "Cuba": "🇨🇺",
    "Cyprus": "🇨🇾",
    "Czech Republic": "🇨🇿",
    "Denmark": "🇩🇰",
    "Djibouti": "🇩🇯",
    "Dominica": "🇩🇲",
    "Dominican Republic": "🇩🇴",
    "East Timor": "🇹🇱",
    "Ecuador": "🇪🇨",
    "Egypt": "🇪🇬",
    "El Salvador": "🇸🇻",
    "Equatorial Guinea": "🇬🇶",
    "Eritrea": "🇪🇷",
    "Estonia": "🇪🇪",
    "Eswatini": "🇸🇿",
    "Ethiopia": "🇪🇹",
    "Fiji": "🇫🇯",
    "Finland": "🇫🇮",
    "France": "🇫🇷",
    "Gabon": "🇬🇦",
    "Gambia": "🇬🇲",
    "Georgia": "🇬🇪",
    "Germany": "🇩🇪",
    "Ghana": "🇬🇭",
    "Greece": "🇬🇷",
    "Grenada": "🇬🇩",
    "Guatemala": "🇬🇹",
    "Guinea": "🇬🇳",
    "Guinea-Bissau": "🇬🇼",
    "Guyana": "🇬🇾",
    "Haiti": "🇭🇹",
    "Honduras": "🇭🇳",
    "Hungary": "🇭🇺",
    "Iceland": "🇮🇸",
    "India": "🇮🇳",
    "Indonesia": "🇮🇩",
    "Iran": "🇮🇷",
    "Iraq": "🇮🇶",
    "Ireland": "🇮🇪",
    "Israel": "🇮🇱",
    "Italy": "🇮🇹",
    "Jamaica": "🇯🇲",
    "Japan": "🇯🇵",
    "Jordan": "🇯🇴",
    "Kazakhstan": "🇰🇿",
    "Kenya": "🇰🇪",
    "Kiribati": "🇰🇮",
    "South Korea": "🇰🇷",
    "Korea, North": "🇰🇵",
    "Korea, South": "🇰🇷",
    "Kosovo": "🇽🇰",
    "Kuwait": "🇰🇼",
    "Kyrgyzstan": "🇰🇬",
    "Laos": "🇱🇦",
    "Latvia": "🇱🇻",
    "Lebanon": "🇱🇧",
    "Lesotho": "🇱🇸",
    "Liberia": "🇱🇷",
    "Libya": "🇱🇾",
    "Liechtenstein": "🇱🇮",
    "Lithuania": "🇱🇹",
    "Luxembourg": "🇱🇺",
    "Madagascar": "🇲🇬",
    "Malawi": "🇲🇼",
    "Malaysia": "🇲🇾",
    "Maldives": "🇲🇻",
    "Mali": "🇲🇱",
    "Malta": "🇲🇹",
    "Marshall Islands": "🇲🇭",
    "Mauritania": "🇲🇷",
    "Mauritius": "🇲🇺",
    "Mexico": "🇲🇽",
    "Micronesia": "🇫🇲",
    "Moldova": "🇲🇩",
    "Monaco": "🇲🇨",
    "Mongolia": "🇲🇳",
    "Montenegro": "🇲🇪",
    "Morocco": "🇲🇦",
    "Mozambique": "🇲🇿",
    "Myanmar": "🇲🇲",
    "Namibia": "🇳🇦",
    "Nauru": "🇳🇷",
    "Nepal": "🇳🇵",
    "Netherlands": "🇳🇱",
    "New Zealand": "🇳🇿",
    "Nicaragua": "🇳🇮",
    "Niger": "🇳🇪",
    "Nigeria": "🇳🇬",
    "North Macedonia": "🇲🇰",
    "Norway": "🇳🇴",
    "Oman": "🇴🇲",
    "Pakistan": "🇵🇰",
    "Palau": "🇵🇼",
    "Panama": "🇵🇦",
    "Papua New Guinea": "🇵🇬",
    "Paraguay": "🇵🇾",
    "Peru": "🇵🇪",
    "Philippines": "🇵🇭",
    "Poland": "🇵🇱",
    "Portugal": "🇵🇹",
    "Qatar": "🇶🇦",
    "Romania": "🇷🇴",
    "Russia": "🇷🇺",
    "Rwanda": "🇷🇼",
    "Saint Kitts & Nevis": "🇰🇳",
    "Saint Lucia": "🇱🇨",
    "Saint Vincent & Grenadines": "🇻🇨",
    "Samoa": "🇼🇸",
    "San Marino": "🇸🇲",
    "Sao Tome & Principe": "🇸🇹",
    "Saudi Arabia": "🇸🇦",
    "Senegal": "🇸🇳",
    "Serbia": "🇷🇸",
    "Seychelles": "🇸🇨",
    "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "Scottish": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "Sierra Leone": "🇸🇱",
    "Singapore": "🇸🇬",
    "Slovakia": "🇸🇰",
    "Slovenia": "🇸🇮",
    "Solomon Islands": "🇸🇧",
    "Somalia": "🇸🇴",
    "South Africa": "🇿🇦",
    "South Sudan": "🇸🇸",
    "Spain": "🇪🇸",
    "Sri Lanka": "🇱🇰",
    "Sudan": "🇸🇩",
    "Suriname": "🇸🇷",
    "Switzerland": "🇨🇭",
    "Syria": "🇸🇾",
    "Taiwan": "🇹🇼",
    "Tajikistan": "🇹🇯",
    "Tanzania": "🇹🇿",
    "Thailand": "🇹🇭",
    "Togo": "🇹🇬",
    "Tonga": "🇹🇴",
    "Trinidad & Tobago": "🇹🇹",
    "Tunisia": "🇹🇳",
    "Turkey": "🇹🇷",
    "Turkmenistan": "🇹🇲",
    "Tuvalu": "🇹🇻",
    "Uganda": "🇺🇬",
    "Ukraine": "🇺🇦",
    "United Arab Emirates": "🇦🇪",
    "United Kingdom": "🇬🇧",
    "United States": "🇺🇸",
    "Uruguay": "🇺🇾",
    "Uzbekistan": "🇺🇿",
    "Vanuatu": "🇻🇺",
    "Vatican City": "🇻🇦",
    "Venezuela": "🇻🇪",
    "Vietnam": "🇻🇳",
    "Yemen": "🇾🇪",
    "Zambia": "🇿🇲",
    "Zimbabwe": "🇿🇼",
}
