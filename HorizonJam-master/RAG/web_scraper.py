import requests
from bs4 import BeautifulSoup
import json

def scrape_and_save(url):
    print(f"🌐 Scraping: {url}")
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.content, 'html.parser')
    text = soup.get_text(separator='\n', strip=True)

    data = {
        "source": url,
        "content": text
    }

    # Load existing data
    try:
        with open('scraped_data.json', 'r') as f:
            existing_data = json.load(f)
    except FileNotFoundError:
        existing_data = []

    # Append and save
    existing_data.append(data)
    with open('scraped_data.json', 'w') as f:
        json.dump(existing_data, f, indent=2)

    print(f"✅ Saved content from: {url}")

# URLs to scrape
urls_to_scrape = [
    "https://www.jazzadvice.com/",
    "https://tonesavvy.com/",
    "https://www.earmaster.com/",
    "https://www.premierguitar.com/",
    "https://viva.pressbooks.pub/openmusictheory/",
    "https://iconcollective.edu/basic-music-theory/",
    "https://www.musictheory.net/lessons",
    "https://www.guitarinstitute.com/resources/",
    "https://www.sweetwater.com/sweetcare/",
    "https://www.guitartricks.com/",
    "https://en.wikipedia.org/wiki/Music_theory",
    "https://tonedear.com/"
]

if __name__ == "__main__":
    for url in urls_to_scrape:
        try:
            scrape_and_save(url)
        except Exception as e:
            print(f"❌ Failed to scrape {url}: {e}")
