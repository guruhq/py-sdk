
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
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111", json={
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
      "url": "https://api.getguru.com/api/v1/cards/1111",
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/drafts/1111"
    }])
  
  @use_guru()
  @responses.activate
  def test_get_drafts_for_invalid(self, g):
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111", status=404)

    # this should trigger the GET call we're expecting.
    g.get_drafts(card="1111")

    # assert that the only API activity was the one call we expected to see.
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111",
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
