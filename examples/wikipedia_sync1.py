
import guru

# these are the pages we'll download and import into guru.
# we'll end up with 6 cards on 1 board.
urls = [
  "https://en.wikipedia.org/wiki/Odessey_and_Oracle",
  "https://en.wikipedia.org/wiki/Pet_Sounds",
  "https://en.wikipedia.org/wiki/London_Calling",
  "https://en.wikipedia.org/wiki/24_Hour_Revenge_Therapy",
  "https://en.wikipedia.org/wiki/...And_Out_Come_the_Wolves",
  "https://en.wikipedia.org/wiki/Left_and_Leaving"
]

# the 'bundle' object helps us build out the set of .html and .yaml files
# that we use to upload content to guru. our code doesn't have to deal with
# the html/yaml files because that's all handled for us, but this doc has
# more information on the data format if you're interested:
# https://developer.getguru.com/docs/importing-a-zip-directory
g = guru.Guru()
bundle = g.bundle("favorite_albums")

# make a node called 'My Favorite Albums'. we'll add the other nodes as its
# children so it'll become a board in guru. we don't have to specify that a
# node will be a board or a card, the guru code will figure out this needs
# to be a board once we add nodes to it.
my_favorite_albums = bundle.node(id="albums", title="My Favorite Albums")

for url in urls:
  # download the page from wikipedia and extract the article's body and title
  # since that's the information we need to make a guru card.
  doc = bundle.load_html(url)
  body = doc.select(".mw-parser-output")[0]
  title = doc.find(id="firstHeading").text

  # remove elements we don't want in the guru card (the right column, footer links, etc.)
  for el in body.select(".ambox-content, .infobox, [role='navigation'], .wikitable.floatright, #toc, #toc ~ *, .shortdescription, .hatnote"):
    el.decompose()

  # make a node representing this article and add it to the 'My Favorite Albums' node.
  bundle.node(
    id=title,
    url=url,
    title=title,
    content=str(body)
  ).add_to(my_favorite_albums)

# zip() tells the guru code that we're done adding nodes.
# view_on_browser() opens a preview of the content that'll be imported into guru.
bundle.zip()
bundle.view_in_browser()

# uncommenting this will make it upload the content to guru.
# if the 'Favorite Albums' collection doesn't exist, it'll create it.
# bundle.upload(name="Favorite Albums", color=guru.CORNFLOWER, is_sync=True)
