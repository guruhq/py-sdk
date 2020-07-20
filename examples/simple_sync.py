
import guru
import json

def save_json(filename, data):
  with open(filename, "w") as file_out:
    file_out.write(json.dumps(data))

def load_json(filename):
  try:
    with open(filename, "r") as file_in:
      return json.loads(file_in.read())
  except:
    return {}

def load_wikipedia_page(url):
  doc = guru.load_html(url)
  body = doc.select(".mw-parser-output")[0]
  title = doc.find(id="firstHeading").text

  # remove elements we don't want in the guru card (the right column, footer links, etc.)
  for el in body.select(".ambox-content, .infobox, [role='navigation'], .wikitable.floatright, #toc, #toc ~ *, .shortdescription, .hatnote"):
    el.decompose()
  
  return title, str(body).replace("\\n", "\n").replace("\\'", "'")


urls = [
  "https://en.wikipedia.org/wiki/Odessey_and_Oracle",
  "https://en.wikipedia.org/wiki/Pet_Sounds",
  "https://en.wikipedia.org/wiki/London_Calling"
]

g = guru.Guru()

# this maps URLs to Guru Card IDs.
# we remember these values as we create cards so when we sync a url again,
# we can find which guru card needs to be updated.
guru_id_lookup = load_json("guru_id_lookup.json")

for url in urls:
  # if we have a guru ID for this page, that means we're updating an existing card.
  if url in guru_id_lookup:
    card = g.get_card(guru_id_lookup[url])
    card.title, card.content = load_wikipedia_page(url)
    card.save()
  else:
    # otherwise it means we're making a new card.
    title, content = load_wikipedia_page(url)
    card = g.make_card(title, content, "General")
    card.save()
    guru_id_lookup[url] = card.id

save_json("guru_id_lookup.json", guru_id_lookup)