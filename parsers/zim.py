from html.parser import HTMLParser
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ZimIndexParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: dict[str, str] = {}
        self.current_text: str = ""
        self.current_href: str = ""
        self.pattern = None

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag == "a":
            if self.current_text and self.pattern:
                if self.pattern.search(self.current_text):
                    self.links[self.current_text] = self.current_href
            elif self.current_text:
                self.links[self.current_text] = self.current_href
            self.current_text = ""
            self.current_href = ""
            for attr in attrs:
                if attr[0] == "href":
                    self.current_href = attr[1]
                    break

    def handle_data(self, data: str) -> None:
        self.current_text += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "a":
            if self.current_text and self.pattern:
                if self.pattern.search(self.current_text):
                    self.links[self.current_text] = self.current_href
            elif self.current_text:
                self.links[self.current_text] = self.current_href
            self.current_text = ""
            self.current_href = ""


def parse_zim_links(url: str, pattern: str = None) -> ZimIndexParser:
    if not url:
        logger.error("ZIM - no url given")
        return None
    try:
        resp = requests.get(url, timeout=10)
        logger.info(f"fetched links from {url}")
    except Exception:
        logger.error(f"could not fetch from {url}")
        return None
    parser = ZimIndexParser()
    if pattern:
        import re
        parser.pattern = re.compile(pattern)
    try:
        parser.feed(resp.text)
    except Exception:
        logger.error(f"could not fetch from {url}")
        return None
    return parser


def get_latest_source_link(url: str, pattern: str = None) -> str:
    parser = parse_zim_links(url, pattern)
    if not parser:
        return ""
    return parser.links[max(parser.links.keys())]
