import os
import re
import csv
import time
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

# =============================
# Configuration
# =============================
BASE_URL = "https://cafef.vn/thi-truong-chung-khoan.chn"
DATA_DIR = "data"
LOG_DIR = "logs"
CSV_FILE = os.path.join(DATA_DIR, "cafef_news.csv")
LOG_FILE = os.path.join(LOG_DIR, "crawl.log")
CHROMIUM_PATH = "/usr/bin/chromium-browser"  # your Chromium path
MAX_PAGES = 5  # Number of pages you want to crawl

# Create a folder if it doesn't exist.
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# =============================
# Logging
# =============================
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

# =============================
# Initialize Selenium
# =============================
chrome_options = Options()
chrome_options.binary_location = CHROMIUM_PATH
chrome_options.add_argument("--headless")  
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
driver = webdriver.Chrome(options=chrome_options)

# =============================
# Get a list of article links from multiple pages
# =============================
def get_article_links():
    links = []
    for page in range(1, MAX_PAGES + 1):
        if page == 1:
            url = BASE_URL
        else:
            url = f"https://cafef.vn/thi-truong-chung-khoan.chn/trang-{page}.chn"

        logging.info(f"🔍 Opening page: {url}")
        print(f"🔍 Opening page: {url}")

        driver.get(url)
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        for tag in soup.find_all("a", href=True):
            href = tag["href"]
            if (
                href.startswith("/") and
                href.endswith(".chn") and
                re.search(r"\d{12,}", href)
            ):
                full_url = "https://cafef.vn" + href
                if full_url not in links:
                    links.append(full_url)

        logging.info(f"🔗 Page {page}: {len(links)} current link")
        print(f"🔗 Page {page}: {len(links)} current link")

    logging.info(f"🔗 Total: {len(links)} posts")
    print(f"🔗 Total: {len(links)} posts")
    return links

# =============================
# Crawl the content of each article
# =============================
def parse_article(url):
    #driver.set_page_load_timeout(30)
    driver.get(url)
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else ""

    body_tag = soup.find("div", class_="contentdetail")
    body = body_tag.get_text(strip=True) if body_tag else ""

    return {
        "url": url,
        "title": title,
        "content": body,
        "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# =============================
# Save to CSV
# =============================
def save_to_csv(new_data):
    existing_data = {}

    # Đọc dữ liệu cũ (nếu có)
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_data[row["url"]] = row

    # Overwrite or add new
    for item in new_data:
        existing_data[item["url"]] = item

    # Record everything
    with open(CSV_FILE, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["crawled_at", "title", "url", "content"])
        writer.writeheader()
        for row in existing_data.values():
            writer.writerow(row)


# =============================
# Main
# =============================
if __name__ == "__main__":
    article_links = get_article_links()

    if not article_links:
        logging.warning("⛔ No posts found.")
        print("⛔ No posts found.")
    else:
        logging.info("🚀 Start crawling each post")
        print("🚀 Start crawling each post")

    articles = []
    for url in article_links:
        try:
            article = parse_article(url)
            articles.append(article)
            print(f"✅ The post has been taken: {article['title'][:50]}...")
        except Exception as e:
            logging.error(f"❌ Post error {url}: {e}")

    save_to_csv(articles)
    logging.info(f"✅ Crawl complete, save {len(articles)} post")
    print(f"✅ Crawl complete, save {len(articles)} post")

    driver.quit()
