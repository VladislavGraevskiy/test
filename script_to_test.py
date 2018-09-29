#!/usr/bin/env python3

import argparse
import os
import sys
from PIL import Image
from lxml import html
import requests
import time
from io import BytesIO
from multiprocessing.dummy import Pool as ThreadPool


class Parse:
    def __init__(self):
        self.keyword = ""
        self.image_size = []
        self.search_service = "duckduckgo.com/lite/?"
        self.links = []
        self.absolute_link = []
        self.count = 0

    def input_args_to_parse(self):
        a_parser = argparse.ArgumentParser(description="Search of images using the keyword")
        a_parser.add_argument('keyword', help='The keyword for search')
        a_parser.add_argument('width', help='Minimum width of the image', type=int)
        a_parser.add_argument('height', help='Minimum height of the image', type=int)
        args = a_parser.parse_args()
        self.keyword = str(args.keyword)
        self.image_size = [args.width, args.height]
        return a_parser.parse_args()

    def url_formation(self, keyword):
        return "https://{}q={}".format(
            self.search_service,
            "+".join(keyword.split("_"))
        )

    def image_download(self, img_url):
        try:
            img = Image.open(BytesIO(requests.get(img_url).content))
            if img.size[0] > int(self.image_size[0]) and img.size[1] > int(self.image_size[1]):
                self.count += 1
                img.save("{}/{}-{}-{}-{}.{}".format(
                    self.keyword,
                    img_url.split("/")[2],
                    self.keyword,
                    img.size[0],
                    img.size[1],
                    img.format)
                )
        except OSError:
            pass

    def parse(self, url_contents):
        self.links = url_contents.xpath("//a[@class='result-link']/@href")[:5]
        return self.links

    def image_search(self, url_contents):
        domain = list(url_contents.keys())[0]
        image_links = list(url_contents.values())[0].xpath("//img/@src")
        # create list with absolute link
        [self.absolute_link.append(requests.compat.urljoin(domain, link)) for link in image_links]
        return self.absolute_link

    @staticmethod
    def get_url_content(url, mode=1):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
        }
        # internet connection and site accessibility test
        try:
            requests.get(url, headers=headers)
        except requests.exceptions.ConnectionError:
            if mode:
                return None
            else:
                print("Oops. Please, check your internet connections")
                raise SystemExit
        page = requests.get(url, headers=headers)
        tree = html.fromstring(page.content)
        if mode:
            return {page.url: tree}
        else:
            return tree

    def folder_creations(self):
        try:
            os.mkdir(self.keyword)
        except FileExistsError:
            pass


class TimeChecker(object):
    def __enter__(self):
        self._startTime = time.time()

    def __exit__(self, type, value, traceback):
        print("Elapsed time: {:.3f} sec".format(time.time() - self._startTime))


def run():
    with TimeChecker() as t:
        parser = Parse()
        parser.input_args_to_parse()
        if not parser.parse(parser.get_url_content(parser.url_formation(parser.keyword), mode=0)):
            print("""References on your request is not found:(
            Try again:)""")
            raise SystemExit
        contents = list(map(parser.get_url_content, parser.links))
        clear_contents = [i for i in contents if i is not None]
        if not clear_contents:
            print("Try other keyword")
            raise SystemExit
        pool = ThreadPool(3)
        image_links = pool.map(parser.image_search, clear_contents)[0]
        print("Found {} images".format(len(image_links)))
        parser.folder_creations()
        pool = ThreadPool(10)
        pool.map(parser.image_download, image_links)
        print("The number of stored images: ", parser.count)
        pool.close()
        pool.join()


if __name__ == "__main__":
    req_version = (3, 2)
    cur_version = sys.version_info
    if cur_version >= req_version:
        run()
    else:
        print("Your Python interpreter is too old. "
              "Please consider upgrading. Your version {}".format(cur_version[:2]))
