import scrapy
from scrapy import FormRequest


class IndividualPostSpider(scrapy.Spider):
    name = 'individual_post_spider'
    facebook = 'https://mbasic.facebook.com'
    individual_post = 'https://mbasic.facebook.com/story.php?story_fbid=10161791263965581&id=669230580&refid=46&ref=104&__xts__%5B0%5D=12.%7B%22unit_id_click_type%22%3A%22graph_search_results_item_tapped%22%2C%22click_type%22%3A%22result%22%2C%22module_id%22%3A3%2C%22result_id%22%3A%22669230580%3A10161791263965581%22%2C%22session_id%22%3A%226062ceebb8d55cc5ec433a902450d32a%22%2C%22module_role%22%3A%22PUBLIC_POSTS%22%2C%22unit_id%22%3A%22browse_rl%3A1c58046d-f2f3-c230-4452-cd1acd058c12%22%2C%22browse_result_type%22%3A%22browse_type_story%22%2C%22unit_id_result_id%22%3A10161791263965581%2C%22module_result_position%22%3A0%2C%22result_creation_time%22%3A1557032750%2C%22result_latest_edit_time%22%3A1557033267%7D&__tn__=%2AW#footer_action_list'
    start_urls = [facebook]

    def clean_url(self, url):
        url = url[:(url.find('?refid'))]
        url = url[:(url.find('&fref'))]
        url = url[:(url.find('%3Amf'))]
        return self.facebook + url[:(url.find('?fref'))]

    def parse(self, response):
        # prompt for username and password, then login
        email = input('enter email of fb account: ')
        password = input('enter password: ')
        return FormRequest.from_response(
            response,
            formxpath='//form[contains(@action, "login")]',
            formdata={
                'email': email, 'pass': password
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
            url=self.individual_post,
            callback=self.parse_indiv_posting
        )

    def parse_indiv_posting(self, response):
        # yield an item
        # or yield individual components of the posting
        reactions = self.facebook + response.xpath(
            '//a[contains(@href, "/ufi/reaction")]/@href').extract()[0]
        this_url = response.request.url
        yield scrapy.Request(
            url=reactions, callback=self.parse_reactions,
            meta={'this_url': this_url}
        )

    def parse_reactions(self, response):
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
        print('all reacts: ', all_reacts)
        print('likes:', likes, '\nheart: ', heart, '\nwow: ', wow, '\nhaha:',
              haha, '\nsad: ', sad, '\nangry: ', angry)
        go_back =response.meta.get('this_url')
        yield scrapy.Request(url=go_back, callback=self.parse_comments,
                             dont_filter=True)

    def parse_comments(self, response):
        '''
        I have two options here:
            first is to parse each comments on the post page, then parse the reply,
            OR
            get the 'reply' url for each comment on the post page, then go to it,
            then parse one by one the root comment and the reply....
            the commented-out block of code is the first option.
        '''
        # get the comments in the page
        comments = response.xpath(
            '//div[string-length(@class) = 2 and count(@id)=1 and contains'
            '("0123456789", substring(@id,1,1))]')
        # iterate through the comments div collected
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

            # !!!!!!!!!!!!!!!!!!!!!!!
            # reply URL, if it exists
            # print(comment.xpath('.//a[contains(@href,"repl")]/@href').extract())
            # ^this pertains to the page of a single comment, and its replies

        # link to replies (if there are replies)
        reply_url = comment.xpath(
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

    # def parse_replies(self, response):
    #     self.logger.info('replies...')
    #     print(response.request.url)
    #     print(response.meta.get('origin_post'))
    #     name = response.xpath(
    #         '//div[@id="viewport"]/div[@id="objects_container"]/div[@id="root"]'
    #         '/div/div[3]/div[string-length(@class) = 2 and contains("0123456789"'
    #         ', substring(@id,1,1))]/div/h3/a/text()'
    #     ).extract()
    #     text = response.xpath(
    #         '//div[@id="viewport"]/div[@id="objects_container"]/div[@id="root"]'
    #         '/div/div[3]/div[string-length(@class) = 2 and contains("0123456789"'
    #         ', substring(@id,1,1))]/div/div[1]/text()'
    #     ).extract()


    # TODO go to the block of commented code with'reply, if it exists', then try to
    #  go to every page of a comment and get info. URL for every comment works now,
    #  but I opt to put this project on django now.
