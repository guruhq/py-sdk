
import json
import yaml
import unittest
import responses

from tests.util import use_guru, get_calls

import guru


class TestCore(unittest.TestCase):
  @use_guru()
  @responses.activate
  def test_get_all_drafts(self, g):
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/drafts", json=[{
      "content": "test",
      "title": "new card",
      "id": "abcd",
      "user": {"email": "user@example.com"},
      "jsonContent": "{}",
      "saveType": "AUTO"
    }])

    # this should trigger the GET call we're expecting.
    g.get_drafts()

    # assert that the only API activity was the one call we expected to see.
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/drafts"
    }])

  @use_guru()
  @responses.activate
  def test_get_drafts_for_one_card(self, g):
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", json={
      "id": "1111"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/drafts/1111", json=[{
      "content": "test",
      "title": "new card",
      "id": "abcd",
      "user": {"email": "user@example.com"},
      "jsonContent": "{}",
      "saveType": "AUTO"
    }])

    # this should trigger the GET call we're expecting.
    g.get_drafts(card="1111")

    # assert that the only API activity was the one call we expected to see.
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111/extended",
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/drafts/1111"
    }])
  
  @use_guru()
  @responses.activate
  def test_get_drafts_for_invalid(self, g):
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", status=404)

    # this should trigger the GET call we're expecting.
    g.get_drafts(card="1111")

    # assert that the only API activity was the one call we expected to see.
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111/extended",
    }])

  @use_guru()
  @responses.activate
  def test_deleting_a_draft(self, g):
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/drafts", json=[{
      "content": "test",
      "title": "new card",
      "id": "abcd",
      "user": {"email": "user@example.com"},
      "jsonContent": "{}",
      "saveType": "AUTO"
    }])
    responses.add(responses.DELETE, "https://api.getguru.com/api/v1/drafts/abcd", status=204)

    # load your drafts then delete one.
    drafts = g.get_drafts()
    g.delete_draft(drafts[0])

    # assert that the only API activity was the one call we expected to see.
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/drafts"
    }, {
      "method": "DELETE",
      "url": "https://api.getguru.com/api/v1/drafts/abcd"
    }])

  @use_guru()
  @responses.activate
  def test_creating_a_draft(self, g):
    responses.add(responses.POST, "https://api.getguru.com/api/v1/drafts", json={
      "lastModified": "2021-07-28T18:51:55.114+0000",
      "version": 1,
      "title": "test",
      "id": "11111111-1111-1111-1111-111111111111",
      "content": "<p>content</p>",
      "user": {
        "status": "ACTIVE",
        "email": "test@example.com",
        "profilePicUrl": "https://pp.getguru.com/32aa6966982240deace9f0a5b735b481.jpeg",
        "lastName": "Test",
        "firstName": "User"
      },
      "jsonContent": "",
      "saveType": "USER"
    })

    draft = g.create_draft("test", "<p>content</p>")
    self.assertEqual(get_calls(), [{
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/drafts",
      "body": {
        "content": "<p>content</p>",
        "jsonContent": "",
        "title": "test",
        "saveType": "USER"
      }
    }])

    self.assertEqual(draft.title, "test")
    self.assertEqual(draft.content, "<p>content</p>")
    self.assertEqual(draft.version, 1)
    self.assertEqual(draft.save_type, "USER")
