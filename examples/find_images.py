
import guru

g = guru.Guru()

# scan all cards, find ones that contain images that are hosted by google.
for card in g.find_cards():
  google_image_count = len(card.doc.select("img[src*=google]"))

  if google_image_count > 0:
    print("\t".join([
      card.collection.name,
      card.title,
      card.url,
      card.verifier_label,
      card.owner.email,
      str(google_image_count)
    ]))
