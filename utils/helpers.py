import base64
from contextlib import suppress
import aiohttp
from bs4 import BeautifulSoup
from bot.config import Config
from pyrogram.types import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
import aiohttp
from database import db

home_xpath = "html body main div div div:nth-of-type(2) div div:nth-of-type(1) div:nth-of-type(1) div:nth-of-type(1) div div:nth-of-type(1)"
away_xpath = "html body main div div div:nth-of-type(2) div div:nth-of-type(1) div:nth-of-type(1) div:nth-of-type(3) div div:nth-of-type(2)"
home_corner_kick_xpath = "html body main div div div:nth-of-type(4) div:nth-of-type(1) div:nth-of-type(1) div:nth-of-type(3) div:nth-of-type(1) div:nth-of-type(1)"
away_corner_kick_xpath = "html body main div div div:nth-of-type(4) div:nth-of-type(1) div:nth-of-type(1) div:nth-of-type(3) div:nth-of-type(1) div:nth-of-type(9)"
time_status_xpath = "html body main div div div:nth-of-type(2) div div:nth-of-type(1) div:nth-of-type(1) div:nth-of-type(2) div div:nth-of-type(2) span"
home_red_card_xpath = "html body main div div div:nth-of-type(4) div:nth-of-type(1) div:nth-of-type(1) div:nth-of-type(3) div:nth-of-type(1) div:nth-of-type(2) span:nth-of-type(2)"
home_yellow_card_xpath = "html body main div div div:nth-of-type(4) div:nth-of-type(1) div:nth-of-type(1) div:nth-of-type(3) div:nth-of-type(1) div:nth-of-type(3) span:nth-of-type(2)"
away_red_card_xpath = "html body main div div div:nth-of-type(4) div:nth-of-type(1) div:nth-of-type(1) div:nth-of-type(3) div:nth-of-type(1) div:nth-of-type(8) span:nth-of-type(2)"
away_yellow_card_xpath = "html body main div div div:nth-of-type(4) div:nth-of-type(1) div:nth-of-type(1) div:nth-of-type(3) div:nth-of-type(1) div:nth-of-type(7) span:nth-of-type(2)"


async def prettify_table_to_markdown(html):
    if isinstance(html, str):
        html = [html]

    data = []
    for h in html:
        soup = BeautifulSoup(h, "html.parser")
        table = soup.find("table")  # Assuming there is only one table element
        # table = ""
        if not table:
            return ""  # No table found

        for row in table.find_all("tr"):
            href = ""
            image = ""
            cells = []
            for td in row.find_all("td"):
                if td.find("a"):
                    href = Config.WEBSITE_URL + td.find("a")["href"]
                elif td.find("img"):
                    image = td.find("img")["alt"].replace("flag", "").strip()
                cells.append(td.get_text().strip())
            if cells:
                if len(cells) == 2:
                    cells.pop(1)

                if len(cells) == 9:
                    cells = cells[2:5]

                cells.append("\n")
                row_text = " | ".join(cells)

                if len(cells) == 2:
                    row_text = row_text.replace("\n", " ")
                    flag = FLAGS.get(image, "")
                    row_text = f"{flag} {row_text.replace(' | ', ' ')} "
                    if "International" in row_text:
                        row_text = f"🗺️ {row_text}"
                    if "UEFA" in row_text:
                        row_text = "⚽ " + row_text

                if href:
                    row_text = row_text.replace("\n", " ").strip()
                    row_text = row_text[::-1].replace("|", "", 1)[::-1]
                    row_text = f"{row_text}"

                data.append({"row_text": row_text, "href": href})

    return data or ""


async def set_commands(client):
    commands = [
        BotCommand(command="start", description="Check if bot is alive"),
        BotCommand(command="live", description="Get live matches"),
        BotCommand(command="search", description="Search for matches"),
    ]

    await client.set_bot_commands(commands)


async def get_source(url):
    i = 1
    sources = []
    while True:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{url}?page={i}") as resp:
                if resp.status != 200:
                    print(f"Status code: {resp.status}")
                    print(resp.reason)
                    print(f"Broke at page {i}")
                    break
                data = await resp.text()
                sources.append(data)
                i += 1

    return sources


async def get_matches():
    sources = await get_source(Config.WEBSITE_URL)
    data = await prettify_table_to_markdown(sources)
    print(str(data) + "\n")
    Config.MATCHES = data


async def get_match_summary(url):
    match_id = url.split("/")[-2]
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            page = await response.text()
    soup = BeautifulSoup(page, "html.parser")

    home_team = soup.select_one(home_xpath).text.strip()
    away_team = soup.select_one(away_xpath).text.strip()
    home_score = soup.find("div", id="home-score").text.strip()
    away_score = soup.find("div", id="away-score").text.strip()
    time_status = soup.select_one(time_status_xpath).text.strip()

    home_corner_kick = soup.select_one(home_corner_kick_xpath).text.strip()
    away_corner_kick = soup.select_one(away_corner_kick_xpath).text.strip()

    home_red_card = soup.select_one(home_red_card_xpath).text.strip()
    home_yellow_card = soup.select_one(home_yellow_card_xpath).text.strip()
    away_red_card = soup.select_one(away_red_card_xpath).text.strip()
    away_yellow_card = soup.select_one(away_yellow_card_xpath).text.strip()
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
            text = f"Goal! {match_summary['home_team']} scored against {match_summary['away_team']}!"
            text_to_sent.append(text)
        if match["away_score"] != match_summary["away_score"]:
            text = f"Goal! {match_summary['away_team']} scored against {match_summary['home_team']}!"
            text_to_sent.append(text)
        if match["home_corner_kick"] != match_summary["home_corner_kick"]:
            text = f"Corner Kick! {match_summary['home_team']} got a corner kick!"
            text_to_sent.append(text)
        if match["away_corner_kick"] != match_summary["away_corner_kick"]:
            text = f"Corner Kick! {match_summary['away_team']} got a corner kick!"
            text_to_sent.append(text)
        if match["home_red_card"] != match_summary["home_red_card"]:
            text = f"Red Card! {match_summary['home_team']} got a red card!"
            text_to_sent.append(text)
        if match["home_yellow_card"] != match_summary["home_yellow_card"]:
            text = f"Yellow Card! {match_summary['home_team']} got a yellow card!"
            text_to_sent.append(text)
        if match["away_red_card"] != match_summary["away_red_card"]:
            text = f"Red Card! {match_summary['away_team']} got a red card!"
            text_to_sent.append(text)
        if match["away_yellow_card"] != match_summary["away_yellow_card"]:
            text = f"Yellow Card! {match_summary['away_team']} got a yellow card!"
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
