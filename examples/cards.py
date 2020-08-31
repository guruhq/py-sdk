
import guru

g = guru.Guru()

# this will load all cards you can see in guru.
for card in g.find_cards():
  # find all the iframes in this card and print the URLs.
  for iframe in card.doc.select("iframe"):
    print("%s\t%s\thttps://app.getguru.com/card/%s\t%s\t%s" % (
      card.collection.name,
      card.title,
      card.slug,
      card.owner.email,
      iframe.attrs.get("src")
    ))
