# -*- coding: utf-8 -*-
from emailgrabber import CommonIGEmailParser


class Bing(CommonIGEmailParser):
    """
    Class for parsing of results of search
    """
    HOST = "http://www.bing.com"

    def _collect_results_from_soup(self, soup):
        """
        Collect search results from soup
        :param soup:
        :return:
        """
        tags = soup.findAll("div", attrs={"class": "b_title"})

        for tag in tags:
            a_tag = tag.a

            if not a_tag:
                continue

            yield tag.a.get("href")

    def _extract_next_link(self, soup):
        """
        Exctract next link
        :param soup:
        :return:
        """
        next_link = soup.find("a", attrs={"class": "sb_pagN"})
        return next_link

    def process(self, *args):
        """
        Get results by target from source
        :return:
        """
        path = "/search"
        params = {
            "q": self.target,
            "qs": "bs",
            "form": "QBRE"
        }

        soup = self._get_soup(path=path, params=params)
        self._collect_results_from_soup(soup)

        next_link = self._extract_next_link(soup)

        while next_link:
            next_url = next_link.get("href")

            soup = self._get_soup(path=next_url)

            for result in self._collect_results_from_soup(soup):
                yield result

            next_link = self._extract_next_link(soup)
