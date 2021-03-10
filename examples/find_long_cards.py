
import guru

g = guru.Guru()

for card in g.find_cards():
  # we can measure card length a few ways:
  html_size = len(card.content)               # 1. the size of its HTML, including the HTML tags.
  text_size = len(card.doc.text)              # 2. the size of its visible text.
  word_count = len(card.doc.text.split(" "))  # 3. the number of words in its text.

  print("\t".join([
    card.collection.name,
    card.title,
    card.url,
    card.verifier_label,
    card.owner.email,
    str(html_size),
    str(text_size),
    str(word_count),
  ]))
