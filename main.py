
from pathlib import Path
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs
import os
from loguru import logger
from bs4 import BeautifulSoup
import tldextract
import re

logger.add("logs.log", format="{time} {level} {message}", level="INFO", rotation="1 MB")

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
			yield scrapy.Request(url=url, callback=self.parse_for_menu_urls)

	def parse_for_menu_urls(self, response):
		page_body = response.body
		soup = BeautifulSoup(page_body)

		possible_menu_anchors = soup.select("a[href*=menu]")
		menu_hrefs = {
			anchor.get("href") for anchor in possible_menu_anchors
			if anchor.get("href")
		}
		if not menu_hrefs:
			...
			logger.warning(f"No menu links found on {response.url}")
			# TODO: parse for locations https://www.girlandthegoat.com/, https://www.momotarochicago.com/, https://www.happycamper.pizza/

		urls = set()
		queries_to_remove = (
			"source",
			"spot_id",
			"promotion"
		)
		for url in menu_hrefs:
			if not url.startswith("http"):
				url = response.urljoin(url)
			u = urlparse(url)
			query = parse_qs(u.query, keep_blank_values=True)
			for q in queries_to_remove:
				query.pop(q, None)
			u = u._replace(query=urlencode(query, True))
			urls.add(urlunparse(u))

		for href in urls:
			yield scrapy.Request(url=href, callback= self.parse_menu_page)

	def parse_menu_page(self, response):
		parsed_url = tldextract.extract(response.url)
		page_body = response.body
		path = urlparse(response.url).path
		soup = BeautifulSoup(page_body)

		output_dir = Path("output") / f"{parsed_url.fqdn}{path}"
		if output_dir.exists() is False:
			output_dir.mkdir(parents=True)

		logger.info(response.url)
		with open(output_dir / f"menu_source.html", "wb") as f:
			f.write(page_body)

		# TODO: Add logic to check if the page is a menu page
		# TODO: Add logic to find links to sections of the menuthen parse those pages as menu pages
		# TODO: Add logic to identify PDFs
		# TODO: Add logic to identify image menus
		# TODO: Add logic to identify iframes

		with open(output_dir / f"menu.txt", "w+") as f:
			text = re.sub(r"\n\n+", r"\n\n", soup.get_text())
			text = re.sub(r"[^\S\r\n]+", " ", text)
			text = text.replace("\t", "")
			text = f"{response.url}\n\n{text}"
			f.write(text)
			logger.info(f"{len(text): <5} - {response.url}")


def main():
	logger.info("Starting")
	process = CrawlerProcess(get_project_settings())
	process.crawl(MenusSpider)
	process.start()
	logger.info("Finished")

if __name__ == "__main__":
	main()
