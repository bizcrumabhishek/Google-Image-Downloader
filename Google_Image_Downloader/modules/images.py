# -*- coding: utf-8 -*-
"""
Created on Wed May 25 16:41:18 2016

@author: ananab06
"""

from __future__ import unicode_literals
from unidecode import unidecode

from utils import get_browser_with_url,measure_time

from bs4 import BeautifulSoup
import urlparse
import sys  #provides information about constants, functions and methods
import requests
import shutil
import os
import threading
import Queue

IMAGE_FORMATS = ["bmp", "gif", "jpg", "png", "psd", "pspimage", "thm",
                 "tif", "yuv", "ai", "drw", "eps", "ps", "svg", "tiff",
                 "jpeg", "jif", "jfif", "jp2", "jpx", "j2k", "j2c", "fpx",
                 "pcd", "png", "pdf"]


class ImageType:
    NONE = None
    FACE = "face"
    PHOTO = "photo"
    CLIPART = "clipart"
    LINE_DRAWING = "lineart"


class SizeCategory:
    NONE = None
    ICON = "i"
    LARGE = "l"
    MEDIUM = "m"
    SMALL = "s"
    LARGER_THAN = "lt"
    EXACTLY = "ex"


class LargerThan:
    NONE = None
    QSVGA = "qsvga"  # 400 x 300
    VGA = "vga"     # 640 x 480
    SVGA = "svga"   # 800 x 600
    XGA = "xga"     # 1024 x 768
    MP_2 = "2mp"    # 2 MP (1600 x 1200)
    MP_4 = "4mp"    # 4 MP (2272 x 1704)
    MP_6 = "6mp"    # 6 MP (2816 x 2112)
    MP_8 = "8mp"    # 8 MP (3264 x 2448)
    MP_10 = "10mp"  # 10 MP (3648 x 2736)
    MP_12 = "12mp"  # 12 MP (4096 x 3072)
    MP_15 = "15mp"  # 15 MP (4480 x 3360)
    MP_20 = "20mp"  # 20 MP (5120 x 3840)
    MP_40 = "40mp"  # 40 MP (7216 x 5412)
    MP_70 = "70mp"  # 70 MP (9600 x 7200)


class ColorType:
    NONE = None
    COLOR = "color"
    BLACK_WHITE = "gray"
    SPECIFIC = "specific"


class License:
    NONE = None
    REUSE = "fc"
    REUSE_WITH_MOD = "fmc"
    REUSE_NON_COMMERCIAL = "f"
    REUSE_WITH_MOD_NON_COMMERCIAL = "fm"


class ImageOptions:

    """Allows passing options to filter a google images search."""

    def __init__(self):
        self.image_type = None
        self.size_category = None
        self.larger_than = None
        self.exact_width = None
        self.exact_height = None
        self.color_type = None
        self.color = None
        self.license = None

    def __repr__(self):
        return unidecode(self.__dict__)

    def get_tbs(self):
        tbs = None
        if self.image_type:
            tbs = self._add_to_tbs(tbs, "itp", self.image_type)
        if self.size_category and not (self.larger_than or (self.exact_width and self.exact_height)):
            tbs = self._add_to_tbs(tbs, "isz", self.size_category)
        if self.larger_than:
            tbs = self._add_to_tbs(tbs, "isz", SizeCategory.LARGER_THAN)
            tbs = self._add_to_tbs(tbs, "islt", self.larger_than)
        if self.exact_width and self.exact_height:
            tbs = self._add_to_tbs(tbs, "isz", SizeCategory.EXACTLY)
            tbs = self._add_to_tbs(tbs, "iszw", self.exact_width)
            tbs = self._add_to_tbs(tbs, "iszh", self.exact_height)
        if self.color_type and not self.color:
            tbs = self._add_to_tbs(tbs, "ic", self.color_type)
        if self.color:
            tbs = self._add_to_tbs(tbs, "ic", ColorType.SPECIFIC)
            tbs = self._add_to_tbs(tbs, "isc", self.color)
        if self.license:
            tbs = self._add_to_tbs(tbs, "sur", self.license)
        return tbs

    def _add_to_tbs(self, tbs, name, value):
        if tbs:
            return "%s,%s:%s" % (tbs, name, value)
        else:
            return "&tbs=%s:%s" % (name, value)


