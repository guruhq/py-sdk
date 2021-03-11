
import guru


g = guru.Guru()

# this is the list of terms we're looking for.
# we'll list every card that contains at least one of these terms.
terms = [
  "test",
  "guru link",
  "intercom"
]

# this will check all cards you can see in guru.
# to check a single collection you can switch it to this:
# for card in g.find_cards(collection="General"):
for card in g.find_cards():
  # we keep track of which terms are found in this card and if we find any, we print the card's information.
  terms_found = []
  for term in terms:
    # we have options here for case-sensitivity (e.g. does "Guru" match "guru"?)
    # and whether we consider text in the card's title.
    # by default, calling has_text(term) will include the title and be case insensitive.
    if card.has_text(term, case_sensitive=False, include_title=True):
      terms_found.append(term)
  
  # if we found any terms, print the card's info.
  if terms_found:
    print("\t".join([
      card.collection.name,
      card.title,
      card.url,
      card.owner.email,
      ", ".join(terms)
    ]))
