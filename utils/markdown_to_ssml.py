import markdown
import re
from bs4 import BeautifulSoup

def md_to_ssml(md: str, heading_pause_ms: int = 600) -> str:
    """Turn markdown into SSML without altering wording."""
    html = markdown.markdown(md)
    soup = BeautifulSoup(html, "html.parser")

    # unwrap bold / italics so the TTS reads plain words
    for tag in soup.select("strong, em, code"):
        tag.unwrap()

    # pause before each heading
    for h in soup.find_all(re.compile("^h[1-6]$")):
        h.insert_before(soup.new_tag("break", time=f"{heading_pause_ms}ms"))
        h.name = "p"

    # list bullets → sentences
    for li in soup.find_all("li"):
        li.insert_after(" ")

    text = soup.get_text(" ", strip=True)
    return f"<speak>{text}</speak>"