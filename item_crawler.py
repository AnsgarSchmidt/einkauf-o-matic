# -*- coding: utf-8 -*-
"""
c-base einkauf-o-matic

@author: Ricardo (XenGi) Band <me@xengi.de>

    This file is part of einkauf-o-matic.

    einkauf-o-matic is licensed under Attribution-NonCommercial-ShareAlike 3.0
    Unported (CC BY-NC-SA 3.0).

    <http://creativecommons.org/licenses/by-nc-sa/3.0/>
"""
import urllib
from urlparse import urlparse
from bs4 import BeautifulSoup


class ItemCrawler():
    """
    gets a url and invokes the correct function for the specified store
    """

    def __init__(self):
        """
        initialize with a list of supported stores
        """
        self.stores = {'adafruit.com': self.item_info_adafruit,
                       'www.adafruit.com': self.item_info_adafruit}

    def get_item(self, url, count=1):
        """
        get the url of the store and start the corresponding function,
        to crawl item data
        """
        urlparts = urlparse(url)
        #ParseResult(scheme='http', netloc='www.cwi.nl:80',
        #            path='/%7Eguido/Python.html', params='', query='',
        #            fragment='')
        if urlparts.netloc == '':
            pass

        return self.stores[urlparts.netloc.split(':')[0]](url, count)

    def item_info_adafruit(self, url, count):
        """
        generate a dict with all infos about the given product
        """
        connection = urllib.urlopen(url)
        html = connection.read()
        connection.close()
        soup = BeautifulSoup(html)

        # item id
        item_id = soup.find(id='productTop').get_text().split('ID: ')[1].split('\n')[0]
        #item name
        item_name = soup.find(id='productName').get_text().strip(' \t\n\r')
        # item image
        for img in soup.findAll('img'):
            if '/images/medium/' in img['src']:
                item_image_url = 'http://www.adafruit.com' + img['src']
                break
        # item availability
        avail = soup.findAll('div', {"class": "availability"})[0].get_text().strip(' \t\n\r')
        if 'IN STOCK' in avail:
            item_availability = avail
        elif 'We expect to have these in stock in about 5 to 10 business days.' in avail:
            item_availability = 'back in 5 to 10 days'
        else:
            item_availability = 'Not available'
        # item price
        #TODO: add discount
        item_price = float(soup.find(id='productPrices').get_text().strip('$ \t\n\r'))
        return dict(id=int(item_id),
                        url=url, name=item_name,
                        image_url=item_image_url,
                        price=item_price,
                        availability=item_availability)


if __name__ == '__main__':
    # only for testing
    crawler = ItemCrawler()
    print crawler.get_item('http://www.adafruit.com/products/1053')