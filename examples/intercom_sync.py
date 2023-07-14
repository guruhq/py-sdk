"""
This script syncs articles from Intercom to Guru. For it to work, you'll need
to set up these environment variables:

INTERCOM_API_TOKEN, which is an intercom API token that has access to read articles.
GURU_API_USER, which is the email address of the account that'll be the author/owner of the cards in guru.
GURU_API_TOKEN, which is that user's API token.
"""

import os
import guru
import time
import requests

from bs4 import BeautifulSoup


INTERCOM_HEADERS = {
  "Authorization": "Bearer %s" % os.environ.get("INTERCOM_API_TOKEN")
}

def get_all(url):
  """
  Makes a get call and uses intercom's pagination info to make
  subsequent calls to load all results.
  """
  data = []
  while url:
    response = requests.get(url, headers=INTERCOM_HEADERS)

    # if we get an error response, we want to stop the whole sync.
    # if we did a partial sync it'd delete any unsynced cards.
    if response.status_code >= 400:
      print("got a %s response for %s" % (response.status_code, url))
      if response.status_code == 429:
        time.sleep(5)
        continue
      else:
        exit(1)

    data += response.json().get("data") or []
    page_info = response.json().get("pages") or {}
    url = page_info.get("next")
  return data

def get_intercom_collections():
  return get_all("https://api.intercom.io/help_center/collections")

def get_intercom_sections():
  return get_all("https://api.intercom.io/help_center/sections")

def get_intercom_articles():
  return get_all("https://api.intercom.io/articles")

def decode_entities(text):
  return BeautifulSoup(text, "lxml").text

def format_content(article):
  """
  This function takes an Intercom article and formats its content
  as the HTML we'll use for the Guru card. Because Intercom has some
  extra fields on its articles, like the # of views, conversations, and
  counts of user reactions and we don't have these fields in Guru, we
  display these values in the card's HTML.
  """
  url = "https://app.intercom.com/a/apps/%s/articles/articles/%s/show/stats?conversations=true" % (
    article.get("workspace_id"),
    article.get("id")
  )
  views_url = url + "&displaying=views"
  conversations_url = url + "&displaying=newchat"
  reactions_url = url + "&displaying=reacted"

  stats = article.get("statistics") or {}

  banner = """
    <hr />
    <p>
      <a target="_blank" rel="noopener noreferrer" href="%s">%s View%s</a>
      <a target="_blank" rel="noopener noreferrer" href="%s">%s Conversation%s</a>
      <a target="_blank" rel="noopener noreferrer" href="%s">%s Reaction%s</a>: 😃 %s%% &nbsp;😐 %s%% &nbsp;😞 %s%%</p>
  """ % (
    views_url,
    stats.get("views", 0),
    "" if stats.get("views") == 1 else "s",
    conversations_url,
    stats.get("conversations", 0),
    "" if stats.get("conversations") == 1 else "s",
    reactions_url,
    stats.get("reactions", 0),
    "" if stats.get("reactions") == 1 else "s",
    stats.get("happy_reaction_percentage", 0),
    stats.get("neutral_reaction_percentage", 0),
    stats.get("sad_reaction_percentage", 0)
  )
  return article.get("body") + banner


# this is where things actually start running.
g = guru.Guru(os.environ.get("GURU_API_USER"), os.environ.get("GURU_API_TOKEN"))
bundle = g.bundle("intercom")

# The grouping structures in Intercom are called Collections and Sections, which
# is a little confusing because those are also terms in Guru. We make a node for
# every Intercom Collection -- these will become Folders in Guru.
for collection in get_intercom_collections():
  bundle.node(
    id=collection.get("id"),
    title=decode_entities(collection.get("name"))
  )

# We make a node for every Intercom Section. These will coincidentally become
# Sections in Guru.
for section in get_intercom_sections():
  collection_node = bundle.node(id=section.get("parent_id"))
  bundle.node(
    id=section.get("id"),
    title=decode_entities(section.get("name"))
  ).add_to(collection_node)

# Make a node for every Intercom Article, these will become Cards in Guru.
for article in get_intercom_articles():
  # Intercom's article objects look like this:
  #   {
  #     'id': '4335012',
  #     'title': '',
  #     'body': '',
  #     'parent_id': None,
  #     'type': 'article',
  #     'workspace_id': 'a00805e22ea9cd915a183abbca34e890bb474886',
  #     'description': None,
  #     'author_id': 3435127,
  #     'state': 'draft',
  #     'created_at': 1597149380,
  #     'updated_at': 1597149380,
  #     'url': None,
  #     'parent_type': None,
  #     'statistics': {
  #       'type': 'article_statistics',
  #       'views': 0,
  #       'conversations': 0,
  #       'reactions': 0,
  #       'happy_reaction_percentage': 0,
  #       'neutral_reaction_percentage': 0,
  #       'sad_reaction_percentage': 0
  #    }
  #   },

  # if there's no content, skip it.
  if not article.get("body"):
    continue
  # only sync published articles.
  if article.get("state") != "published":
    continue

  article_node = bundle.node(
    id=article.get("id"),
    title=article.get("title") or "untitled",
    content=format_content(article), # article.get("body"),
    url=article.get("url")
  )

  # parent_id will either refer to a collection or section.
  parent_id = article.get("parent_id")
  if parent_id:
    bundle.node(id=parent_id).add_child(article_node)

def download_file(bundle, url, filename):
  if "api.getguru.com/files/" in url:
    # if the file is a pdf, the url here takes us to an HTML page that iframes the pdf.
    # doing this transform gives us a url that takes us to the actual file.
    # https://api.getguru.com/files/view/... -> https://content.api.getguru.com/files/gt/...
    url = url.replace("//api.getguru.com", "//content.api.getguru.com")
    url = url.replace("/files/view/", "/files/gt/")
    status_code, file_size = bundle.download_file(url, filename)
    return status_code

bundle.zip(
  # you can change this to favor_folders=True to make the sync create
  # folder groups with folders, rather than folders with sections, if
  # that's your preference.
  favor_sections=True,
  download_func=lambda url, filename, bundle, node: download_file(bundle, url, filename)
)

# to preview the content that'll be imported without actually loading it
# into guru, uncomment this line:
bundle.view_in_browser()

# running this will actually upload the content to guru as a sync.
# the first time this runs it'll create the collection. it's important
# that the collection doesn't already exist because it needs to be
# created as an 'external' collection and if you create the collection
# through our UI it's considered 'internal'.
# bundle.upload(name="Help Center (Intercom)", is_sync=True)
