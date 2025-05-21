# core/management/commands/scrape_aims.py

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
import json

class Command(BaseCommand):
    help = "Scrapes the aims category page using Selenium with improved anti-bot evasion."

    def handle(self, *args, **options):
        url = "http://www.amis.pk/Daily%20Market%20Changes.aspx"

        chrome_options = Options()
        chrome_options.headless = True 
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0"
        )
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Start the Chrome driver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        # Execute JavaScript to override the navigator.webdriver property if needed
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                  get: () => undefined
                })
            """
        })

        self.stdout.write("Opening the page...")
        driver.get(url)

        # Wait for dynamic content to load;
        time.sleep(5)

        # Get the final rendered page source
        page_source = driver.page_source
        driver.quit()

        # Save the rendered HTML to a file for inspection
        with open("aims_page_rendered.html", "w", encoding="utf-8") as f:
            f.write(page_source)

        self.stdout.write(self.style.SUCCESS("Rendered page source saved to aims_page_rendered.html"))

        # Parse the HTML with BeautifulSoup 
        soup = BeautifulSoup(page_source, "html.parser")

        # Find the main table (assume first table on the page)
        table = soup.find("table")
        data = []
        if table:
            headers = []
            header_row = table.find("tr")
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all("th")]
            for row in table.find_all("tr")[1:]:
                cells = row.find_all(["td", "th"])
                if not cells:
                    continue
                row_data = {}
                for i, cell in enumerate(cells):
                    key = headers[i] if i < len(headers) else f"col_{i+1}"
                    row_data[key] = cell.get_text(strip=True)
                data.append(row_data)

        # Save as JSON
        with open("aims_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.stdout.write(self.style.SUCCESS(f"Extracted {len(data)} rows and saved to aims_data.json"))

        self.stdout.write(self.style.SUCCESS("Scraping finished successfully!"))
