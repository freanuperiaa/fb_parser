import scrapy
from scrapy import FormRequest


class GroupPostsSpider(scrapy.Spider):

    def __init__(self, *args, **kwargs):
        # We are going to pass these args from our django view.
        self.email = kwargs.get('email')
        self.password = kwargs.get('password')
        self.name = 'group_posts_spider'
        self.facebook = 'https://mbasic.facebook.com'
        self.start_urls = [self.facebook]

    def clean_url(self, url):
        url = url[:(url.find('?refid'))]
        url = url[:(url.find('&fref'))]
        url = url[:(url.find('%3Amf'))]
        url = url[:(url.find('?fref'))]
        if self.facebook in url:
            return url
        else:
            return self.facebook + url

    def parse(self, response):
        # prompt for username and password, then login
        # email = input('enter email of fb account: ')
        # password = input('enter password: ')
        return FormRequest.from_response(
            response,
            formxpath='//form[contains(@action, "login")]',
            formdata={
                'email': self.email, 'pass': self.password
            },
            callback=self.parse_home
            )

    def parse_home(self, response):
        # goes through the 'save device' part by not saving device
        if response.xpath("//div/a[contains(@href,'save-device')]"):
            self.logger.info('"save-device" checkpoint. redirecting...')
            return FormRequest.from_response(
                response,
                formdata={'name_action_selected': 'dont_save'},
                callback=self.parse_home
            )
        # if "don't save" is selected, go on to the groups page
        return scrapy.Request(
            url='https://mbasic.facebook.com/groups/?seemore',
            callback=self.parse_group_list
        )

    def parse_group_list(self, response):
        # parse urls of all of the groups of the current account
        groups = response.selector.xpath(
                 '/html/body/div/div/div[2]/div/table/tbody/tr/td/div[2]/ul'
                 '/li/table/tbody/tr/td/a/@href'
        ).extract()
        self.logger.info('gathered groups:')
        for group in groups:
            url = self.facebook + group
            self.logger.info(url)
            # go scrape each groups
            yield scrapy.Request(url=url, callback=self.parse_group)

    def parse_group(self, response):
        # for every postings in the group page, parse
        # posting's 'FULL STORY' link
        indiv_postings_urls = response.selector.xpath(
            '/html/body/div/div/div[2]/div/div[1]/div[5]/div[1]/div/div[2]'
            '/div[2]/a[3][contains(@href, "/groups/")]/@href').extract()
        for x in indiv_postings_urls:
            url = self.clean_url(x)
            self.logger.info(url)
            yield scrapy.Request(
                url=url,
                callback=self.parse_indiv_posting
            )
        # go check and scroll to see more postings
        if response.selector.xpath('//span[contains(text(), "See More Posts")]'):
            next_page = response.selector.xpath(
                       '//*[@id="m_group_stories_container"]/div[2]/a/@href'
            ).extract()
            next_group = str(self.facebook + next_page[0])
            self.logger.info('going to next page...')
            yield scrapy.Request(url=next_group, callback=self.parse_group)

    def parse_indiv_posting(self, response):
        # yield an item
        # or yield individual components of the posting
        post = {
            'title': response.xpath(
                '/html/body/div/div/div[2]/div/div[1]/div[1]/div/div[1]/div[3]'
                '/div[1]/div[1]/span[2]/text()'
            ).extract(),
            'post url': self.clean_url(response.request.url),
            'group': response.xpath(
                '/html/body/div/div/div[2]/div/div[1]/div[1]/div/div[1]/div[1]'
                '/table/tbody/tr/td[2]/div/h3/span/strong[2]/a/text()'
            ).extract(),
            'group url': self.clean_url(response.xpath(
                '/html/body/div/div/div[2]/div/div[1]/div[1]/div/div[1]/div[1]'
                '/table/tbody/tr/td[2]/div/h3/span/strong[2]/a/@href'
            ).extract()[0]),
            'author': response.xpath(
                '/html/body/div/div/div[2]/div/div[1]/div[1]/div/div[1]/div[1]'
                '/table/tbody/tr/td[2]/div/h3/span/strong[1]/a/text()'
            ).extract(),
            'author url': self.clean_url(response.xpath(
                '/html/body/div/div/div[2]/div/div[1]/div[1]/div/div[1]/div[1]'
                '/table/tbody/tr/td[2]/div/h3/span/strong[1]/a/@href'
            ).extract()[0]),
            'description': ''.join(response.xpath(
                '/html/body/div/div/div[2]/div/div[1]/div[1]/div/div[1]/div[3]'
                '/div[1]/div[4]/p/text()'
            ).extract()),
            'post_url': response.request.url,
        }
        reactions = self.facebook + response.xpath(
            '//a[contains(@href, "/ufi/reaction")]/@href').extract()[0]

        yield scrapy.Request(url=reactions, callback=self.parse_reactions, meta=post)

    def parse_reactions(self, response):
        self.logger.info('parse post info, including reacts')
        print('title: ', response.meta.get('title'))
        print('post url: ', response.meta.get('post url'))
        print('group: ', response.meta.get('group'))
        print('group url: ', response.meta.get('group url'))
        print('author: ', response.meta.get('author'))
        print('author url: ', response.meta.get('author url'))
        print('description: ', response.meta.get('description'))
        all_reacts = response.xpath('//a[contains(text(), "All")]/text()').extract()
        likes = response.xpath(
            '//a[contains(@href, "ufi/reaction")]/img[@alt="Like"]/'
            'following-sibling::span/text()'
        ).extract()
        heart = response.xpath(
            '//a[contains(@href, "ufi/reaction")]/img[@alt="Love"]/'
            'following-sibling::span/text()'
        ).extract()
        wow = response.xpath(
            '//a[contains(@href, "ufi/reaction")]/img[@alt="Wow"]/'
            'following-sibling::span/text()'
        ).extract()
        haha = response.xpath(
            '//a[contains(@href, "ufi/reaction")]/img[@alt="Haha"]/'
            'following-sibling::span/text()'
        ).extract()
        sad = response.xpath(
            '//a[contains(@href, "ufi/reaction")]/img[@alt="Sad"]/'
            'following-sibling::span/text()'
        ).extract()
        angry = response.xpath(
            '//a[contains(@href, "ufi/reaction")]/img[@alt="Angry"]/'
            'following-sibling::span/text()'
        ).extract()
        print('total reacts: ', all_reacts[3:])
        print('likes:', likes, '\nheart: ', heart, '\nwow: ', wow, '\nhaha:',
              haha, '\nsad: ', sad, '\nangry: ', angry)
        go_back = response.meta.get('post_url')
        yield scrapy.Request(url=go_back, callback=self.parse_comments,
                             dont_filter=True)

    def parse_comments(self, response):
        # get the comments in the page
        self.logger.info('parse comments of post')
        comments = response.xpath(
            '//div[string-length(@class) = 2 and count(@id)=1 and contains'
            '("0123456789", substring(@id,1,1))]')
        # iterate through the comments div collected
        print(self.clean_url(response.request.url))
        for comment in comments:
            # author
            print(comment.xpath('./div/h3/a/text()').extract())
            # text
            print(comment.xpath('./div/div[1]/text()').extract())
            # time
            print(comment.xpath('./div/div[3]/abbr/text()').extract())
            # reacts
            print(comment.xpath('./div/div/span/span/a[1]/span/'
                                'following-sibling::text()').extract())

        reply_url = comments.xpath(
            '//div[contains(@id, "comment_replies")]//a[string-length'
            '(@class) = 2 and contains(@href, "comment/replies")]/@href'
        ).extract()
        try:
            prev_comments = response.xpath(
                '//a[contains(@href, "/story.php?") and contains(text(), "View '
                'previous comments")]/@href').extract()[0]
        except IndexError:
            prev_comments = None
        if prev_comments is not None:
            yield scrapy.Request(url=(self.facebook+prev_comments),
                                 callback=self.parse_comments)
