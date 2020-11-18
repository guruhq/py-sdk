
import json
import yaml
import unittest
import responses

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

  @use_guru()
  @responses.activate
  def test_analytics(self, g):
    # it'll call this first to get your team ID to use as a path parameter.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/whoami", json={
      "team": {
        "id": "abcd"
      }
    })

    # these are the analytics responses.
    # the second page has a header for a third page but we'll call it
    # with max_pages=2 to make sure it doesn't try to load the third.
    base_url = "https://api.getguru.com/api/v1/teams/abcd/analytics"
    responses.add(responses.GET, "%s?fromDate=&toDate=" % base_url, json=[
      {}, {}, {}, {}, {}
    ], headers={
      "Link": "< %s?token=1>" % base_url
    })
    responses.add(responses.GET, "%s?token=1" % base_url, json=[
      {}, {}, {}, {}, {}
    ], headers={
      "Link": "< %s?token=2>" % base_url
    })
    
    g.get_events(max_pages=2)

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/whoami"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/teams/abcd/analytics?fromDate=&toDate="
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/teams/abcd/analytics?token=1"
    }])
