import scrapy
from bs4 import BeautifulSoup

from wiki.items import WikiItem

class WikiSpider(scrapy.Spider):
    name = 'wiki'
    allowed_domains = ['wikipedia.org']
    start_urls = ['http://en.wikipedia.org/wiki/Category:Subfields_by_academic_discipline',
    'http://en.wikipedia.org/wiki/Category:Algorithms_and_data_structures']

    def parse(self, response):
        soup = BeautifulSoup(response.body)
        item = WikiItem()
        if soup.title.string.split(':')[0] != 'Category':
            yield Request(url = response.url, dont_filter = True)
            return
        item['title'] = response.url.split(':')[-1]
        item['subcats'], item['pages'] = [], []
        sublinks = []
        for link in soup.find_all('a'):
            if link.get('class') is not None:
                if 'CategoryTreeLabel' in link['class']:
                    item['subcats'].append(link.string)
                    sublinks.append(link['href'])
        for div in soup.find_all('div'):
            if div.h2 is None or div.h2.contents[-1] is None or not div.h2.contents[-1].startswith('Pages in category'): continue
            for link in div.find_all('a'):
                if link['href'] == '/wiki/' + link.string.replace(' ', '_'):
                    item['pages'].append(link.string)
        yield item
        for sublink in sublinks:
            yield Request(url = 'http://en.wikipedia.org' + sublink)
