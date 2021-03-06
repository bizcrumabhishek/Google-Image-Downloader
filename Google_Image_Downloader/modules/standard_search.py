# -*- coding: utf-8 -*-
"""
Created on Wed May 25 16:41:18 2016

@author: ananab06
"""

from __future__ import unicode_literals

from utils import _get_search_url, get_html
from bs4 import BeautifulSoup
import urlparse
from urllib2 import unquote
from unidecode import unidecode
from re import match


class GoogleResult:

    """Represents a google search result."""

    def __init__(self):
        self.name = None
        self.link = None
        self.google_link = None
        self.description = None
        self.thumb = None
        self.cached = None
        self.page = None
        self.index = None
        
    def __repr__(self):
        name = self._limit_str_size(self.name, 55)
        description = self._limit_str_size(self.description, 49)

        list_google = ["GoogleResult(",
                       "name={}".format(name), "\n", " " * 13,
                       "description={}".format(description)]

        return "".join(list_google)

    def _limit_str_size(self, str_element, size_limit):
        
        if not str_element:
            return None

        elif len(str_element) > size_limit:
            return unidecode(str_element[:size_limit]) + ".."

        else:
            return unidecode(str_element)


def search(query, pages=1, lang='en', void=True):
    """Returns a list of GoogleResult.

    Args:
        query: String to search in google.
        pages: Number of pages where results must be taken.

    Returns:
        A GoogleResult object."""

    results = []
    for i in range(pages):
        url = _get_search_url(query, i, lang=lang)
        html = get_html(url)

        if html:
            soup = BeautifulSoup(html, "html.parser")
            divs = soup.findAll("div", attrs={"class": "g"})

            j = 0
            for li in divs:
                res = GoogleResult()

                res.page = i
                res.index = j

                res.name = _get_name(li)
                res.link = _get_link(li)
                res.google_link = _get_google_link(li)
                res.description = _get_description(li)
                res.thumb = _get_thumb()
                res.cached = _get_cached(li)
                if void is True:
                    if res.description is None:
                        continue
                results.append(res)
                j += 1

    return results

def _get_name(li):
    """Return the name of a google search."""
    a = li.find("a")
    if a is not None:
        return a.text.strip()
    return None


def _get_link(li):
    """Return external link from a search."""
    try:
        a = li.find("a")
        link = a["href"]
    except:
        return None

    if link.startswith("/url?"):
        m = match('/url\?(url|q)=(.+?)&', link)
        if m and len(m.groups()) == 2:
            return unquote(m.group(2))

    return None


def _get_google_link(li):
    """Return google link from a search."""
    try:
        a = li.find("a")
        link = a["href"]
    except:
        return None

    if link.startswith("/url?") or link.startswith("/search?"):
        return urlparse.urljoin("http://www.google.com", link)

    else:
        return None


def _get_description(li):
    """Return the description of a google search."""

    sdiv = li.find("div", attrs={"class": "s"})
    if sdiv:
        stspan = sdiv.find("span", attrs={"class": "st"})
        if stspan is not None:
            return stspan.text.strip()
    else:
        return None


def _get_thumb():
    """Return the link to a thumbnail of the website."""
    pass


def _get_cached(li):
    """Return a link to the cached version of the page."""
    links = li.find_all("a")
    if len(links) > 1 and links[1].text == "Cached":
        link = links[1]["href"]
        if link.startswith("/url?") or link.startswith("/search?"):
            return urlparse.urljoin("http://www.google.com", link)
    return None