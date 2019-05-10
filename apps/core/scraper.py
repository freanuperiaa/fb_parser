import scrapy
from scrapy import FormRequest

from .models import FacebookGroup, Post, Comment


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
            ).extract()[0],
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
        }
        reactions = self.facebook + response.xpath(
            '//a[contains(@href, "/ufi/reaction")]/@href').extract()[0]

        yield scrapy.Request(url=reactions, callback=self.parse_reactions, meta=post)

    def parse_reactions(self, response):
        self.logger.info('parse post info, including reacts')
        all_reacts = response.xpath('//a[contains(text(), "All")]/text()').extract()
        if all_reacts == []:
            all_reacts = ''
        else:
            all_reacts = all_reacts[0]
        likes = response.xpath(
            '//a[contains(@href, "ufi/reaction")]/img[@alt="Like"]/'
            'following-sibling::span/text()'
        ).extract()
        if likes == []:
            likes =''
        else:
            likes = likes[0]
        heart = response.xpath(
            '//a[contains(@href, "ufi/reaction")]/img[@alt="Love"]/'
            'following-sibling::span/text()'
        ).extract()
        if heart == []:
            heart =''
        else:
            heart = heart[0]
        wow = response.xpath(
            '//a[contains(@href, "ufi/reaction")]/img[@alt="Wow"]/'
            'following-sibling::span/text()'
        ).extract()
        if wow == []:
            wow =''
        else:
            wow = wow[0]
        haha = response.xpath(
            '//a[contains(@href, "ufi/reaction")]/img[@alt="Haha"]/'
            'following-sibling::span/text()'
        ).extract()
        if haha == []:
            haha =''
        else:
            haha = haha[0]
        sad = response.xpath(
            '//a[contains(@href, "ufi/reaction")]/img[@alt="Sad"]/'
            'following-sibling::span/text()'
        ).extract()
        if sad == []:
            sad = ''
        else:
            sad = sad[0]
        angry = response.xpath(
            '//a[contains(@href, "ufi/reaction")]/img[@alt="Angry"]/'
            'following-sibling::span/text()'
        ).extract()
        if angry == []:
            angry =''
        else:
            angry = angry[0]
        this_group = FacebookGroup.objects.get(name=response.meta.get('group'))
        title = response.meta.get('title')
        title = title[0]
        author = response.meta.get('author')
        author = author[0]
        new_post = Post(
            title=title, url=response.meta.get('post url'),
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
        title = response.xpath(
                '/html/body/div/div/div[2]/div/div[1]/div[1]/div/div[1]/div[3]'
                '/div[1]/div[1]/span[2]/text()'
        ).extract()
        title = title[0]
        author = response.xpath(
                '/html/body/div/div/div[2]/div/div[1]/div[1]/div/div[1]/div[1]'
                '/table/tbody/tr/td[2]/div/h3/span/strong[1]/a/text()'
            ).extract()
        author = author[0]
        this_post = Post.objects.get(title=title, author=author)
        comments = response.xpath(
            '//div[string-length(@class) = 2 and count(@id)=1 and contains'
            '("0123456789", substring(@id,1,1))]')
        # iterate through the comments div collected
        print(self.clean_url(response.request.url))
        for comment in comments:
            # author
            author = comment.xpath('./div/h3/a/text()').extract()
            print(author)
            # text
            text = comment.xpath('./div/div[1]/text()').extract()
            print(text)
            # time
            time = comment.xpath('./div/div[3]/abbr/text()').extract()
            print(time)
            # reacts
            reacts = comment.xpath('./div/div/span/span/a[1]/span/'
                                'following-sibling::text()').extract()
            if reacts == []:
                reacts = ''
            else:
                reacts = reacts[0]
            print(reacts)
            new_comment = Comment(
                author=author[0], text=text[0], time=time[0], no_reacts=reacts,
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

    def parse_group_info(self,response):
        group_name = response.xpath(
            '//table/tbody/tr/td[2]/h1/div/text()').extract()[0]
        this_group_url = response.request.url
        if not FacebookGroup.objects.filter(name=group_name).exists():
            this_group = FacebookGroup(name=group_name, url=this_group_url)
            this_group.save()
        yield scrapy.Request(
            url=this_group_url, callback=self.parse_group, dont_filter=True,
        )
