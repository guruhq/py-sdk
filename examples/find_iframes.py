
import guru
import html

from bs4 import BeautifulSoup

g = guru.Guru()

def print_iframe_info(card, iframe_url):
  print("%s\t%s\t%s\t%s\t%s" % (
    card.collection.name,
    card.title,
    card.url,
    card.owner.email,
    iframe_url
  ))

# this will check all cards you can see in guru.
for card in g.find_cards():
  # find all the links in this card and print the URLs.
  for iframe in card.doc.select("iframe"):
    print_iframe_info(card, iframe.attrs.get("src"))
  
  # look for iframes in markdown blocks.
  for markdown_div in card.doc.select("[data-ghq-card-content-markdown-content]"):
    markdown = markdown_div.attrs.get("data-ghq-card-content-markdown-content")
    doc = BeautifulSoup(html.unescape(markdown), "html.parser")

    for iframe in doc.select("iframe"):
      print_iframe_info(card, iframe.attrs.get("src"))
