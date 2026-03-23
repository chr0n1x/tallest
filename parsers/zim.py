"""Parse ZIM index pages to extract source links."""

from html.parser import HTMLParser
import re
from urllib.parse import urljoin
import requests


class ZimIndexParser(HTMLParser):
    """Parse ZIM index HTML to extract links."""

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
    """Parse ZIM links from a URL."""
    if not url:
        raise ValueError("ZIM - no url given")
    try:
        resp = requests.get(url, timeout=10)
    except Exception as exc:
        raise RuntimeError(f"could not fetch from {url}") from exc
    parser = ZimIndexParser()
    if pattern:
        parser.pattern = re.compile(pattern)
    try:
        parser.feed(resp.text)
    except Exception as exc:
        raise RuntimeError(f"could not fetch from {url}") from exc
    return parser


def get_latest_source_link(url: str, pattern: str = None) -> tuple[str, str] | str:
    """Get the latest source link from a ZIM index.

    Returns:
        A tuple of (name, href) if a link is found, or an empty string if no links are found.
    """
    parser = parse_zim_links(url, pattern)
    if not parser.links:
        return ""
    name = max(parser.links.keys())
    href = parser.links[name]
    # some zim indices will have href of JUST file name; prepend the index URL
    if not href.startswith(("http://", "https://")):
        href = urljoin(url, href)
    return (name, href)
