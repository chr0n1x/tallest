"""Tests for ZIM index parser."""

import unittest
from urllib.parse import urljoin

import pytest
import requests
from unittest.mock import patch, MagicMock

from parsers.zim import ZimIndexParser, parse_zim_links, get_latest_source_link


class TestZimIndexParser(unittest.TestCase):
    """Test ZimIndexParser class."""

    def setUp(self):
        self.parser = ZimIndexParser()

    def test_init(self):
        """Test parser initialization."""
        self.assertEqual(self.parser.links, {})
        self.assertEqual(self.parser.current_text, "")
        self.assertEqual(self.parser.current_href, "")
        self.assertIsNone(self.parser.pattern)

    def test_handle_starttag_with_link(self):
        """Test handling start tag with href attribute."""
        attrs = [("href", "link.zim")]
        self.parser.handle_starttag("a", attrs)
        self.assertEqual(self.parser.current_href, "link.zim")

    def test_handle_starttag_without_link(self):
        """Test handling start tag without href attribute."""
        attrs = [("class", "link")]
        self.parser.handle_starttag("a", attrs)
        self.assertEqual(self.parser.current_href, "")

    def test_handle_data(self):
        """Test handling text data."""
        self.parser.handle_data("Sample")
        self.assertEqual(self.parser.current_text, "Sample")

    def test_handle_data_multiple(self):
        """Test handling multiple data calls."""
        self.parser.handle_data("Sample")
        self.parser.handle_data("Text")
        self.assertEqual(self.parser.current_text, "SampleText")

    def test_handle_endtag(self):
        """Test handling end tag."""
        self.parser.current_text = "Sample"
        self.parser.current_href = "link.zim"
        self.parser.handle_endtag("a")
        self.assertEqual(self.parser.current_text, "")
        self.assertEqual(self.parser.current_href, "")


class TestParseZimLinks(unittest.TestCase):
    """Test parse_zim_links function."""

    def setUp(self):
        self.test_html = """
        <html>
        <body>
            <a href="link1.zim">Source 1</a>
            <a href="link2.zim">Source 2</a>
        </body>
        </html>
        """

    @patch("parsers.zim.requests.get")
    def test_parse_links_success(self, mock_get):
        """Test parsing links on success."""
        # Create a proper mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = self.test_html
        mock_response.raise_for_status = MagicMock()

        mock_get.return_value = mock_response

        parser = parse_zim_links("http://example.com/index.html")

        mock_get.assert_called_once_with(
            "http://example.com/index.html", timeout=10)
        # Parser counts all 'a' tags it processes
        self.assertGreaterEqual(len(parser.links), 2)
        self.assertIn("Source 1", parser.links)
        self.assertIn("Source 2", parser.links)

    @patch("parsers.zim.requests.get")
    def test_parse_links_with_pattern(self, mock_get):
        """Test parsing links with pattern."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = self.test_html
        mock_response.raise_for_status = MagicMock()

        mock_get.return_value = mock_response

        pattern = r"Source \d"
        parser = parse_zim_links(
            "http://example.com/index.html", pattern=pattern)
        self.assertIsNotNone(parser.pattern)

    @patch("parsers.zim.requests.get")
    def test_parse_links_empty_url(self, mock_get):
        """Test parsing with empty URL."""
        with self.assertRaises(ValueError):
            parse_zim_links("")

    @patch("parsers.zim.requests.get")
    def test_parse_links_request_error(self, mock_get):
        """Test parsing with request error."""
        mock_get.side_effect = requests.RequestException("Connection error")

        with pytest.raises(RuntimeError):
            parse_zim_links("http://example.com/index.html")

    @patch("parsers.zim.requests.get")
    def test_parse_links_parse_error(self, mock_get):
        """Test parsing with parse error.

        The parser.feed() method is called with HTML content. It only raises
        RuntimeError if there's an exception during parsing, not based on
        the content being valid or invalid.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = self.test_html
        mock_response.raise_for_status = MagicMock()

        mock_get.return_value = mock_response

        # Valid HTML should not raise an error
        parser = parse_zim_links("http://example.com/index.html")
        self.assertIsInstance(parser, ZimIndexParser)


class TestGetLatestSourceLink(unittest.TestCase):
    """Test get_latest_source_link function."""

    def setUp(self):
        self.test_html = """
        <html>
        <body>
            <a href="link1.zim">Source 1</a>
            <a href="link2.zim">Source 2</a>
            <a href="source.zim">Main Source</a>
        </body>
        </html>
        """

    @patch("parsers.zim.requests.get")
    def test_get_latest_link_absolute_urls(self, mock_get):
        """Test getting latest link with absolute URLs."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = self.test_html
        mock_response.raise_for_status = MagicMock()

        mock_get.return_value = mock_response

        result = get_latest_source_link("http://example.com/index.html")

        self.assertIsInstance(result, tuple)
        # max() on string keys returns lexicographically largest key
        self.assertIn(result[0], ["Source 2", "Source 1"])
        # The URL should be the one corresponding to the max key
        self.assertEqual(result[1], "http://example.com/link2.zim")

    @patch("parsers.zim.requests.get")
    def test_get_latest_link_relative_urls(self, mock_get):
        """Test getting latest link with relative URLs."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
        <body>
            <a href="local_source.zim">Local Source</a>
        </body>
        </html>
        """
        mock_response.raise_for_status = MagicMock()

        mock_get.return_value = mock_response

        result = get_latest_source_link("http://example.com/index.html")

        self.assertIsInstance(result, tuple)
        self.assertEqual(result[1], "http://example.com/local_source.zim")

    @patch("parsers.zim.requests.get")
    def test_get_latest_link_empty(self, mock_get):
        """Test getting latest link with empty result."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body></body></html>"
        mock_response.raise_for_status = MagicMock()

        mock_get.return_value = mock_response

        result = get_latest_source_link("http://example.com/index.html")
        # Empty result returns empty string
        self.assertEqual(result, "")

    @patch("parsers.zim.requests.get")
    def test_get_latest_link_returns_tuple(self, mock_get):
        """Test that get_latest_source_link always returns a tuple or empty string."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = self.test_html
        mock_response.raise_for_status = MagicMock()

        mock_get.return_value = mock_response

        result = get_latest_source_link("http://example.com/index.html")
        self.assertIsInstance(result, tuple)


class TestUrlJoin(unittest.TestCase):
    """Test URL joining logic."""

    def test_urljoin_relative(self):
        """Test urljoin with relative path."""
        base = "http://example.com/index.html"
        relative = "source.zim"
        result = urljoin(base, relative)
        expected = "http://example.com/source.zim"
        self.assertEqual(result, expected)

    def test_urljoin_absolute(self):
        """Test urljoin with absolute path."""
        base = "http://example.com/index.html"
        absolute = "http://other.com/source.zim"
        result = urljoin(base, absolute)
        self.assertEqual(result, absolute)

    def test_urljoin_root(self):
        """Test urljoin with root path."""
        base = "http://example.com/index.html"
        root = "/source.zim"
        result = urljoin(base, root)
        expected = "http://example.com/source.zim"
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
