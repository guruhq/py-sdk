"""
This script shows how to use Guru's SDK to publish cards, boards, or entire
collections to an external site -- in this case, Salesforce Knowledge.

This script takes the contents of a board in Guru and makes API calls to
Salesforce to create or update Knowledge objects as needed.

1. Behind the scenes, the SDK enumerates all the sections and cards on the
   board we specify.
2. The SDK also writes a metadata .json file to keep track of which cards have
   been published before.
3. Using the metadata, the SDK knows whether a card has been published before
   and needs to be updated in Saleforce or is a brand new card and we need to
   create a Knowledge object in Salesforce.

The SDK orchestrates everything and this file just needs to implement methods
that call SFDC's API to do specific tasks. When the SDK sees a card that's never
been published before, it'll call create_external_card and we implement the POST
call to create the external representation of a card (e.g. the Knowledge object)

This script uses these environment variables:

 - GURU_USER and GURU_TOKEN to authenticate Guru API calls.
 - SFDC_CLIENT_ID
 - SFDC_CLIENT_SECRET
 - SFDC_USERNAME
 - SFDC_PASSWORD
"""

import os
import guru
import requests

from urllib.parse import quote


def convert_card_to_article(card):
  """
  Guru cards have a title and content but Salesforce Knowledge objects
  can have many fields.
  """
  return {
    "title": card.title,

    # this is the Knowledge object's rich text field which is not configured by default.
    # i called mine 'Body' so that's why this is 'Body__c'.
    "Body__c": card.content,

    # the UrlName is like the title but meant to be displayed in a URL, in Guru
    # we have the card's slug which serves the same purpose. the slug has two
    # parts, an ID and title, so we just need the second part here.
    "UrlName": card.slug.split("/")[1],

    # Guru cards just have one field for their HTML content. if you want to set
    # additional fields, like the summary, you'll need some convention. like, you
    # could start each card with a blockquote as the summary, then in this function
    # you'd separate the content into 'summary' and 'body'.
    "summary": ""
  }



