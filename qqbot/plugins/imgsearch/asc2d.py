from typing import List, Tuple
import cloudscraper

from lxml.html import HTMLParser, fromstring
from pyquery import PyQuery


class Ascii2DItem:
    def __init__(self, data: PyQuery):
        self.origin: PyQuery = data  # 原始数据
        # 原图长宽，类型，大小
        self.hash: str = data("div.hash").eq(0).text()
        self.detail: str = data("small").eq(0).text()
        self.thumbnail: str = "https://ascii2d.net" + data("img").eq(0).attr("src")
        self.url: str = ""
        self.url_list: List[Tuple[str, str]] = []
        self.title: str = ""
        self.author: str = ""
        self.author_url: str = ""
        self._arrange(data)

    def _arrange(self, data: PyQuery) -> None:
        infos = data.find("div.detail-box.gray-link")
        if infos:
            links = infos.find("a")
            if links:
                mark = infos("small").eq(-1).text()
                self.url_list = [(i.attr("href"), i.text()) for i in links.items()]
                if len(list(links.items())) > 1 and mark in [
                    "pixiv",
                    "twitter",
                    "fanbox",
                    "fantia",
                    "ニコニコ静画",
                    "ニジエ",
                ]:
                    self.title = links.eq(0).text()
                    self.url = links.eq(0).attr("href")
                    self.author_url = links.eq(1).attr("href")
                    self.author = links.eq(1).text()
                elif links.eq(0).parents("small"):
                    infos.remove("small")
                    self.title = infos.text()
            if not self.title:
                external = infos.find("div.external")
                external.remove("a")
                self.title = external.text()

        self.url_list = list(
            map(
                lambda x: (f"https://ascii2d.net{x[0]}", x[1])
                if x[0].startswith("/")
                else x,
                self.url_list,
            )
        )

        if not self.url_list:
            links = data.find("div.pull-xs-right > a")
            if links:
                self.url = links.eq(0).attr("href")
                self.url_list = [(self.url, links.eq(0).text())]


class Ascii2DResponse:
    def __init__(self, resp_text: str):
        self.origin: str = resp_text  # 原始数据
        utf8_parser = HTMLParser(encoding="utf-8")
        data = PyQuery(fromstring(self.origin, parser=utf8_parser))
        # 结果返回值
        self.raw: List[Ascii2DItem] = [
            Ascii2DItem(i) for i in data.find("div.row.item-box").items()
        ]

def Ascii2DSearch(
        url: str = None, file: str|bytes|None = None
    ) -> Ascii2DResponse:
        """
        Ascii2D
        -----------
        Reverse image from https://ascii2d.net\n


        Return Attributes
        -----------
        • .origin = Raw data from scrapper\n
        • .raw = Simplified data from scrapper\n
        • .raw[0] = First index of simplified data that was found\n
        • .raw[0].title = First index of title that was found\n
        • .raw[0].url = First index of url source that was found\n
        • .raw[0].authors = First index of authors that was found\n
        • .raw[0].thumbnail = First index of url image that was found\n
        • .raw[0].detail = First index of details image that was found
        """
        client = cloudscraper.create_scraper()
        if url:
            ascii2d_url = "https://ascii2d.net/search/uri"
            resp = client.post(ascii2d_url, data={"uri": url})
        elif file:
            ascii2d_url = "https://ascii2d.net/search/file"
            data = (
                {"file": file}
                if isinstance(file, bytes)
                else {"file": open(file, "rb")}
            )
            resp = client.post(ascii2d_url, data=data)
        else:
            raise ValueError("url or file is required")

        return Ascii2DResponse(resp.text),Ascii2DResponse(client.get(resp.url.replace("/color/", "/bovw/")).text)