
import json
import yaml
import unittest
import responses

from unittest.mock import Mock, patch
from requests.auth import HTTPBasicAuth

from tests.util import use_guru, get_calls

import guru


class TestCore(unittest.TestCase):
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
