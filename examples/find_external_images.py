import guru

g = guru.Guru()

# convert a string like "https://lh6.googleusercontent.com/something.png" to just "googleusercontent.com".
def get_image_domain(src):
  src = src.replace("http://", "").replace("https://", "")
  src = src.split("/")[0]
  return ".".join(src.split(".")[-2:])

# scan all cards, find ones that contain images that are hosted externally.
for card in g.find_cards():
  non_guru_domains = []
  for image in card.doc.select("img"):
    domain = get_image_domain(image.attrs["src"])
    if domain != "getguru.com":
      if domain not in non_guru_domains:
        non_guru_domains.append(domain)

  for domain in non_guru_domains:
    print("\t".join([
      card.collection.name,
      card.title,
      card.url,
      card.verifier_label,
      card.owner.email,
      domain
    ]))
