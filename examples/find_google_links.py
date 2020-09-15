
import guru

g = guru.Guru()

# scan all cards, find ones that contain links to a google.com URL
# and print out the collection, card, and link URL for each.
for card in g.find_cards():
  for link in card.doc.select("a[href*=google.com]"):
    print(card.collection.name, card.id, card.title, link.attrs.get("href"))
