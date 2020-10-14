
import guru

g = guru.Guru()

# scan all cards, find ones that contain links to a google.com URL
# and print out the collection, card, and link URL for each.
for card in g.find_cards():
  for link_or_iframe in card.doc.select("a[href*=google.com], iframe[src*=google.com]"):
    url = link_or_iframe.attrs.get("href") or link_or_iframe.attrs.get("src")
    print(card.collection.name, card.title, card.url, url)
