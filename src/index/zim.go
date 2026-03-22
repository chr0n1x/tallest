package main

import (
	"fmt"
	"io"
	"net/http"
	"strings"

	html "golang.org/x/net/html"
)

type Zim struct {
	URL string
}

func (z *Zim) ParseIndex() []string {
	if z.URL == "" {
		return []string{}
	}

	resp, err := http.Get(z.URL)
	if err != nil {
		return []string{}
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return []string{}
	}

	return z.parseHTML(string(body))
}

func (z *Zim) parseHTML(html string) []string {
	doc, err := html.Parse(strings.NewReader(html))
	if err != nil {
		return []string{}
	}

	var links []string
	var collectLinks func(*html.Node)
	collectLinks = func(n *html.Node) {
		if n.Type == html.ElementNode && n.Data == "pre" {
			var found bool
			for c := n.FirstChild; c != nil; c = c.NextSibling {
				if c.Type == html.ElementNode && c.Data == "a" {
					if found {
						continue
					}
					found = true
					var href string
					for _, attr := range c.Attr {
						if attr.Key == "href" {
							href = attr.Val
						}
					}
					if next := c.NextSibling; next != nil && next.Type == html.TextNode {
						text := strings.TrimSpace(next.Data)
						links = append(links, fmt.Sprintf("%s\t%s", href, text))
					}
				}
			}
		}
		for c := n.FirstChild; c != nil; c = c.NextSibling {
			collectLinks(c)
		}
	}
	collectLinks(doc)

	return links
}
