# -*- coding: utf-8 -*-
import base64
from emailgrabber import CommonIGEmailParser


class BingAPI(CommonIGEmailParser):
    """
    Class for parsing of results of search
    """
    HOST = "https://api.datamarket.azure.com/Bing/SearchWeb/Web"

    def _collect_results_from_soup(self, soup):
        """
        Collect search results from soup
        :param soup:
        :return:
        """
        tags = soup.findAll("d:url")
        
        for tag in tags:
            yield tag.text

    def process(self, *args):
        """
        Get results by target from source
        :return:
        """
        params = {"Query": self.target}

        if not args or not args[0] or not args[0][0]:
            raise ValueError("Bing API key is required.")

        keys = "%s:%s" % (args[0][0], args[0][0])
        encoded = base64.b64encode(keys)
        self.headers.update({"Authorization": "Basic %s" % encoded})

        soup = self._get_soup(params=params)
        self._collect_results_from_soup(soup)

        skip = 0

        while True:
            skip += 50
            params["$skip"] = skip

            soup = self._get_soup(params=params)

            for result in self._collect_results_from_soup(soup):
                yield result

            if not soup.find("d:url"):
                break
