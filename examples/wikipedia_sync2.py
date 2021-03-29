
import guru

# this is like wikipedia_sync1 except there are two main differences:
# 1. this sync creates a deeper hierarchy so the resulting guru content has
#    a board group with two boards, and one of the boards contains sections.
# 2. we download images from wikipedia so the resulting guru cards have their
#    images hosted in guru, rather than referencing the external images.

def get_page(bundle, url, include_image=True):
  doc = bundle.load_html(url)

  # remove elements we don't want in the guru card (right column, footer links, etc.)
  body = doc.select(".mw-parser-output")[0]
  image = body.select(".infobox img")[0]
  image_tag = "<p><img src=\"%s\" /></p>" % image.attrs["src"] if image else ""

  for el in body.select(".ambox-content, .infobox, [role='navigation'], .wikitable.floatright, #toc, .shortdescription, .hatnote"):
    el.decompose()
  
  title = doc.find(id="firstHeading").text

  # make a node for this page and add it to the board.
  return bundle.node(
    id=title,
    url=url,
    title=title,
    content=image_tag + str(body)
  )

# this function is responsible for deciding if we should download an attachment
# and, if we should, it goes ahead and downloads it. if you're working with an
# external system that requires authentication, you may need to add a header to
# the download_file() call so it's able to access the file.
def download_file(url, filename, bundle, node):
  if "upload.wikimedia.org" in url:
    return bundle.download_file(url, filename)

# these are the urls of the pages we're going to download and turn into guru cards.
# the cards will be grouped by decade, so the decade labels become sections.
albums = {
  "60s": [
    "https://en.wikipedia.org/wiki/Odessey_and_Oracle",
    "https://en.wikipedia.org/wiki/Pet_Sounds",
  ],
  "70s-80s": [
    "https://en.wikipedia.org/wiki/London_Calling",
    "https://en.wikipedia.org/wiki/Graceland_(album)"
  ],
  "90s-2000s": [
    "https://en.wikipedia.org/wiki/24_Hour_Revenge_Therapy",
    "https://en.wikipedia.org/wiki/...And_Out_Come_the_Wolves",
    "https://en.wikipedia.org/wiki/Left_and_Leaving",
  ]
}

# these pages get added to a separate board that has no sections.
musicians = [
  "https://en.wikipedia.org/wiki/Joe_Strummer",
  "https://en.wikipedia.org/wiki/Paul_Simon",
  "https://en.wikipedia.org/wiki/Brian_Wilson"
]

g = guru.Guru()
bundle = g.bundle("favorite_stuff", verbose=True)

# make a node called 'My Favorite Albums', we'll add the other nodes
# as its children so it'll become a board in guru.
all_stuff = bundle.node(id="favorites", title="My Favorites")
albums_board = bundle.node(id="albums", title="Albums").add_to(all_stuff)
musicians_board = bundle.node(id="musicians", title="Musicians").add_to(all_stuff)

# for each url, make a new node with the page's title/content and add it to the board.
for era in sorted(albums.keys()):
  section = bundle.node(id=era, title=era).add_to(albums_board)

  for url in albums[era]:
    node = get_page(bundle, url)
    node.tags = [era, "album"]
    node.add_to(section)

for url in musicians:
  get_page(bundle, url).add_to(musicians_board)

bundle.zip(download_func=download_file)
bundle.view_in_browser()

# uncommenting this will make it upload the content to guru.
# bundle.upload(name="Favorite Albums", color=guru.CORNFLOWER, is_sync=True)
