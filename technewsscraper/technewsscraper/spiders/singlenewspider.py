import scrapy

import scrapy
from scrapy_playwright.page import PageMethod

class SinglenewspiderSpider(scrapy.Spider):
    name = "singlenewspider"
    allowed_domains = ["www.techinasia.com"]

    def start_requests(self):
        # Input the specific URL you want to scrape
        url = "https://www.techinasia.com/news/alibaba-sell-intime-retail-department-store-13b-loss"  # Replace with the desired URL
        yield scrapy.Request(
            url=url,
            meta=dict(
                playwright=True,
                playwright_include_page=True,
                playwright_page_methods=[
                    PageMethod('wait_for_load_state', 'networkidle'),
                    PageMethod('wait_for_selector', 'h2.jsx-3509540955.title', timeout=240000),
                ],
            ),
            callback=self.parse_page_content,
            errback=self.errback
        )

    async def parse_page_content(self, response):
        """Extract the title and content of the page."""
        title = response.css("h2.jsx-3509540955.title::text").get()
        paragraphs = response.css("div#content p::text").getall()
        content = "\n".join(paragraphs)
        print(title.strip())

        if title:
            self.logger.info(f"Extracted Title: {title.strip()}")
        else:
            self.logger.warning("Title not found.")
        
        if content:
            self.logger.info("Content extracted successfully.")
        else:
            self.logger.warning("Content not found.")
        
        # Yield the scraped data
        yield {
            "title": title.strip() if title else "No Title Found",
            "news_content": content.strip() if content else "No Content Found"
        }

    async def errback(self, failure):
        """Handle errors."""
        self.logger.error(f"Error occurred: {failure}")
