"""
This script shows how to use Guru's SDK to publish cards,
boards, or entire collections to an external site -- in this
case, Salesforce Knowledge.

This script takes the contents of a board in Guru and makes
API calls to Salesforce to create or update Knowledge objects
as needed.

1. Behind the scenes, the SDK enumerates all the sections
   and cards on the board we specify.
2. The SDK also writes a metadata .json file to keep track
   of which cards have been published before.
3. Using the metadata, the SDK knows whether a card has been
   published before and needs to be updated in Saleforce or
   is a brand new card and we need to create a Knowledge
   object in Salesforce.

The SDK orchestrates everything and this file just needs to
implement methods that call SFDC's API to do specific tasks.
When the SDK sees a card that's never been published before,
it'll call create_external_card and we implement the POST call
to create the Knowledge object.
"""

import os
import guru
import requests


class SalesforcePublisher(guru.Publisher):
  def __init__(self, g):
    super().__init__(g)

    # get your sfdc access token.
    # i set this connection up in salesforce by following this guide:
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
    Salesforce Knowledge object to another.
    """
    return "https://developer.getguru.com/docs/%s" % external_id

  def find_external_card(self, card):
    """
    If some articles may already exist in Salesforce, this method
    is how you'd match a Guru card to an existing Knowledge object.

    For example, this method could search SFDC to see if there's
    a Knowledge object with the same title as this card. If this
    method returns the SFDC Object's ID, the SDK then knows the card
    exists in SFDC already and calls update_external_card().
    """
    pass

  def create_external_card(self, card, section, board, board_group, collection):
    """
    This method is called automatically when the SDK sees a card
    that it knows hasn't been published before. This means we need
    to use SFDC's POST endpoint to create a new Knowledge object.
    """
    data = {
      "title": card.title,
      "summary" : "",
      "UrlName": card.slug.split("/")[1],
      # this is the Knowledge object's rich text field which is not configured by default.
      # i called mine 'Body' so that's why this is 'Body__c'.
      "Body__c": card.content
    }
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
    data = {
      "title": card.title,
      "summary" : "",
      "UrlName": card.slug.split("/")[1],
      "Body__c": card.content
    }
    headers = {
      "Authorization": "Bearer %s" % self.sfdc_token
    }

    url = "%s/services/data/v43.0/support/knowledgeArticles/%s" % (self.sfdc_url, external_id)
    return requests.put(url, json=data, headers=headers)
  
  def delete_external_card(self, external_id):
    # if we want to automatically delete Salesforce Knowledge articles
    # when the Guru cards are archived, you'd implement that here.
    pass


if __name__ == "__main__":
  guru_user = os.environ.get("GURU_USER")
  guru_api_token = os.environ.get("GURU_API_TOKEN")
  g = guru.Guru(guru_user, guru_api_token)
  publisher = SalesforcePublisher(g)

  # the identifier here comes from a board's URL.
  # in this case i'm publishing this board from my test team:
  # https://app.getguru.com/boards/KieEXj9i/Managing-and-Sharing-your-Guru-team
  publisher.publish_board("KieEXj9i")