class ImageResult:

    """Represents a google image search result."""

    ROOT_FILENAME = "img"
    DEFAULT_FORMAT = "jpg"

    def __init__(self):
        self.name = None
        self.file_name = None
        self.link = None
        self.thumb = None
        self.thumb_width = None
        self.thumb_height = None
        self.width = None
        self.height = None
        self.filesize = None
        self.format = None
        self.domain = None
        self.page = None
        self.index = None
        self.site = None

    def __eq__(self, other):
        return self.link == other.link

    def __hash__(self):
        return id(self.link)

    def __repr__(self):
        string = "ImageResult(index={i}, page={p}, domain={d}, link={l})".format(
            i=str(self.index),
            p=str(self.page),
            d=unidecode(self.domain) if self.domain else None,
            l=unidecode(self.link) if self.link else None
        )
        return string
        
    def download(self, path="images"):
        """Download an image to a given path."""

        self._create_path(path)

        try:
            response = requests.get(self.link, stream=True)

            if "image" in response.headers['content-type']:
                path_filename = self._get_path_filename(path)
                with open(path_filename, 'wb') as output_file:
                    shutil.copyfileobj(response.raw, output_file)
            else:
                print "\r\rskiped! cached image"

            del response

        except Exception as inst:
            print self.link, "has failed:"
            print inst

    def _get_path_filename(self, path):
        
        path_filename = None

        if self.file_name:
            original_filename = self.file_name
            path_filename = os.path.join(path, original_filename)

        if not path_filename or os.path.isfile(path_filename):

            if self.format:
                file_format = self.format
            else:
                file_format = self.DEFAULT_FORMAT

            i = 1
            default_filename = self.ROOT_FILENAME + str(i) + "." + file_format
            path_filename = os.path.join(path, default_filename)
            while os.path.isfile(path_filename):
                i += 1
                default_filename = self.ROOT_FILENAME + str(i) + "." + \
                    file_format
                path_filename = os.path.join(path, default_filename)

        return path_filename

    def _create_path(self, path):
        """Create a path, if it doesn't exists."""

        if not os.path.isdir(path):
            os.mkdir(path)

def _parse_image_format(image_link):
    """Parse an image format from a download link.
    """
    parsed_format = image_link[image_link.rfind(".") + 1:]

    if parsed_format not in IMAGE_FORMATS:
        for image_format in IMAGE_FORMATS:
            if image_format in parsed_format:
                parsed_format = image_format
                break

    if parsed_format not in IMAGE_FORMATS:
        parsed_format = None

    return parsed_format


def _get_images_req_url(query, image_options=None, page=0,
                        per_page=20):
    query = query.strip().replace(":", "%3A").replace(
        "+", "%2B").replace("&", "%26").replace(" ", "+")

    url = "https://www.google.com.ar/search?q={}".format(query) + \
          "&es_sm=122&source=lnms" + \
          "&tbm=isch&sa=X&ei=DDdUVL-fE4SpNq-ngPgK&ved=0CAgQ_AUoAQ" + \
          "&biw=1024&bih=719&dpr=1.25"

    if image_options:
        tbs = image_options.get_tbs()
        if tbs:
            url = url + tbs

    return url


def _find_divs_with_images(soup):

    try:
        div_container = soup.find("div", {"id": "rg_s"})
        divs = div_container.find_all("div", {"class": "rg_di"})
    except:
        divs = None
    return divs


def _get_file_name(link):

    temp_name = link.rsplit('/', 1)[-1]
    image_format = _parse_image_format(link)

    if image_format and temp_name.rsplit(".", 1)[-1] != image_format:
        file_name = temp_name.rsplit(".", 1)[0] + "." + image_format

    else:
        file_name = temp_name

    return file_name


def _get_name():
    pass


def _get_filesize():
    pass


