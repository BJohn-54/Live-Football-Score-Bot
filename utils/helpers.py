from bs4 import BeautifulSoup
from bot.config import Config


async def prettify_table_to_markdown(html):
    data = []
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")  # Assuming there is only one table element
    # table = ""
    if not table:
        return ""  # No table found

    for row in table.find_all("tr"):
        href = ""
        cells = []
        for td in row.find_all("td"):
            if td.find("a"):
                href = Config.WEBSITE_URL + td.find("a")["href"]
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
                row_text = f"🏆 {row_text.replace(' | ', ' ')} "

            if href:
                row_text = row_text.replace("\n", " ").strip()
                # replace the last | with a ]( to make the link work
                row_text = row_text[::-1].replace("|", "", 1)[::-1]
                row_text = f"{row_text}"

            data.append({"row_text": row_text, "href": href})

    return data or ""
