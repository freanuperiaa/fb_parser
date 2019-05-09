import scrapy
from scrapy.crawler import CrawlerProcess, Crawler

from .scraper import GroupPostsSpider


def scrape(inp_email, inp_pass):
    crawler = Crawler(GroupPostsSpider, {
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
        'ROBOTSTXT_OBEY': False,
    })
    process = CrawlerProcess()

    process.crawl(crawler, email=inp_email, password=inp_pass)
    process.start()
