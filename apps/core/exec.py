import scrapy
from scrapy.crawler import CrawlerProcess

from scraper import GroupPostsSpider


def scrape(inp_email, inp_pass):
    spider = GroupPostsSpider(email=inp_email, password=inp_pass)
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
        'ROBOTSTXT_OBEY': False,
    })

    process.crawl(spider)
    process.start()  # the script will block here until the crawling is finished