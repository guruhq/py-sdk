"""
This script shows how to use Guru's SDK to publish cards,
folders, or entire collections to an external site, like a
third-party help site.

This script takes the contents of a folder in Guru and makes
API calls to Intercom (https://www.intercom.com/) to create
or update articles in Intercom based on the changes seen in
Guru. There are a few parts to this:

1. Behind the scenes, the SDK enumerates all the folders
   and cards on the folder we specify.
2. The SDK also writes a metadata .json file to keep track
   of which cards have been published before.
3. Using the metadata, the SDK knows whether a card has been
   published before and needs to be updated in Intercom or is
   a brand new card and we need to create an article in Intercom.

The SDK orchestrates everything on the Guru side. This script
just implements the calls to Intercom's API to create and update
each type of object. When the Guru SDK sees a card that's never
been published before, it'll call create_external_card and we
need to implement the Intercom API call to create the article.
"""

import os
import guru
import requests

from urllib.parse import unquote

GURU_USER = os.environ.get("GURU_USER")
GURU_API_TOKEN = os.environ.get("GURU_API_TOKEN")
INTERCOM_API_TOKEN = os.environ.get("INTERCOM_API_TOKEN")


class IntercomPublisher(guru.PublisherFolders):
  def __init__(self, g):
    super().__init__(g)

    # we use this to cache the responses to the API calls
    # for looking up articles, sections, or collections.
    self.cache = {}

  def get_headers(self):
    return {
        "Authorization": "Bearer %s" % INTERCOM_API_TOKEN
    }

  def get_all(self, url):
    """
    Make a GET call to Intercom's API and use its pagination
    to load all pages of results.
    """
    if self.cache.get(url):
      return self.cache.get(url)

    results = []
    original_url = url

    while url:
      response = requests.get(url, headers=self.get_headers())
      results += response.json().get("data")
      url = response.json().get("pages", {}).get("next")

    self.cache[original_url] = results
    return results

  def get_external_url(self, external_id, card):
    """
    This builds the public-facing URL for an Intercom article. We use this
    to convert links between Guru Cards to be links between Intercom articles.
    """
    return "https://intercom.help/publishing-test-dev/en/articles/%s" % external_id

  def find_external_collection(self, collection):
    """
    This checks if a colelction already exists in Intercom by checking for one
    with the same name. Guru collections are 'Collections' in Intercom.
    """
    intercom_collections = self.get_all(
        "https://api.intercom.io/help_center/collections")

    for intercom_collection in intercom_collections:
      if intercom_collection["name"].lower() == collection.title.lower():
        return intercom_collection["id"]

  def create_external_collection(self, collection):
    """
    If a card is in a collection and we can't find a 'collection' with the
    same name in Intercom, we'll call this function to create the
    collection in Intercom. It'd use this API call:

    https://developers.intercom.com/intercom-api-reference/reference#create-a-collection

    We don't have to implement this. If we don't, then we're simply
    requiring that new collections be created manually in Intercom.
    This might be fine, depending on how often you plan to make
    new collections.
    """
    pass

  def update_external_collection(self, external_id, collection):
    """
    This is similar to create_external_folder except it's called when
    a Guru collection is updated (e.g. you changed it's name) and this would
    make the Intercom API call to update an Intercom collection:

    https://developers.intercom.com/intercom-api-reference/reference#update-a-collection
    """
    pass

  def find_external_section(self, folder):
    """
    This checks if a section already exists in Intercom by checking for one with
    the same name. Sections in intercom are synonymous with folders in Guru.
    """
    intercom_sections = self.get_all(
        "https://api.intercom.io/help_center/sections")

    for intercom_section in intercom_sections:
      if intercom_section["name"].lower() == folder.title.lower():
        return intercom_section["id"]

  def create_external_section(self, folder, collection):
    """
    If a card is in a folder and we can't find a a section name in Intercom with the same name, we'll call this function to create the
    section in Intercom. It'd use this API call:

    https://developers.intercom.com/intercom-api-reference/reference#create-a-section

    We don't have to implement this. If we don't, then we're simply
    requiring that new sections be created manually in Intercom.
    This might be fine, depending on how often you plan to make
    new sections.
    """
    pass

  def update_external_section(self, external_id, folder, collection):
    """
    This is similar to create_external_section except it's called when
    a Guru folder is updated (e.g. you changed it's name) and this would
    make the Intercom API call to update a section:

    https://developers.intercom.com/intercom-api-reference/reference#update-a-section
    """
    pass

  def find_external_card(self, card):
    """
    This checks if a card already exists externally by looking for an Intercom
    article with the same title.
    """
    articles = self.get_all("https://api.intercom.io/articles")

    for article in articles:
      if article.get("title").lower() == card.title.lower():
        return article.get("id")

  def convert_card_to_article(self, card, folder=None, collection=None):
    """
    This builds the JSON payload for creating or updating an
    Intercom article from the given Guru Card.
    """
    data = {
        "title": card.title,
        "author_id": 5056532,
        "body": card.content,
        "state": "published",
    }

    # if the card is on a folder, that's its parent Section in Intercom.
    # if it's on a Collection, then that's its parent in Intercom.
    if collection:
      data["parent_id"] = self.get_external_id(collection.id)
      data["parent_type"] = "collection"
    elif folder:
      data["parent_id"] = self.get_external_id(folder.id)
      data["parent_type"] = "section"

    return data

  def create_external_card(self, card, changes, folder=None, collection=None):
    """
    This method is called automatically when the SDK sees a card
    that it knows hasn't been published before. This means we need
    to use Intercom's POST endpoint to create a new article.

    NOTE: Pass only a folder or collection. Logic will default to collection first.

    """
    data = self.convert_card_to_article(card, folder, collection)
    url = "https://api.intercom.io/articles"

    # This method has to return the Intercom ID of the new article. We need
    # to remember the Intercom ID that's associated with each Guru card so
    # the next time we publish this card we can make the 'update' call to
    # Intercom to update this particular article.
    return requests.post(url, json=data, headers=self.get_headers()).json().get("id")

  def update_external_card(self, external_id, card, folder, collection):
    """
    This script stores metadata so it knows which cards have been
    published before. If a card has already been published to
    Intercom, it'll call this method so we can make the PUT call
    to update the article in Intercom.
    """
    data = self.convert_card_to_article(card, folder, collection)
    url = "https://api.intercom.io/articles/%s" % external_id

    # this method returns the response object so the SDK will know
    # if the API call to update the article was successful.
    return requests.put(url, json=data, headers=self.get_headers())

  def delete_external_card(self, external_id):
    # if we want to automatically delete Intercom articles when the Guru
    # cards are archived, we could implement that here.
    pass


if __name__ == "__main__":
  g = guru.Guru(GURU_USER, GURU_API_TOKEN)
  publisher = IntercomPublisher(g)

  # 'Gi6dzBxi' is the slug that identifies the folder we publish to Intercom.
  # you can find this ID in the folder's URL, like:
  # https://app.getguru.com/folder/Gi6dzBxi/Intercom-Articles
  publisher.publish_folder("Gi6dzBxi")

  # for now, we haven't implemented any of the 'delete' methods. if we do want to
  # be able to delete Intercom articles when the guru cards are archived (or when
  # they're removed from our 'intercom' folder), we'll need to implement the delete
  # method and also call process_deletions().
  # publisher.process_deletions()
