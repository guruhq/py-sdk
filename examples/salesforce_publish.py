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
"""

import os
import guru
import requests


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

  def create_external_card(self, card, section, board, board_group, collection):
    """
    This method is called automatically when the SDK sees a card
    that it knows hasn't been published before. This means we need
    to use SFDC's POST endpoint to create a new Knowledge object.
    """
    data = convert_card_to_article(card)
    headers = {
      "Authorization": "Bearer %s" % self.sfdc_token
    }
    
    url = "%s/services/data/v20.0/sobjects/Knowledge__kav/" % self.sfdc_url

    # the response will look like this:
    # {
    #   "id": "ka05e000000nLb9AAE",
    #   "success": true,
    #   "errors": []
    # }
    return requests.post(url, json=data, headers=headers).json().get("id")
  
  def update_external_card(self, external_id, card, section, board, board_group, collection):
    """
    This method is called automatically when the SDK sees a card
    that _has_ been published before. We know its Salesforce ID so
    we can make the PUT call to update the Knowledge object.
    """
    data = convert_card_to_article(card)
    headers = {
      "Authorization": "Bearer %s" % self.sfdc_token
    }

    url = "%s/services/data/v43.0/support/knowledgeArticles/%s" % (self.sfdc_url, external_id)
    return requests.put(url, json=data, headers=headers)
  
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
  publisher = SalesforcePublisher(g, dry_run=True)

  # the identifier here comes from a board's URL.
  # in this case i'm publishing this board from my test team:
  # 
  #   https://app.getguru.com/boards/KieEXj9i/Managing-and-Sharing-your-Guru-team
  # 
  # so we can use "KieEXj9i" as its ID.
  publisher.publish_board("KieEXj9i")
