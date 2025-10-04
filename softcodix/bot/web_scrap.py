import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .models import PageContent

def scrape_all_pages(domain, limit=20):
    visited = set()
    to_visit = [domain]

    while to_visit and len(visited) < limit:
        url = to_visit.pop(0)
        if url in visited:
            continue
        try:
            res = requests.get(url, timeout=5)
            if res.status_code != 200:
                continue
            soup = BeautifulSoup(res.text, "html.parser")
            text = soup.get_text(" ", strip=True)

            # Save to DB
            PageContent.objects.update_or_create(
                url=url,
                defaults={"content": text[:2000]}
            )

            # Extract more links
            for link in soup.find_all("a", href=True):
                new_url = urljoin(domain, link["href"])
                if domain in new_url and new_url not in visited:
                    to_visit.append(new_url)

            visited.add(url)
        except Exception as e:
            print("Error:", e)

    return visited
