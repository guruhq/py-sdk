
import json
import yaml
import unittest
import responses

from tests.util import use_guru, get_calls

import guru


class TestCoreCache(unittest.TestCase):
  @use_guru()
  @responses.activate
  def test_that_caching_happens(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[])
    g.get_group("group name")
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }])

    # this triggers a second call because we're not using the cache.
    g.get_group("group name")
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }])

    # if we use cache=True this won't make another call.
    g.get_group("group name", cache=True)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }])

  @use_guru()
  @responses.activate
  def test_that_the_cache_is_cleared_after_creating_a_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?search=user%40example.com", json=[{
      "user": {"email": "user@example.com"},
      "groups": []
    }])

    # the first call happens when we try to add the user to the group (we want it to fail).
    # the second call happens inside make_group -- it checks if the group exists before creating it (we want it to not exist).
    # the third call happens when we add the user to the group again and we want to simulate the group now existing.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1111",
      "name": "Experts"
    }])

    responses.add(responses.POST, "https://api.getguru.com/api/v1/groups", json={})
    responses.add(responses.POST, "https://api.getguru.com/api/v1/groups/1111/members", json=[
      {"id": "user@example.com"}
    ])

    # the frist time we call this, the group doesn't exist.
    result1 = g.add_user_to_group("user@example.com", "Experts")
    self.assertEqual(result1, {"Experts": False})

    # create the group.
    g.make_group("Experts")

    # add_user_to_group uses cache=True so if we don't clear the cache automatically, this'll fail again.
    result2 = g.add_user_to_group("user@example.com", "Experts")
    self.assertEqual(result2, {"Experts": True})

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/members?search=user%40example.com"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups",
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups",
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/groups",
      "body": {
        "id": "new-group",
        "name": "Experts"
      }
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/members?search=user%40example.com"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/groups/1111/members",
      "body": [
        "user@example.com"
      ]
    }])
