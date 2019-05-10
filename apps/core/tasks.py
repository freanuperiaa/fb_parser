import scrapy
from scrapy.crawler import CrawlerProcess, Crawler
from celery import shared_task

from .scraper import GroupPostsSpider, IndividualGroupPostSpider

@shared_task
def scrape(inp_email, inp_pass):
    crawler = Crawler(GroupPostsSpider, {
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
        'ROBOTSTXT_OBEY': False,
    })
    process = CrawlerProcess()

    process.crawl(crawler, email=inp_email, password=inp_pass)
    process.start()

@shared_task
def scrape_group(inp_email, inp_pass, group_url):
    crawler = Crawler(IndividualGroupPostSpider, {
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
        'ROBOTSTXT_OBEY': False,
    })
    process = CrawlerProcess()

    process.crawl(crawler, email=inp_email, password=inp_pass, group_url=group_url)
    process.start()
