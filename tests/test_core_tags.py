
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
  def test_get_tags(self, g):
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/whoami", json={
      "team": {
        "id": "abcd"
      }
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/teams/abcd/tagcategories", json=[{
      "id": "0000",
      "tags": [{
        "id": "1111",
        "value": "case study"
      }, {
        "id" : "2222",
        "value" : "troubleshooting"
      }]
    }])

    tags = g.get_tags()

    # assert that the only API activity was the one call we expected to see.
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/whoami"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/teams/abcd/tagcategories"
    }])

    # do assertions about the objects we get back.
    self.assertEqual(len(tags), 2)
    self.assertEqual(tags[0].id, "1111")
    self.assertEqual(tags[0].value, "case study")
    self.assertEqual(tags[1].id, "2222")
    self.assertEqual(tags[1].value, "troubleshooting")
  
  @use_guru()
  @responses.activate
  def test_delete_tag_by_id(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/whoami", json={
      "team": {
        "id": "abcd"
      }
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/teams/abcd/tagcategories", json=[{
      "id": "0000",
      "tags": [{
        "id": "1111",
        "value": "case study"
      }, {
        "id" : "2222",
        "value" : "troubleshooting"
      }]
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/teams/abcd/bulkop", json={})

    g.delete_tag("1111")

    # assert that the only API activity was the one call we expected to see.
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/whoami"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/teams/abcd/tagcategories"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/teams/abcd/bulkop",
      "body": {
        "action": {
          "type": "delete-tag",
          "tagId": "1111"
        }
      }
    }])

  @use_guru()
  @responses.activate
  def test_delete_tag_by_value(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/whoami", json={
      "team": {
        "id": "abcd"
      }
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/teams/abcd/tagcategories", json=[{
      "id": "0000",
      "tags": [{
        "id": "1111",
        "value": "case study"
      }, {
        "id" : "2222",
        "value" : "troubleshooting"
      }]
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/teams/abcd/bulkop", json={})

    g.delete_tag("troubleshooting")

    # assert that the only API activity was the one call we expected to see.
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/whoami"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/teams/abcd/tagcategories"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/teams/abcd/bulkop",
      "body": {
        "action": {
          "type": "delete-tag",
          "tagId": "2222"
        }
      }
    }])
  
  @use_guru()
  @responses.activate
  def test_delete_invalid_tag(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/whoami", json={
      "team": {
        "id": "abcd"
      }
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/teams/abcd/tagcategories", json=[{
      "id": "0000",
      "tags": [{
        "id": "1111",
        "value": "case study"
      }]
    }])

    result = g.delete_tag("3333")

    # assert that the only API activity was the one call we expected to see.
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/whoami"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/teams/abcd/tagcategories"
    }])
    self.assertEqual(result, False)

  @use_guru()
  @responses.activate
  def test_merge_tags(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/whoami", json={
      "team": {
        "id": "abcd"
      }
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/teams/abcd/tagcategories", json=[{
      "id": "0000",
      "tags": [{
        "id": "1111",
        "value": "case study"
      }, {
        "id" : "2222",
        "value" : "troubleshooting"
      }]
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/teams/abcd/bulkop", json={})

    tags = g.get_tags()
    g.merge_tags("case study", tags[1])

    # assert that the only API activity was the one call we expected to see.
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/whoami"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/teams/abcd/tagcategories"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/teams/abcd/tagcategories"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/teams/abcd/bulkop",
      "body": {
        "action": {
        "type": "merge-tag",
          "mergeSpec": {
            "parentId": "1111",
            "childIds": [
              "2222"
            ]
          }
        }
      }
    }])
  
  @use_guru()
  @responses.activate
  def test_merge_invalid_tag(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/whoami", json={
      "team": {
        "id": "abcd"
      }
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/teams/abcd/tagcategories", json=[{
      "id": "0000",
      "tags": [{
        "id": "1111",
        "value": "case study"
      }, {
        "id" : "2222",
        "value" : "troubleshooting"
      }]
    }])

    tags = g.get_tags()
    g.merge_tags("case study", "3333")

    # assert that the only API activity was the one call we expected to see.
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/whoami"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/teams/abcd/tagcategories"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/teams/abcd/tagcategories"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/teams/abcd/tagcategories"
    }])
