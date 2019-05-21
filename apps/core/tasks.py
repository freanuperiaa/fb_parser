import logging

from scrapy.crawler import CrawlerProcess, Crawler
from celery import shared_task
from scrapy.utils.log import configure_logging

from .scraper import GroupPostsSpider, IndividualGroupPostSpider


@shared_task
def scrape(email, password, *args, **kwargs):
    logging.basicConfig(
        format='%(levelname)s: %(message)s',
        level=logging.ERROR
    )
    configure_logging(install_root_handler=False)
    # set both loggers below to False to have no log message
    # logging.getLogger('scrapy').propagate = False
    logging.getLogger('celery').propagate = False
    crawler = Crawler(GroupPostsSpider, {
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
        'ROBOTSTXT_OBEY': False,
        'LOG_LEVEL': 'ERROR',
    })
    process = CrawlerProcess()

    process.crawl(crawler, email=email, password=password)
    process.start()


@shared_task
def scrape_group(email, password, url):
    logging.basicConfig(
        format='%(levelname)s: %(message)s',
        level=logging.ERROR
    )
    configure_logging(install_root_handler=False)
    # set both loggers below to False to have no log message
    # logging.getLogger('scrapy').propagate = False
    logging.getLogger('celery').propagate = False
    crawler = Crawler(IndividualGroupPostSpider, {
        'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)',
        'ROBOTSTXT_OBEY': False,
        'LOG_LEVEL': 'ERROR',
    })
    process = CrawlerProcess()

    process.crawl(crawler, email=email, password=password, group_url=url)
    process.start()