class SalesforcePublisher(guru.Publisher):
  def __init__(self, g, dry_run=False):
    super().__init__(g, dry_run=dry_run)

    # We need to get an SFDC access token.
    # I set this connection up in salesforce by following this guide:
    # https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/CR_quickstart_oauth.htm
    data = {
      "grant_type": "password",
      "client_id": os.environ.get("SFDC_CLIENT_ID"),
      "client_secret": os.environ.get("SFDC_CLIENT_SECRET"),
      "username": os.environ.get("SFDC_USERNAME"),
      "password": os.environ.get("SFDC_PASSWORD")
    }
    sfdc_data = requests.post("https://login.salesforce.com/services/oauth2/token", data=data).json()
    
    self.sfdc_token = sfdc_data.get("access_token")
    self.sfdc_url = sfdc_data.get("instance_url")
    self.data_categories = self.get_all_data_categories()

  def get_external_url(self, external_id, card):
    """
    This is used for converting card-to-card links to link from one
    Salesforce Knowledge object to another. When we're publishing a card
    that links to another Guru card, we use this method to convert the
    card-to-card link to be a link between salesforce knowledge articles.
    """
    return "https://support.getguru.com/help/s/article/%s" % external_id

  def find_external_card(self, card):
    """
    If some articles may already exist in Salesforce, this method
    is how you'd match a Guru card to an existing Knowledge object.

    For example, this method could search SFDC to see if there's
    a Knowledge object with the same title as this card. If this
    method returns the SFDC Object's ID, the SDK then knows the card
    exists in SFDC already and calls update_external_card().

    If you expect all articles will be written in Guru first, then
    you don't need to worry about this method.
    """
    pass

  def sfdc_get(self, url):
    """
    Makes a GET call to salesforce's API. This adds some convenience by adding
    the salesforce instance URL as a prefix and parses the JSON response.
    """
    headers = {
      "Authorization": "Bearer %s" % self.sfdc_token
    }

    # you can pass in just "/services/data/..." as the url and we'll add the prefix.
    if not url.startswith("https:"):
      url = self.sfdc_url + url

    return requests.get(url, headers=headers).json()

  def sfdc_post(self, url, data):
    """
    Makes a POST call to salesforce's API. This adds some convenience by adding
    the salesforce instance URL as a prefix and parses the JSON response.
    """
    headers = {
      "Authorization": "Bearer %s" % self.sfdc_token
    }

    # you can pass in just "/services/data/..." as the url and we'll add the prefix.
    if not url.startswith("https:"):
      url = self.sfdc_url + url

    response = requests.post(url, json=data, headers=headers)
    return response.json()

  def sfdc_delete(self, url):
    """
    Makes a DELETE call to salesforce's API. This adds some convenience by adding
    the salesforce instance URL as a prefix and parses the JSON response.
    """
    headers = {
      "Authorization": "Bearer %s" % self.sfdc_token
    }

    # you can pass in just "/services/data/..." as the url and we'll add the prefix.
    if not url.startswith("https:"):
      url = self.sfdc_url + url

    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
      return True
    else:
      return response.json()

  def get_all_data_categories(self):
    """
    Loads the list of all Data Categories and Data Category Groups from
    Salesforce. When we need to map an article to a Data Category, we'll need
    to have the Data Category's ID. By loading all of them up front, we'll be
    able to look up the ID when we need it without making extra API calls.
    """
    # https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/dome_query.htm
    data_category_groups = self.sfdc_get("/services/data/v52.0/support/dataCategoryGroups?sObjectName=KnowledgeArticleVersion&topCategoriesOnly=false").get("categoryGroups")

    # data categories are arranged in a tree so we use this function to recursively
    # find all categories and build a flat list.
    def find_categories(group_name, objects):
      categories = []

      # each object in the list looks like this:
      #   {
      #     'childCategories': [],
      #     'label': 'Known Issues',
      #     'name': 'Known_Issues',
      #     'url': '/services/data/v52.0/support/dataCategoryGroups/Announcements/dataCategories/Known_Issues?sObjectName=KnowledgeArticleVersion'
      #   }
      # so we add each one to the list and recursively add child categories.
      for object in objects:
        categories.append({
          "group_name": group_name,
          "name": object.get("name"),
          "label": object.get("label")
        })

        # if there are child categories, add them recursively.
        child_categories = object.get("childCategories")
        if child_categories:
          categories += find_categories(group_name, child_categories)

      return categories

    data_categories = []
    for group in data_category_groups:
      data_categories += find_categories(
        group.get("name"),
        group.get("topCategories")[0].get("childCategories")
      )

    return data_categories

  def set_data_category_mappings(self, card, knowledge_id, remove_existing=False):
    """
    Updates the Date Category mappings of a Knowledge Object. These are based
    the Guru Boards the card is on.

    This method removes all existing mappings as this is an easy way to keep
    Salesforce and Guru in sync -- remove all the mappings, then add back the
    ones we need. That way, it doesn't matter how the Card's Board assignments
    changed. If some were added and some were removed, this process will make
    sure the Knowldege object has the correct Data Categories assigned.

    Args:
      card (Card): The Card object Guru's SDK provides representing the Guru
        card that's being published.
      knowledge_id (str): The Salesforce ID of the Knowledge object we're updating.
      remove_existing (False, optional): True if we want to remove all existing
        Data Category mappings. If it's a new article being created we'll leave
        this as False.
    """
    # load the list of existing data category assignments.
    query = "select id, DataCategoryName from Knowledge__DataCategorySelection where ParentId = '%s'" % knowledge_id
    url = "/services/data/v52.0/query/?q=%s" % quote(query)
    mappings = self.sfdc_get(url).get("records")
    mapping_ids = [m.get("Id") for m in mappings]

    # remove all of them. we may add some back but it's hard to match them by
    # name because the names don't match exactly. also, removing all and
    # re-adding the ones we need is the easiest way to make sure salesforce
    # and guru are 100% in sync.
    if remove_existing:
      for mapping_id in mapping_ids:
        self.remove_data_category_mapping(mapping_id)

    # add all of the necessary data category mappings.
    for board in card.boards:
      self.add_data_category_mapping(knowledge_id, board.title)

  def add_data_category_mapping(self, knowledge_id, data_category_name):
    """
    Maps a Salesforce Knowledge object to a Data Category. The Data Category
    is specified by name and we'll look it up to get its Salesforce ID.

    Args:
      knowledge_id (str): The ID of the Knowledge object we're updating.
      data_category_name (str): The name of the Data Category to map the
        Knowledge object to.
    """
    # find the data category group name.
    data_category_group_name = ""
    for category in self.data_categories:
      if category.get("label") == data_category_name:
        data_category_name = category.get("name")
        data_category_group_name = category.get("group_name")
        break

    # if the data category name isn't found, we can stop here.
    if not data_category_group_name:
      return

    data = {
      "DataCategoryGroupName": data_category_group_name,
      "DataCategoryName": data_category_name,
      "ParentId": knowledge_id
    }
    url = "/services/data/v52.0/sobjects/Knowledge__DataCategorySelection/"
    self.sfdc_post(url, data)

  def remove_data_category_mapping(self, mapping_id):
    """
    Removes as single Data Category mapping from a Knowledge object.

    Args:
      mapping_id (str): The Salesforce ID of the Data Category Selection object,
        which is what maps a Knowledge object to Data Category.
    """
    url = "/services/data/v52.0/sobjects/Knowledge__DataCategorySelection/%s" % mapping_id
    return self.sfdc_delete(url)

  def create_external_card(self, card, changes, section, board, board_group, collection):
    """
    This method is called automatically when the SDK sees a card
    that it knows hasn't been published before. This means we need
    to use SFDC's POST endpoint to create a new Knowledge object.
    """
    data = convert_card_to_article(card)
    headers = {
      "Authorization": "Bearer %s" % self.sfdc_token
    }
    
    url = "%s/services/data/v52.0/sobjects/Knowledge__kav/" % self.sfdc_url

    # the response will look like this:
    # {
    #   "id": "ka05e000000nLb9AAE",
    #   "success": true,
    #   "errors": []
    # }
    response = requests.post(url, json=data, headers=headers)
    knowledge_id = response.json().get("id")

    # create the data category mappings.
    self.set_data_category_mappings(card, knowledge_id)

    return knowledge_id
  
  def update_external_card(self, external_id, card, changes, section, board, board_group, collection):
    """
    This method is called automatically when the SDK sees a card that has been
    published before. We know its Salesforce ID so we can make the PUT call to
    update the Knowledge object.
    """
    data = convert_card_to_article(card)
    headers = {
      "Authorization": "Bearer %s" % self.sfdc_token
    }

    url = "%s/services/data/v52.0/sobjects/Knowledge__kav/%s" % (self.sfdc_url, external_id)
    response = requests.patch(url, json=data, headers=headers)

    # the boards in guru determine what data categories the knowledge article is mapped to.
    # when you add or remove board assignments in guru, we need to update salesforce accordingly.
    self.set_data_category_mappings(card, external_id, remove_existing=True)

    return response
  
  def delete_external_card(self, external_id):
    """
    If you want to automatically delete Salesforce Knowledge articles when the
    corresponding card is archived or removed from what you're publishing,
    that's implemented here.
    
    We'll detect when a card is no longer in the set of cards being published
    and call this method. All you need to do here is implement the SFDC API
    call to delete the Knowledge object.
    """
    pass


if __name__ == "__main__":
  guru_user = os.environ.get("GURU_USER")
  guru_api_token = os.environ.get("GURU_API_TOKEN")
  g = guru.Guru(guru_user, guru_api_token)
  publisher = SalesforcePublisher(g, dry_run=False)

  # the identifier here comes from a board's URL.
  # in this case i'm publishing this board from my test team:
  # 
  #   https://app.getguru.com/boards/KieEXj9i/Managing-and-Sharing-your-Guru-team
  # 
  # so we can use "KieEXj9i" as its ID.
  # publisher.publish_board("KieEXj9i")

  # if we're publishing an entire collection we can reference it by name.
  publisher.publish_collection("Publish to Salesforce")
