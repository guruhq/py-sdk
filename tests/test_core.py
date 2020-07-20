
import json
import yaml
import unittest
import responses

from unittest.mock import Mock, patch
from requests.auth import HTTPBasicAuth

import guru

def use_guru(username="user@example.com", api_token="abcdabcd-abcd-abcd-abcd-abcdabcdabcd", silent=True, dry_run=False):
  def wrapper(func):
    def call_func(self):
      g = guru.Guru(username, api_token, silent=silent, dry_run=dry_run)
      func(self, g)
    return call_func
  return wrapper

def get_calls():
  calls = []
  for call in responses.calls:
    c = {
      "method": call.request.method,
      "url": call.request.url
    }
    if call.request.method != "GET" and call.request.body:
      try:
        c["body"] = json.loads(call.request.body)
      except:
        c["body"] = call.request.body
    calls.append(c)
  return calls

class TestExample(unittest.TestCase):
  @use_guru()
  @responses.activate
  def test_get_card(self, g):
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/cardid", json={})

    # this should trigger the GET call we're expecting.
    card = g.get_card("cardid")

    # assert that the only API activity was the one call we expected to see.
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/cardid"
    }])

  @use_guru()
  @responses.activate
  def test_get_card_and_use_doc(self, g):
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/cardid", json={
      "content": "<p>test</p>"
    })

    # this should trigger the GET call we're expecting.
    card = g.get_card("cardid")

    self.assertEqual(len(card.doc.select("p")), 1)
    self.assertEqual(len(card.doc.select("p")), 1)
    self.assertEqual(len(card.doc.select("span")), 0)

    card.content = "<p><span>test</span></p>"
    self.assertEqual(len(card.doc.select("p")), 1)
    self.assertEqual(len(card.doc.select("span")), 1)

  @use_guru()
  @responses.activate
  def test_get_card_and_check_url(self, g):
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111", json={})
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/2222", json={
      "slug": "abcd"
    })

    # this should trigger the GET call we're expecting.
    card1 = g.get_card("1111")
    card2 = g.get_card("2222")

    # assert that the only API activity was the one call we expected to see.
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/2222"
    }])

    self.assertEqual(card1.url, "")
    self.assertEqual(card2.url, "https://app.getguru.com/card/abcd")

  @use_guru()
  @responses.activate
  def test_get_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[])
    card = g.get_group("group name")
    self.assertEqual(len(get_calls()), 1)

    # this will trigger a second call because it's not cached.
    card = g.get_group("group name")
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }])
  
    # caching means this doesn't trigger a third call.
    card = g.get_group("group name", cache=True)
    self.assertEqual(len(get_calls()), 2)
  
  @use_guru()
  @responses.activate
  def test_get_collection_by_name(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "name": "test"
    }])
    g.get_collection("test")
    self.assertEqual(get_calls(), [
      {
        "method": "GET",
        "url": "https://api.getguru.com/api/v1/collections"
      }
    ])

  @use_guru()
  @responses.activate
  def test_get_collection_by_id(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections/11111111-1111-1111-1111-111111111111", json={})
    g.get_collection("11111111-1111-1111-1111-111111111111")
    self.assertEqual(get_calls(), [
      {
        "method": "GET",
        "url": "https://api.getguru.com/api/v1/collections/11111111-1111-1111-1111-111111111111"
      }
    ])

  @use_guru()
  @responses.activate
  def test_make_collection(self, g):
    # make_collection() will look up the group by name so we need this to return something.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1234",
      "name": "All Members"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/collections", json={})
    g.make_collection("Test")

    self.assertEqual(get_calls(), [
      {
        "method": "GET",
        "url": "https://api.getguru.com/api/v1/groups"
      }, {
        "method": "POST",
        "url": "https://api.getguru.com/api/v1/collections",
        "body": {
          "name": "Test",
          "color": "#009688",
          "description": "",
          "collectionType": "INTERNAL",
          "publicCardsEnabled": True,
          "syncVerificationEnabled": False,
          "initialAdminGroupId": "1234"
        }
      }
    ])

  @use_guru()
  @responses.activate
  def test_make_collection_with_missing_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[])

    g.make_collection("Test")

    # this makes a GET call to look for the group called 'Test'
    # but it doesn't make the POST call because it doesn't find the group.
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }])
  
  @use_guru()
  @responses.activate
  def test_add_group_to_collection(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "5678",
      "name": "Experts"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "abcd",
      "name": "General"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/collections/abcd/groups", json={})

    g.add_group_to_collection("Experts", "General", guru.AUTHOR)

    # this makes get calls to look up the group and collection by name, then
    # a post call to add the group to the collection.
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/collections/abcd/groups",
      "body": {
        "groupId": "5678",
        "role": "AUTHOR"
      }
    }])

  @use_guru()
  @responses.activate
  def test_add_group_to_collection_with_invalid_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "abcd",
      "name": "General"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/collections/abcd/groups", json={})

    result = g.add_group_to_collection("Experts", "General", guru.AUTHOR)

    self.assertEqual(result, False)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }])
  
  @use_guru()
  @responses.activate
  def test_add_group_to_collection_with_invalid_collection(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1234",
      "name": "Experts"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/collections/abcd/groups", json={})

    result = g.add_group_to_collection("Experts", "General", guru.AUTHOR)

    self.assertEqual(result, False)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }])

  @use_guru()
  @responses.activate
  def test_add_group_to_collection_when_its_already_on_it(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "5678",
      "name": "Experts"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "abcd",
      "name": "General"
    }])
    # when we try to add a group to a collection and it's already on the collection, the POST
    # call returns a 400 response, this will make us trigger a PUT call instead.
    responses.add(responses.POST, "https://api.getguru.com/api/v1/collections/abcd/groups", json={}, status=400)
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/collections/abcd/groups/5678", json={})

    g.add_group_to_collection("Experts", "General", guru.AUTHOR)

    # this makes get calls to look up the group and collection by name, then
    # a post call to add the group to the collection.
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/collections/abcd/groups",
      "body": {
        "groupId": "5678",
        "role": "AUTHOR"
      }
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/collections/abcd/groups/5678",
      "body": {
        "groupId": "5678",
        "role": "AUTHOR"
      }
    }])
  
  @use_guru()
  @responses.activate
  def test_remove_group_from_collection(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "5678",
      "name": "Experts"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "abcd",
      "name": "General"
    }])
    responses.add(responses.DELETE, "https://api.getguru.com/api/v1/collections/abcd/groups/5678")

    g.remove_group_from_collection("Experts", "General")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }, {
      "method": "DELETE",
      "url": "https://api.getguru.com/api/v1/collections/abcd/groups/5678"
    }])
  
  @use_guru()
  @responses.activate
  def test_remove_group_from_collection_with_invalid_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "abcd",
      "name": "General"
    }])
    responses.add(responses.DELETE, "https://api.getguru.com/api/v1/collections/abcd/groups/5678")

    result = g.remove_group_from_collection("Experts", "General")

    self.assertEqual(result, False)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }])
  
  @use_guru()
  @responses.activate
  def test_remove_group_from_collection_with_invalid_collection(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "5678",
      "name": "Experts"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[])
    responses.add(responses.DELETE, "https://api.getguru.com/api/v1/collections/abcd/groups/5678")

    result = g.remove_group_from_collection("Experts", "General")

    self.assertEqual(result, False)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }])

  @use_guru()
  @responses.activate
  def test_delete_collection(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "abcd",
      "name": "General"
    }])
    responses.add(responses.DELETE, "https://api.getguru.com/api/v1/collections/abcd")

    g.delete_collection("General")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }, {
      "method": "DELETE",
      "url": "https://api.getguru.com/api/v1/collections/abcd"
    }])
  
  @use_guru()
  @responses.activate
  def test_delete_collection_with_invalid_collection(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[])
    responses.add(responses.DELETE, "https://api.getguru.com/api/v1/collections/abcd")

    g.delete_collection("General")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }])
  
  @use_guru()
  @responses.activate
  def test_invite_user(self, g):
    responses.add(responses.POST, "https://api.getguru.com/api/v1/members/invite", json={})

    g.invite_user("user@example.com")

    self.assertEqual(get_calls(), [{
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/members/invite",
      "body": {
        "emails": "user@example.com"
      }
    }])
  
  @use_guru()
  @responses.activate
  def test_invite_user_and_add_to_groups(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1234",
      "name": "Experts"
    }, {
      "id": "5678",
      "name": "other group"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/members/invite", json={})
    responses.add(responses.POST, "https://api.getguru.com/api/v1/groups/1234/members")
    responses.add(responses.POST, "https://api.getguru.com/api/v1/groups/5678/members")

    g.invite_user("user@example.com", "Experts", "other group")

    self.assertEqual(get_calls(), [{
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/members/invite",
      "body": {
        "emails": "user@example.com"
      }
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/groups/1234/members",
      "body": [
        "user@example.com"
      ]
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/groups/5678/members",
      "body": [
        "user@example.com"
      ]
    }])

  @use_guru()
  @responses.activate
  def test_invite_user_to_invalid_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1234",
      "name": "Experts"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/members/invite", json={})

    g.invite_user("user@example.com", "other group")

    self.assertEqual(get_calls(), [{
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/members/invite",
      "body": {
        "emails": "user@example.com"
      }
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }])
  
  @use_guru()
  @responses.activate
  def test_add_user_to_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1234",
      "name": "Experts"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/groups/1234/members")

    g.add_user_to_group("user@example.com", "Experts")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/groups/1234/members",
      "body": [
        "user@example.com"
      ]
    }])

  @use_guru()
  @responses.activate
  def test_add_user_to_invalid_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1234",
      "name": "Other Group"
    }])

    g.add_user_to_group("user@example.com", "Experts")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }])

  @use_guru()
  @responses.activate
  def test_add_user_to_groups(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1234",
      "name": "Experts"
    }, {
      "id": "5678",
      "name": "other group"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/groups/1234/members")
    responses.add(responses.POST, "https://api.getguru.com/api/v1/groups/5678/members")

    g.add_user_to_groups("user@example.com", "Experts", "other group")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/groups/1234/members",
      "body": [
        "user@example.com"
      ]
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/groups/5678/members",
      "body": [
        "user@example.com"
      ]
    }])

  @use_guru()
  @responses.activate
  def test_add_user_to_groups_where_first_one_is_invalid(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "5678",
      "name": "other group"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/groups/5678/members")

    result = g.add_user_to_groups("user@example.com", "Experts", "other group")

    self.assertEqual(result, {
      "Experts": False,
      "other group": True
    })

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/groups/5678/members",
      "body": [
        "user@example.com"
      ]
    }])

  @use_guru()
  @responses.activate
  def test_add_user_to_groups_where_second_one_is_invalid(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1234",
      "name": "Experts"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/groups/1234/members")

    result = g.add_user_to_groups("user@example.com", "Experts", "other group")

    self.assertEqual(result, {
      "Experts": True,
      "other group": False
    })

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/groups/1234/members",
      "body": [
        "user@example.com"
      ]
    }])
  
  @use_guru()
  @responses.activate
  def test_remove_user_from_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1234",
      "name": "Experts"
    }])
    responses.add(responses.DELETE, "https://api.getguru.com/api/v1/groups/1234/members/user@example.com")

    g.remove_user_from_group("user@example.com", "Experts")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "DELETE",
      "url": "https://api.getguru.com/api/v1/groups/1234/members/user@example.com"
    }])
  
  @use_guru()
  @responses.activate
  def test_remove_user_from_groups(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1234",
      "name": "Experts"
    }, {
      "id": "5678",
      "name": "other group"
    }])
    responses.add(responses.DELETE, "https://api.getguru.com/api/v1/groups/1234/members/user@example.com")
    responses.add(responses.DELETE, "https://api.getguru.com/api/v1/groups/5678/members/user@example.com")

    result = g.remove_user_from_groups("user@example.com", "Experts", "other group")

    self.assertEqual(result, {
      "Experts": True,
      "other group": True
    })
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "DELETE",
      "url": "https://api.getguru.com/api/v1/groups/1234/members/user@example.com"
    }, {
      "method": "DELETE",
      "url": "https://api.getguru.com/api/v1/groups/5678/members/user@example.com"
    }])
  
  @use_guru()
  @responses.activate
  def test_remove_user_from_groups_with_invalid_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1234",
      "name": "Experts"
    }])
    responses.add(responses.DELETE, "https://api.getguru.com/api/v1/groups/1234/members/user@example.com")

    result = g.remove_user_from_groups("user@example.com", "Experts", "other group")

    self.assertEqual(result, {
      "Experts": True,
      "other group": False
    })
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "DELETE",
      "url": "https://api.getguru.com/api/v1/groups/1234/members/user@example.com"
    }])

  @use_guru()
  @responses.activate
  def test_remove_user_from_team(self, g):
    responses.add(responses.DELETE, "https://api.getguru.com/api/v1/members/user@example.com/replaceverifier")

    g.remove_user_from_team("user@example.com")

    self.assertEqual(get_calls(), [{
      "method": "DELETE",
      "url": "https://api.getguru.com/api/v1/members/user@example.com/replaceverifier",
      "body": {
        "collectionVerifiers": {}
      }
    }])

  @use_guru()
  @responses.activate
  def test_make_card(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/cards", json={})

    g.make_card("title", "card content", "General")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/cards",
      "body": {
        "cardType": "CARD",
        "collection": {
          "id": "1234",
          "name": "General",
          "type": None,
          "color": None
        },
        "content": "card content",
        "id": None,
        "preferredPhrase": "title",
        "shareStatus": "TEAM",
        "tags": [],
        "suppressVerification": True
      }
    }])
  
  @use_guru()
  @responses.activate
  def test_add_comment_to_card(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111", json={
      "id": "1111"
    })
    responses.add(responses.POST, "https://api.getguru.com/api/v1/cards/1111/comments", json={
      "id": "2222",
      "content": "comment text"
    })

    comment = g.add_comment_to_card("1111", "comment text")

    self.assertEqual(comment.id, "2222")
    self.assertEqual(comment.card.id, "1111")
    self.assertEqual(comment.content, "comment text")
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/cards/1111/comments",
      "body": {"content": "comment text"}
    }])
  
  @use_guru()
  @responses.activate
  def test_update_card_comment(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111", json={
      "id": "1111"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/comments", json=[{
      "id": "2222"
    }])
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/cards/1111/comments/2222", json={
      "id": "2222",
      "content": "updated content"
    })

    comments = g.get_card_comments("1111")
    comments[0].content = "updated content"
    comment = comments[0].save()

    self.assertEqual(comment.content, "updated content")
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111/comments"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/cards/1111/comments/2222",
      "body": {"content": "updated content"}
    }])

  @use_guru()
  @responses.activate
  def test_card_comment_edge_cases(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111", json={
      "id": "1111"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/2222", json=None)

    card = g.get_card("1111")
    card.comment("")

    g.add_comment_to_card("2222", "test")
    g.get_card_comments("2222")
    g.delete_card_comment("2222", "3333")

  @use_guru()
  @responses.activate
  def test_delete_card_comment(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111", json={
      "id": "1111"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/comments", json=[{
      "id": "2222"
    }])
    responses.add(responses.DELETE, "https://api.getguru.com/api/v1/cards/1111/comments/2222")

    comments = g.get_card_comments("1111")
    comments[0].delete()

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111/comments"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111"
    }, {
      "method": "DELETE",
      "url": "https://api.getguru.com/api/v1/cards/1111/comments/2222"
    }])

  @use_guru()
  @responses.activate
  def test_archive_invalid_card(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111", json=None, status=404)

    g.archive_card("1111")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111"
    }])

  @use_guru()
  @responses.activate
  def test_make_card_with_invalid_collection(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/cards", json={})

    g.make_card("title", "card content", "General")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }])

  @use_guru()
  @responses.activate
  def test_save_card(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1234", json={
      "id": "1234"
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/cards/1234", json={})

    card = g.get_card("1234")
    card.save()

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1234"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/cards/1234",
      "body": {
        "cardType": "CARD",
        "collection": None,
        "content": "",
        "id": "1234",
        "preferredPhrase": "",
        "shareStatus": "TEAM",
        "suppressVerification": True,
        "tags": []
      },
    }])

  @use_guru()
  @responses.activate
  def test_add_tag_to_card(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1234", json={
      "id": "1234"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/search/inuse?boardId=&tagIds=&categoryIds=", json=[{
      "tags": [{
        "id": "abcd",
        "value": "tag1"
      }],
      "id": "1234",
      "name": "category"
    }])
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/cards/1234", json={})

    card = g.get_card("1234")
    card.add_tag("tag1")
    card.add_tag("tag1")
    card.save()

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1234"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/search/inuse?boardId=&tagIds=&categoryIds="
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/cards/1234",
      "body": {
        "cardType": "CARD",
        "collection": None,
        "content": "",
        "id": "1234",
        "preferredPhrase": "",
        "shareStatus": "TEAM",
        "tags": [{
          "id": "abcd",
          "value": "tag1",
          "categoryName": None,
          "categoryId": None
        }],
        "suppressVerification": True
      }
    }])

  @use_guru()
  @responses.activate
  def test_add_invalid_tag_to_card(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1234", json={
      "id": "1234"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/search/inuse?boardId=&tagIds=&categoryIds=", json=[{
      "tags": [],
      "id": "1234",
      "name": "category"
    }])

    card = g.get_card("1234")
    card.add_tag("tag1")
    
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1234"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/search/inuse?boardId=&tagIds=&categoryIds="
    }])

  @use_guru()
  @responses.activate
  def test_find_cards(self, g):
    responses.add(responses.POST, "https://api.getguru.com/api/v1/search/cardmgr", json=[])

    g.find_cards()

    self.assertEqual(get_calls(), [{
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/search/cardmgr",
      "body": {
        "queryType": None,
        "sorts": [{
          "type": "verificationState",
          "dir": "ASC"
        }],
        "query": None,
        "collectionIds": []
      }
    }])

  @use_guru()
  @responses.activate
  def test_find_cards_by_collection(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/search/cardmgr", json=[])

    g.find_cards(collection="General")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/search/cardmgr",
      "body": {
        "queryType": None,
        "sorts": [{
          "type": "verificationState",
          "dir": "ASC"
        }],
        "query": None,
        "collectionIds": ["1234"]
      }
    }])
  
  @use_guru()
  @responses.activate
  def test_find_cards_by_tag(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/search/inuse?boardId=&tagIds=&categoryIds=", json=[{
      "tags": [{
        "id": "abcd",
        "value": "tag1"
      }],
      "id": "1234",
      "name": "category"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/search/cardmgr", json=[])

    g.find_cards(tag="tag1")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/search/inuse?boardId=&tagIds=&categoryIds="
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/search/cardmgr",
      "body": {
        "queryType": None,
        "sorts": [{
          "type": "verificationState",
          "dir": "ASC"
        }],
        "query": {
          "nestedExpressions": [{
            "ids": ["abcd"],
            "op": "EXISTS",
            "type": "tag"
          }],
          "op": "AND",
          "type": "grouping"
        },
        "collectionIds": []
      }
    }])
  
  @use_guru()
  @responses.activate
  def test_find_card_by_tag(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/search/inuse?boardId=&tagIds=&categoryIds=", json=[{
      "tags": [{
        "id": "abcd",
        "value": "tag1"
      }],
      "id": "1234",
      "name": "category"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/search/cardmgr", json=[{}])

    g.find_card(tag="tag1")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/search/inuse?boardId=&tagIds=&categoryIds="
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/search/cardmgr",
      "body": {
        "queryType": None,
        "sorts": [{
          "type": "verificationState",
          "dir": "ASC"
        }],
        "query": {
          "nestedExpressions": [{
            "ids": ["abcd"],
            "op": "EXISTS",
            "type": "tag"
          }],
          "op": "AND",
          "type": "grouping"
        },
        "collectionIds": []
      }
    }])

  @use_guru()
  @responses.activate
  def test_find_cards_by_invalid_collection(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[])

    with self.assertRaises(BaseException):
      g.find_cards(collection="General")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }])

  @use_guru()
  @responses.activate
  def test_find_cards_by_invalid_tag(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/search/inuse?boardId=&tagIds=&categoryIds=", json=[{
      "tags": [],
      "id": "1234",
      "name": "category"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/search/cardmgr", json=[])

    g.find_cards(tag="tag1")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/search/inuse?boardId=&tagIds=&categoryIds="
    }])
  
  @use_guru()
  @responses.activate
  def test_make_group(self, g):
    responses.add(responses.POST, "https://api.getguru.com/api/v1/groups", json={})

    g.make_group("new group")

    self.assertEqual(get_calls(), [{
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/groups",
      "body": {
        "id": "new-group",
        "name": "new group"
      }
    }])

  @use_guru()
  @responses.activate
  def test_delete_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1111",
      "name": "New Group"
    }])
    responses.add(responses.DELETE, "https://api.getguru.com/api/v1/groups/1111")

    g.delete_group("new group")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups",
    }, {
      "method": "DELETE",
      "url": "https://api.getguru.com/api/v1/groups/1111",
    }])

  @use_guru()
  @responses.activate
  def test_delete_invalid_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[])

    g.delete_group("new group")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups",
    }])

  @use_guru()
  @responses.activate
  def test_get_board(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/test", json={
      "items": [{
        "type": "section",
        "title": "test",
        "items": [{
          "type": "fact"
        }]
      }, {
        "type": "fact"
      }]
    })

    g.get_board("test")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/test"
    }])

  @use_guru()
  @responses.activate
  def test_get_home_board(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/home?collection=1234", json={
      "items": [{
        "type": "section",
        "items": [{
          "type": "board"
        }]
      }, {
        "type": "board"
      }]
    })

    g.get_home_board("General")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/home?collection=1234"
    }])

  @use_guru()
  @responses.activate
  def test_get_home_board_by_invalid_collection(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/home?collection=1234", json={})

    g.get_home_board("General")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }])

  @use_guru()
  @responses.activate
  def test_get_members(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?search=", json=[])

    g.get_members()

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/members?search="
    }])

  @use_guru()
  @responses.activate
  def test_pagination_on_get_calls(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?search=", json=[
      {}, {}, {}, {}, {}
    ], headers={
      "Link": "< https://api.getguru.com/api/v1/members?token=1>"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?token=1", json=[
      {}, {}, {}, {}
    ], headers={
      "Link": "< https://api.getguru.com/api/v1/members?token=2>"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?token=2", json=[
      {}, {}
    ])

    result = g.get_members()

    self.assertEqual(len(result), 11)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/members?search="
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/members?token=1"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/members?token=2"
    }])

  @use_guru()
  @responses.activate
  def test_upload_content(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])
    responses.add(responses.POST, "https://api.getguru.com/app/contentupload?collectionId=1234", json={})

    g.upload_content("General", "test.zip", "./tests/test.zip")

    post_body = get_calls()[1]["body"]
    self.assertEqual(b'Content-Disposition: form-data; name="contentFile"; filename="test.zip"\r\nContent-Type: application/zip\r\n\r\nzip file\r\n--' in post_body, True)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/app/contentupload?collectionId=1234",
      "body": post_body
    }])

  @use_guru()
  @responses.activate
  def test_upload_and_get_error(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])
    responses.add(responses.POST, "https://api.getguru.com/app/contentupload?collectionId=1234", status=400)

    with self.assertRaises(BaseException):
      g.upload_content("General", "test.zip", "./tests/test.zip")

  @use_guru()
  @responses.activate
  def test_upload_content_to_invalid_collection(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[])

    g.upload_content("General", "test.zip", "test.zip")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }])

  @use_guru(silent=False)
  @responses.activate
  def test_logging(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/cards", json={})
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/cards/1234", json={})
    responses.add(responses.POST, "https://api.getguru.com/api/v1/search/cardmgr", json=[{
      "preferredPhrase": "1234"
    }])
    responses.add(responses.DELETE, "https://api.getguru.com/api/v1/cards/1234")

    # this should trigger the GET call we're expecting.
    card = g.make_card("title", "content", "General")
    card.id = "1234"
    card.save()

    card = g.find_card(title="1234")
    card.id = "1234"
    card.archive()

  @use_guru(dry_run=True)
  @responses.activate
  def test_dry_run(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])

    # this should trigger the GET call we're expecting.
    card = g.make_card("title", "content", "General")
    card.id = "1234"
    card.save()

    card = g.find_card(title="1234")
    card.id = "1234"
    card.archive()

  @use_guru()
  @responses.activate
  def test_get_object_by_reference(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1111",
      "name": "General"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "2222",
      "name": "Experts"
    }])
    collection = g.get_collection("general")
    group = g.get_group("experts")

    collection2 = g.get_collection(collection)
    group2 = g.get_group(group)

    self.assertEqual(collection, collection2)
    self.assertEqual(group, group2)

  @use_guru()
  def test_get_invalid_tag(self, g):
    self.assertIsNone(g.get_tag(""))