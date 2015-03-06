import scrapy
from bs4 import BeautifulSoup

from wiki.items import WikiItem

class WikiSpider(scrapy.Spider):
    name = 'wiki'
    allowed_domains = ['wikipedia.org']
    start_urls = ['http://en.wikipedia.org/wiki/Category:Subfields_by_academic_discipline']

    def parse(self, response):
        soup = BeautifulSoup(response.body)
        item = WikiItem()
        if soup.title is None or soup.title.string is None: return
        if soup.title.string.split(':')[0] != 'Category':
            yield Request(url = response.url, dont_filter = True)
            return
        item['title'] = response.url.split(':')[-1]
        item['subcats'], item['pages'] = [], []
        sublinks = []
        for link in soup.find_all('a'):
            if link is not None and link.get('class') is not None:
                if 'CategoryTreeLabel' in link['class']:
                    if link.string is not None:
                        item['subcats'].append(link.string)
                    if link.get('href') is not None:
                        sublinks.append(link['href'])
        for div in soup.find_all('div'):
            if div.h2 is None or div.h2.contents is None or div.h2.contents[-1] is None or not div.h2.contents[-1].startswith('Pages in category'): continue
            for link in div.find_all('a'):
                if link.get('href') is None or link.string is None: continue
                if link['href'] == '/wiki/' + link.string.replace(' ', '_'):
                    item['pages'].append(link.string)
        yield item
        for sublink in sublinks:
            yield scrapy.Request(url = 'http://en.wikipedia.org' + sublink, callback = self.parse)
