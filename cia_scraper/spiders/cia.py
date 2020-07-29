import scrapy
# XPath

# links = '//a[contains(@href, "collection") and (parent::h3 | parent::h2)]/@href'
# title = '//h1[@class="documentFirstHeading"]/text()'
# date =  '//a[contains(@href, "collection") and (parent::h3 | parent::h2)]/parent::node()/following-sibling::*[1]/text()'
# body = '//div[@class="field-item even"]//p/text()'
# pdf_page_title = '//h4[@class="field-content"]/a/text()'
# pdf_page_link = '//h4[@class="field-content"]/a[contains(@href,"document")]/@href'
# pdf_file = '//span[@class="file"]//a[contains(.,"pdf")]/@href'


class SpiderCIA(scrapy.Spider):
    name = 'cia'
    start_urls = [
        'https://www.cia.gov/library/readingroom/historical-collections',
    ]

    custom_settings = {
        'FEED_URI': 'cia.json',
        'FEED_FORMAT': 'json',
        'FEED_EXPORT_ENCODING': 'utf-8',
        'CONCURRENT_REQUESTS': 200,
    }

    def parse(self, response):
        """Function that extracts all the data from the responses."""
        links_declassified_xpath = response.xpath(
            '//a[contains(@href, "collection") and (parent::h3 | parent::h2)]')
        links_declassified = []
        dates = []
        for i, l in enumerate(links_declassified_xpath):
            link = l.xpath('@href').get()
            date = l.xpath(
                'node()/../.././following-sibling::*[1]/text()|node()/../.././following-sibling::*[1]/i/text()').get()
            links_declassified.append(link)
            dates.append(date)
            print(f'* {i}. ', link)
            print('\t----', date)

        for link, date in zip(links_declassified, dates):
            print(f'---- {date}, {link}\n')
            yield response.follow(link, callback=self.parse_link,
                                  cb_kwargs={'url': response.urljoin(link), 'date': date})

    def parse_link(self, response, **kwargs):
        """
        This methods extracts the title and 
        the description of the declassified file
        """
        link = kwargs['url']
        date = kwargs['date']

        if kwargs:
            try:
                if kwargs['pdf_links']:
                    title = kwargs['title']
                    date = kwargs['date']
                    paragraphs = kwargs['body']
                    pdf_links = kwargs['pdf_links']
                    pdf_links.extend(response.xpath(
                        '//span[@class="file"]/a/@href').getall())
                    dict_data = {
                        'url': link, 'title': title, 'date': date,
                        'body': paragraphs, 'pdf_links': pdf_links,
                    }
                    yield self.analazyng_page(response, **dict_data)

            except:
                # Extracting for first time
                # Append new ones
                title = response.xpath(
                    '//h1[@class="documentFirstHeading"]/text()').get()
                paragraphs = ''.join(response.xpath(
                    '//div[@class="field-item even"]//p/text()').getall())

                # PDF Link extraction
                pdf_links = response.xpath(
                    '//span[@class="file"]/a/@href').getall()

                dict_data = {
                    'url': link, 'title': title, 'date': date,
                    'body': paragraphs, 'pdf_links': pdf_links,
                }

                yield self.analazyng_page(response, **dict_data)

    def analazyng_page(self, response, **kwargs):
        """This function analyze the page searching for more PDF links"""

        title = kwargs['title']
        date = kwargs['date']
        paragraphs = kwargs['body']
        pdf_links = kwargs['pdf_links']
        pdf_links.extend(response.xpath(
            '//span[@class="file"]/a/@href').getall())
        link = kwargs['url']

        next_page_button_link = response.xpath(
            '//li[@class="pager-next"]/a/@href').get()
        if next_page_button_link:
            return response.follow(next_page_button_link,
                                   callback=self.parse_link,
                                   cb_kwargs={
                                       'url': link, 'title': title,
                                       'date': date, 'body': paragraphs,
                                       'pdf_links': list(set(pdf_links)), })
        else:
            return {
                'url': link, 'title': title, 'date': date,
                'body': paragraphs,
                'pdf_links': list(set(pdf_links)),
            }
