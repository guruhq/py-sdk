
import guru

g = guru.Guru()

# this will load all cards you can see in guru.
cards = g.find_cards()

for card in cards:
  # find all the links in this card and print the URLs.
  for link in card.doc.select("a"):
    print(link.attrs.get("href"))
