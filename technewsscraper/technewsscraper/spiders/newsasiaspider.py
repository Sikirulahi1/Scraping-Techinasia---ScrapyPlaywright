import scrapy
import time
import os
from dotenv import load_dotenv
from urllib.parse import urlencode
from scrapy_playwright.page import PageMethod

load_dotenv()

class NewsasiaspiderSpider(scrapy.Spider):
    name = "newsasiaspider"
    allowed_domains = ["www.techinasia.com", "proxy.scrapeops.io"]
    
    API_KEY = os.getenv("SCRAPY_API_KEY")

    def get_proxy_url(self, url):
        payload = {'api_key': self.API_KEY, 'url': url}
        proxy_url = 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)
        return proxy_url

    def start_requests(self):
        # Define the start URL
        start_url = "https://www.techinasia.com/news?category=all"
        # Yield request using Scrapy Playwright middleware
        yield scrapy.Request(url = start_url, 
                             meta=dict(
                                 playwright=True,  # Enable playwright
                                 playwright_include_page=True,
                                 playwright_page_methods=[
                                    # PageMethod("route", "**/*", lambda route: route.abort() if route.request.resource_type in ["image", "stylesheet"] else route.continue_()),
                                    PageMethod('wait_for_selector', 'div.jsx-1678928787.post-image'),
                                    # PageMethod("evaluate", "window.scrollBy(0, document.body.scrollHeight)"),
                                    # PageMethod("wait_for_selector", "div.jsx-1678928787.post-image:nth-child(11)")
                                    ],
                             ), 
                             callback=self.parse,  # Set parse method as the callback
                             errback=self.errback)

    async def parse(self, response):
        page = response.meta["playwright_page"]
        
        # Extracting the links
        links = await page.locator('div.jsx-1678928787.post-image a').all()
        # links = await page.locator('div.jsx-1678928787.post-image a').all()
        for element in links:
            href = await element.get_attribute('href')
            if href:
                absolute_url = response.urljoin(href)  # Make the link absolute
                
                if absolute_url.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')):  # Image file extensions
                    continue

                print(absolute_url)
                print("--------------------------------------------------------------------")
                self.logger.info(f"Found link: {absolute_url}")
                
                # Yield a new request to the extracted link
                yield scrapy.Request(
                    url=absolute_url, 
                    meta=dict(
                        playwright=True,
                        playwright_include_page=True,
                        playwright_page_goto_timeout= 60000,
                        playwright_page_methods=[
                            PageMethod('wait_for_load_state', 'networkidle'),
                            PageMethod('wait_for_selector', 'h2.jsx-3509540955.title')

                        ],
                    ),
                    callback=self.parse_page_content,  # Callback to process the new page
                    errback=self.errback
                )
        
        # Extract additional data if needed
        # You can do more parsing here or yield additional requests
        
        await page.close()  # Close the page once scraping is done

    async def parse_page_content(self, response):
        """Callback to parse the content of the new pages."""
        page = response.meta["playwright_page"]

        title_selector = "h2.jsx-3509540955.title"
        # title_element = await page.locator(title_selector).first()
        # title_text = await title_element.inner_text()
        title_text = response.css(title_selector).get()
        print(title_text.strip())

        paragraphs = response.css("div#content p::text").getall()
        print(paragraphs)
        
        # Join the extracted paragraphs into a full content string
        full_content = "\n".join(paragraphs)

        self.logger.info(f"Extracted Title: {title_text}")
        self.logger.info("Content extracted successfully.")
        
        # Yield the result as an item
        yield {
            "title": title_text.strip(),
            "news_content": full_content.strip()
        }

        await page.close()

    async def errback(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.close()