def _get_image_data(res, a): 
    """Parse image data and write it to an ImageResult object.

    Args:
        res: An ImageResult object.
        a: An "a" html tag.
    """
    google_middle_link = a["href"]
    url_parsed = urlparse.urlparse(google_middle_link)
    qry_parsed = urlparse.parse_qs(url_parsed.query)
    res.name = _get_name()
    res.link = qry_parsed["imgurl"][0]
    res.file_name = _get_file_name(res.link)
    res.format = _parse_image_format(res.link)
    res.width = qry_parsed["w"][0]
    res.height = qry_parsed["h"][0]
    res.site = qry_parsed["imgrefurl"][0]
    res.domain = urlparse.urlparse(res.site).netloc
    res.filesize = _get_filesize()


def _get_thumb_data(res, img):
    """Parse thumb data and write it to an ImageResult object.

    Args:
        res: An ImageResult object.
        a: An "a" html tag.
    """
    try:
        res.thumb = img[0]["src"]
    except:
        res.thumb = img[0]["data-src"]

    try:
        img_style = img[0]["style"].split(";")
        img_style_dict = {i.split(":")[0]: i.split(":")[-1] for i in img_style}
        res.thumb_width = img_style_dict["width"]
        res.thumb_height = img_style_dict["height"]
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print exc_type, exc_value, "index=", res.index



def search(query, image_options=None, num_images=20):  #we can set how many image we want to search
    """Search images in google.

    Search images in google filtering by image type, size category, resolution,
    exact width, exact height, color type or color. A simple search can be
    performed without passing options. To filter the search, an ImageOptions
    must be built with the different filter categories and passed.

    Args:
        query: string to search in google images
        image_options: an ImageOptions object to filter the search
        num_images: number of images to be scraped

    Returns:
        A list of ImageResult objects
    """

    results = set()
    curr_num_img = 1
    page = 0
    browser = get_browser_with_url("")
    while curr_num_img <= num_images:

        page += 1
        url = _get_images_req_url(query, image_options, page)
        browser.get(url)
        html = browser.page_source

        if html:
            soup = BeautifulSoup(html,"html.parser")
            divs = _find_divs_with_images(soup)
            if not divs:
                break

            for div in divs:
                res = ImageResult()
                res.page = page
                res.index = curr_num_img
                a = div.find("a")
                if a:
                    _get_image_data(res, a)
                img = a.find_all("img")
                if img:
                    _get_thumb_data(res, img)

                prev_num_results = len(results)
                results.add(res)
                curr_num_results = len(results)

                if curr_num_results > prev_num_results:
                    curr_num_img += 1

                if curr_num_img >= num_images:
                    break

    browser.quit()

    return list(results)
    
def _download_image(image_result, path):

    if image_result.format:
        if path:
            image_result.download(path)
        else:
            image_result.download()


@measure_time
def download(image_results, path=None):
    """Download a list of images.

    Args:
        images_list: a list of ImageResult instances
        path: path to store downloaded images.
    """

    total_images = len(image_results)
    i = 1
    for image_result in image_results:

        progress = "".join(["Downloading image ", str(i),
                            " (", str(total_images), ")"])
        print progress
        sys.stdout.flush()

        _download_image(image_result, path)

        i += 1


class ThreadUrl(threading.Thread):

    def __init__(self, queue, path, total):
        threading.Thread.__init__(self)
        self.queue = queue
        self.path = path
        self.total = total

    def run(self):
        while True:
            image_result = self.queue.get()

            counter = self.total - self.queue.qsize()
            progress = "".join(["Downloading image ", str(counter),
                                " (", str(self.total), ")"])
            print progress
            sys.stdout.flush()
            _download_image(image_result, self.path)

            self.queue.task_done()


@measure_time
def fast_download(image_results, path=None, threads=10):
    queue = Queue.Queue()
    total = len(image_results)

    for image_result in image_results:
        queue.put(image_result)

    for i in range(threads):
        t = ThreadUrl(queue, path, total)
        t.setDaemon(True)
        t.start()

    queue.join()