
import guru

def get_page(url, include_image=True):
  doc = guru.load_html(url)

  # remove elements we don't want in the guru card (right column, footer links, etc.)
  body = doc.select(".mw-parser-output")[0]
  image = body.select(".infobox img")[0]
  image_tag = "<p><img src=\"%s\" /></p>" % image.attrs["src"] if image else ""

  for el in body.select(".ambox-content, .infobox, [role='navigation'], .wikitable.floatright, #toc, #toc ~ *, .shortdescription, .hatnote"):
    el.decompose()
  
  title = doc.find(id="firstHeading").text

  # make a node for this page and add it to the board.
  return sync.node(
    id=title,
    url=url,
    title=title,
    content=image_tag + str(body)
  )

def download_file(url, filename):
  if "upload.wikimedia.org" in url:
    return guru.download_file(url, filename)

# these are the urls of the pages we're going to download
# and turn into guru cards.
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

musicians = [
  "https://en.wikipedia.org/wiki/Joe_Strummer",
  "https://en.wikipedia.org/wiki/Paul_Simon",
  "https://en.wikipedia.org/wiki/Brian_Wilson"
]

g = guru.Guru()
sync = g.sync("favorite_stuff", verbose=True)

# make a node called 'My Favorite Albums', we'll add the other nodes
# as its children so it'll become a board in guru.
all_stuff = sync.node(id="favorites", title="My Favorites")
albums_board = sync.node(id="albums", title="Albums").add_to(all_stuff)
musicians_board = sync.node(id="musicians", title="Musicians").add_to(all_stuff)

# for each url, make a new node with the page's title/content and add it to the board.
for era in sorted(albums.keys()):
  section = sync.node(id=era, title=era).add_to(albums_board)

  for url in albums[era]:
    node = get_page(url)
    node.tags = [era, "album"]
    node.add_to(section)

for url in musicians:
  get_page(url).add_to(musicians_board)

sync.zip(download_func=download_file)
sync.print_tree()
sync.view_in_browser()
# uncommenting this will make it upload the content to guru.
# sync.upload(name="Favorite Albums", color=guru.CORNFLOWER, is_sync=True)
