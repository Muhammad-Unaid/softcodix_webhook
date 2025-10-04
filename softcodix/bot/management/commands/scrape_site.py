from django.core.management.base import BaseCommand
from bot.web_scrap import scrape_all_pages

class Command(BaseCommand):
    help = "Scrape entire site and save into PageContent"

    def handle(self, *args, **options):
        domain = "https://softcodix.com"   # 👈 apna domain fix kar do
        visited = scrape_all_pages(domain, limit=50)  # limit = max pages
        self.stdout.write(self.style.SUCCESS(f"Scraped {len(visited)} pages from {domain}"))
