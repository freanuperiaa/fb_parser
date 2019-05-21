import scrapy
from scrapy import FormRequest
from scrapy.utils import log

from .models import FacebookGroup, Post, Comment


class GroupPostsSpider(scrapy.Spider):

    custom_settings = {
        'LOG_LEVEL': 'ERROR',
    }

    def __init__(self, *args, **kwargs):
        # We are going to pass these args from our django view.
        self.email = kwargs.get('email')
        self.password = kwargs.get('password')
        self.name = 'group_posts_spider'
        self.facebook = 'https://mbasic.facebook.com'
        self.start_urls = [self.facebook]
        super().__init__(*args, **kwargs)

    def clean_url(self, url):
        url = url[:(url.find('?refid'))]
        url = url[:(url.find('&fref'))]
        url = url[:(url.find('%3Amf'))]
        url = url[:(url.find('?fref'))]
        if url != '':
            if self.facebook in url:
                return url
            else:
                return self.facebook + url
        else:
            return ''

    def get_element(self, element):
        '''

        :param element: the object returned by getting an element by XPath
        :return: if list is empty, returns '', else, returns first element
        '''
        if element == []:
            return ''
        else:
            return element[0]

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
            '/html/body/div/div/div[2]/div/table/tbody/tr/td'
            '/div[2]/ul/li/table/tbody/tr/td[1]'
        )
        self.logger.info('gathered groups:')
        for group in groups:
            url = [self.facebook + s for s in group.xpath('a/@href').extract()]
            url = url[0]
            name = group.xpath('a/text()').extract()
            name = name[0]
            if not FacebookGroup.objects.filter(name=name).exists():
                new_page = FacebookGroup(
                    name=name,
                    url=url,
                )
                new_page.save()
            self.logger.info('saved new facebook page instance')
            yield scrapy.Request(url=url, callback=self.parse_group)

    def parse_group(self, response):
        # for every postings in the group page, parse
        # posting's 'FULL STORY' link
        indiv_postings_urls = response.selector.xpath(
            '//span[@aria-hidden="true"]/following-sibling'
            '::a[contains(text(), "Full")]/@href'
        ).extract()
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
            'group': self.get_element(response.xpath(
                '//strong/following-sibling::a[contains(@href, "/groups/")]/'
                'text() | //strong/a[contains(@href, "/groups/")]/text()'
            ).extract()),
            'group url': self.clean_url(self.get_element(response.xpath(
                '/html/body/div/div/div[2]/div/div[1]/div[1]/div/div[1]/div[1]'
                '/table/tbody/tr/td[2]/div/h3/span/strong[2]/a/@href'
            ).extract())),
            'author': response.xpath(
                '/html/body/div/div/div[2]/div/div[1]/div[1]/div/div[1]/div[1]'
                '/table/tbody/tr/td[2]/div/h3/span/strong[1]/a/text()'
            ).extract(),
            'author url': self.clean_url(self.get_element(response.xpath(
                '/html/body/div/div/div[2]/div/div[1]/div[1]/div/div[1]/div[1]'
                '/table/tbody/tr/td[2]/div/h3/span/strong[1]/a/@href'
            ).extract())),
            'description': ''.join(response.xpath(
                '//div[string-length(@class) = 2]//p/text()'
            ).extract()),
        }
        reactions = self.facebook + response.xpath(
            '//a[contains(@href, "/ufi/reaction")]/@href').extract()[0]

        yield scrapy.Request(url=reactions, callback=self.parse_reactions, meta=post)

    def parse_reactions(self, response):
        self.logger.info('parse post info, including reacts')
        all_reacts = self.get_element(response.xpath(
            '//a[contains(text(), "All")]/text()').extract())
        likes = self.get_element(response.xpath(
            '//a[contains(@href, "ufi/reaction")]/img[@alt="Like"]/'
            'following-sibling::span/text()'
        ).extract())
        heart = self.get_element(response.xpath(
            '//a[contains(@href, "ufi/reaction")]/img[@alt="Love"]/'
            'following-sibling::span/text()'
        ).extract())
        wow = self.get_element(response.xpath(
            '//a[contains(@href, "ufi/reaction")]/img[@alt="Wow"]/'
            'following-sibling::span/text()'
        ).extract())
        haha = self.get_element(response.xpath(
            '//a[contains(@href, "ufi/reaction")]/img[@alt="Haha"]/'
            'following-sibling::span/text()'
        ).extract())
        sad = self.get_element(response.xpath(
            '//a[contains(@href, "ufi/reaction")]/img[@alt="Sad"]/'
            'following-sibling::span/text()'
        ).extract())
        angry = self.get_element(response.xpath(
            '//a[contains(@href, "ufi/reaction")]/img[@alt="Angry"]/'
            'following-sibling::span/text()'
        ).extract())
        # reason behind 'name__icontains' is because there are some
        # groups that have the names splitted on the full story page.
        this_group = FacebookGroup.objects.get(
            name__icontains=response.meta.get('group'))
        title = self.get_element(response.meta.get('title'))
        author = self.get_element(response.meta.get('author'))
        new_post = Post(
            title=title, url=self.clean_url(response.meta.get('post url')),
            group=this_group, author=author,
            author_url=response.meta.get('author url'), description=
            response.meta.get('description'), total_reacts=all_reacts,
            likes=likes, heart=heart, wow=wow, haha=haha, sad=sad, angry=angry,
        )
        new_post.save()
        self.logger.info('saved new post instance')
        go_back = response.meta.get('post url')
        yield scrapy.Request(url=go_back, callback=self.parse_comments,
                             dont_filter=True, meta={'post url': go_back})

    def parse_comments(self, response):
        # get the comments in the page
        self.logger.info('parse comments of post')
        title = self.get_element(
            response.xpath(
                '/html/body/div/div/div[2]/div/div[1]/div[1]/div/div[1]/div[3]'
                '/div[1]/div[1]/span[2]/text()'
            ).extract()
        )

        author = self.get_element(response.xpath(
                '/html/body/div/div/div[2]/div/div[1]/div[1]/div/div[1]/div[1]'
                '/table/tbody/tr/td[2]/div/h3/span/strong[1]/a/text()'
            ).extract())
        this_post = Post.objects.get(
            title=title, author=author, url=self.clean_url(response.request.url))
        comments = response.xpath(
            '//div[string-length(@class) = 2 and count(@id)=1 and contains'
            '("0123456789", substring(@id,1,1))]')
        # iterate through the comments div collected
        for comment in comments:
            # author
            author = self.get_element(
                comment.xpath('./div/div[1]/text()').extract())
            text = self.get_element(comment.xpath(
                './div/div[1]/text()').extract())
            time = self.get_element(comment.xpath(
                './div/div[3]/abbr/text()').extract())
            reacts = self.get_element(comment.xpath(
                './div/div/span/span/a[1]/span/following-sibling::text()'
            ).extract())
            new_comment = Comment(
                author=author, text=text, time=time, no_reacts=reacts,
                post=this_post,
            )
            new_comment.save()

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
        else:
            pass


class IndividualGroupPostSpider(GroupPostsSpider):

    def __init__(self, *args, **kwargs):
        self.group_url = kwargs.pop('group_url')
        super(IndividualGroupPostSpider, self).__init__(*args, **kwargs)

    def parse_home(self, response):
        # goes through the 'save device' part by not saving device
        if response.xpath("//div/a[contains(@href,'save-device')]"):
            self.logger.info('"save-device" checkpoint. redirecting...')
            return FormRequest.from_response(
                response,
                formdata={'name_action_selected': 'dont_save'},
                callback=self.parse_home
            )
        # if "don't save" is selected, go on to the group page
        msg = 'saved device. going to -- ' + self.group_url
        self.logger.info(msg)
        return scrapy.Request(
            url=self.group_url,
            callback=self.parse_group_info,
        )

    def parse_group_info(self, response):
        group_name = response.xpath(
            '//table/tbody/tr/td[2]/h1/div/text()').extract()[0]
        this_group_url = response.request.url
        if not FacebookGroup.objects.filter(name=group_name).exists():
            this_group = FacebookGroup(name=group_name, url=this_group_url)
            this_group.save()
        yield scrapy.Request(
            url=this_group_url, callback=self.parse_group, dont_filter=True,
        )
