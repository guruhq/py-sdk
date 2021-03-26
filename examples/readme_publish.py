"""
This script shows how to use Guru's SDK to publish cards,
boards, or entire collections to an external site, like a
third-party help site.

This is the script we use to publish our docs from Guru to
https://developer.getguru.com/docs

This script takes the contents of a board in Guru and makes
API calls to Readme (https://readme.com/) to create or update
docs in Readme based on the changes seen in Guru. There are
a few parts to this:

1. Behind the scenes, the SDK enumerates all the sections
   and cards on the board we specify.
2. The SDK also writes a metadata .json file to keep track
   of which cards have been published before.
3. Using the metadata, the SDK knows whether a card has been
   published before and needs to be updated in Readme or is
   a brand new card and we need to create a doc in Readme.

The SDK orchestrates everything and this file just neesd to
implement methods that call Readme's API to do specific tasks.
When the SDK sees a card that's never been published before,
it'll call create_external_card and we need to implement how
the API call to Readme is made to create the doc in Readme.
"""

import os
import guru
import requests

from urllib.parse import unquote

GURU_USER = os.environ.get("GURU_USER")
GURU_API_TOKEN = os.environ.get("GURU_API_TOKEN")
README_API_TOKEN = os.environ.get("README_API_TOKEN")

def get_card_content(card):
  """
  Readme uses Markdown for its articles so the Guru cards
  we write contain a single markdown block. This function
  extracts the Markdown code from that block.
  """
  markdown_div = card.doc.select("[data-ghq-card-content-markdown-content]")
  if markdown_div:
    markdown_div = markdown_div[0]
    return unquote(markdown_div.attrs.get("data-ghq-card-content-markdown-content"))
  else:
    print("The card %s does not have any markdown blocks. Cards we sync to readme have to be written as a single markdown block" % card.title)
    return ""


class ReadmePublisher(guru.Publisher):
  def get_external_url(self, external_id, card):
    return "https://developer.getguru.com/docs/%s" % external_id

  def find_external_section(self, section):
    """
    This checks if a section already exists in Readme by checking for a 'category'
    with the same title.
    """
    url = "https://dash.readme.io/api/v1/categories?perPage=100"
    categories = requests.get(url, auth=(README_API_TOKEN, "")).json()

    for category in categories:
      if category["title"].lower() == section.title.lower():
        return category["_id"]

  def create_external_section(self, section, board, board_group, collection):
    # When we add a new section to our board, this method will
    # be called to create the section in Readme. We don't have
    # to do anything here, it just meanas that new sections won't
    # automatically get created in Readme.
    pass

  def update_external_section(self, external_id, section, board, board_group, collection):
    # todo: update a 'category' in readme.
    pass

  def find_external_card(self, card):
    """
    This checks if a card already exists externally by looking for a Readme
    doc with the same title.

    To do this, we get a list of all categories, then get a list of all docs
    in each category and scan the docs. If we find one with a matching title,
    we return its slug (which is what we use as the external ID).
    """
    url = "https://dash.readme.io/api/v1/categories?perPage=100"
    categories = requests.get(url, auth=(README_API_TOKEN, "")).json()

    for category in categories:
      url = "https://dash.readme.io/api/v1/categories/%s/docs" % category.get("slug")
      docs = requests.get(url, json={}, auth=(README_API_TOKEN, "")).json()

      for doc in docs:
        if doc.get("title") == card.title:
          return doc.get("slug")

  def create_external_card(self, card, section, board, board_group, collection):
    """
    This method is called automatically when the SDK sees a card
    that it knows hasn't been published before. This means we need
    to use Readme's POST endpoint to create a new doc.
    """
    data = {
      "title": card.title,
      "type": "basic",
      "body": get_card_content(card),
      "hidden": card.has_tag("draft")
    }
    if section:
      data["category"] = self.get_external_id(section.id)
    
    url = "https://dash.readme.io/api/v1/docs"

    # This method has to return the Readme ID of the new doc. We need
    # to remember the Readme ID that's associated with each Guru card
    # so the next time we publish this card we can make the 'update'
    # call to Readme to update this particular doc.
    return requests.post(url, json=data, auth=(README_API_TOKEN, "")).json().get("_id")
  
  def update_external_card(self, external_id, card, section, board, board_group, collection):
    """
    This script stores metadata so it knows which cards have been
    published before. If a card has already been published to
    Readme, it'll call this method so we can make the PUT call to
    update the doc in Readme.
    """
    data = {
      "title": card.title,
      "type": "basic",
      "body": get_card_content(card),
      "hidden": card.has_tag("draft")
    }
    if section:
      data["category"] = self.get_external_id(section.id)

    url = "https://dash.readme.io/api/v1/docs/%s" % external_id

    # this method returns the response object so the SDK will know
    # if the API call to update the doc was successful.
    return requests.put(url, json=data, auth=(README_API_TOKEN, ""))
  
  def delete_external_card(self, external_id):
    # if we want to automatically delete Readme docs when the Guru
    # cards are archived, we could implement that here.
    pass


if __name__ == "__main__":
  g = guru.Guru(GURU_USER, GURU_API_TOKEN)
  publisher = ReadmePublisher(g)

  # 6Tkg78RT is the slug that identifies the board we publish to Readme.
  # you can find this ID in the board's URL, like:
  # https://app.getguru.com/boards/6Tkg78RT/Readme-Guides
  publisher.publish_board("6Tkg78RT")

  # for now, we haven't implemented any of the 'delete' methods. if we do want to
  # be able to delete Readme docs when the guru cards are archived (or when they're
  # removed from our 'readme' board), we'll need to implement the delete method and
  # also call process_deletions().
  # publisher.process_deletions()