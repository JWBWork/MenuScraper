
from pathlib import Path
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import os
from loguru import logger
from bs4 import BeautifulSoup
import tldextract
import re


class MenusSpider(scrapy.Spider):
    name = "Menus"

    def get_urls(self):
        with open("restaurants.txt", "r") as f:
            urls = f.read().splitlines()
            logger.info(f"Loaded {len(urls)} urls")
            return urls

    def start_requests(self):
        urls = self.get_urls()
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        page_body = response.body
        soup = BeautifulSoup(page_body)
        
        possible_menu_anchors = soup.select("a[href*=menu]")
        menu_hrefs = {
            anchor.get("href") for anchor in possible_menu_anchors
            if anchor.get("href")
        }

        absolute_menu_hrefs = list({
            href 
            if href.startswith("http") 
            else response.urljoin(href)
            for href in menu_hrefs
        })
        for href in absolute_menu_hrefs:
            yield scrapy.Request(url=href, callback= self.parse_menu_page)

    def parse_menu_page(self, response):
        domain = tldextract.extract(response.url).domain
        page_body = response.body

        output_dir = Path("output") / domain
        if output_dir.exists() is False:
            output_dir.mkdir(parents=True)
        
        with open(output_dir / f"menu-{len(os.listdir(output_dir))}.html", "wb") as f:
            f.write(page_body)
        
        # TODO: Add logic to check if the page is a menu page
        # TODO: Add logic to find links to sections of the menuthen parse those pages as menu pages
        # TODO: Add logic to identify PDFs
        # TODO: Add logic to identify image menus
        # TODO: Add logic to identify iframes


def main():
    process = CrawlerProcess(get_project_settings())
    process.crawl(MenusSpider)
    process.start()

if __name__ == "__main__":
    main()
