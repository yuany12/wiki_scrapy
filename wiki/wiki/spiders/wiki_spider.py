import scrapy
from bs4 import BeautifulSoup

from wiki.items import WikiItem

class WikiSpider(scrapy.Spider):
    name = 'wiki'
    allowed_domains = ['wikipedia.org']
    start_urls = ['http://en.wikipedia.org/wiki/Category:Areas_of_computer_science',
    'http://en.wikipedia.org/wiki/Category:Engineering_disciplines']

    def check(self, s):
        inputs = s.split()
        if inputs[0].isupper(): return False
        if any(inputs[i][0].isupper() for i in range(1, len(inputs))): return False
        if any(char.isdigit() for char in s): return False
        return True

    def parse(self, response):
        soup = BeautifulSoup(response.body)
        item = WikiItem()
        if soup.title is None or soup.title.string is None: return
        if soup.title.string.split(':')[0] != 'Category':
            yield Request(url = response.url, dont_filter = True)
            return
        item['title'] = response.url.split(':')[-1].replace('_', ' ')
        item['subcats'], item['pages'] = [], []
        sublinks = []
        for link in soup.find_all('a'):
            if link is not None and link.get('class') is not None:
                if 'CategoryTreeLabel' in link['class']:
                    if link.string is not None:
                        if self.check(link.string):
                            item['subcats'].append(link.string)
                            if link.get('href') is not None:
                                sublinks.append(link['href'])
        for div in soup.find_all('div'):
            try:
                flag = div.h2.contents[-1].startswith('Pages in category')
            except:
                flag = False
            if not flag: continue
            for link in div.find_all('a'):
                if link.get('href') is None or link.string is None: continue
                if link['href'] == '/wiki/' + link.string.replace(' ', '_'):
                    item['pages'].append(link.string)
        yield item
        for sublink in sublinks:
            yield scrapy.Request(url = 'http://en.wikipedia.org' + sublink, callback = self.parse)
