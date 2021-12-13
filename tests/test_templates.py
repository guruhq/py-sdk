
import json
import yaml
import unittest
import responses

from tests.util import use_guru, get_calls

import guru


class TestTemplates(unittest.TestCase):
  @use_guru()
  @responses.activate
  def test_get_all_templates(self, g):
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/templates/cards", json=[{
      "content": "test",
      "collection": {
        "id": "1111"
      },
      "cardTitle": "my new card",
      "templateTitle": "my template",
      "id": "2222",
      "verifier": {"type": "user", "email": "user@example.com"},
      "jsonContent": "{}"
    }])

    # this should trigger the GET call we're expecting.
    template = g.get_templates()[0]

    self.assertEqual(template.id, "2222")
    self.assertEqual(template.card_title, "my new card")

    # assert that the only API activity was the one call we expected to see.
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/templates/cards"
    }])

  @use_guru()
  @responses.activate
  def test_adding_a_tag(self, g):
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/templates/cards", json=[{
      "content": "test",
      "description": "my description",
      "collection": {
        "id": "1111"
      },
      "cardTitle": "my new card",
      "templateTitle": "my template",
      "id": "2222",
      "verificationInterval": 90,
      "cardVerifier": {
        "type": "user",
        "id": "user@example.com",
        "user": {
          "email": "user@example.com"
        }
      },
      "jsonContent": "{}"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/whoami", json={
      "team": {
        "id": "3333"
      }
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/teams/3333/tagcategories", json=[{
      "tags": [{
        "id": "4444",
        "value": "test tag"
      }],
      "id": "5555",
      "name": "category"
    }])
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/templates/cards/2222", json={
      "content": "test",
      "collection": {
        "id": "1111"
      },
      "cardTitle": "my new card",
      "templateTitle": "my template",
      "id": "abcd",
      "cardVerifier": {"type": "user", "email": "user@example.com"},
      "jsonContent": "{}"
    })

    # this should trigger the GET call we're expecting.
    template = g.get_templates()[0]

    template.add_tag("test tag")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/templates/cards"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/whoami"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/teams/3333/tagcategories"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/templates/cards/2222",
      "body": {
        "id": "2222",
        "tags": [{
          "id": "4444",
          "value": "test tag",
          "categoryName": None,
          "categoryId": None,
        }],
        "boards": [],
        "content": "test",
        "description": "my description",
        "collection": {
          "id": "1111",
          "name": None,
          "type": None,
          "color": None
        },
        "shareStatus": None,
        "jsonContent": "{}",
        "verificationInterval": 90,
        "cardTitle": "my new card",
        "templateTitle": "my template",
        "cardVerifier": {
          "type": "user",
          "id": "user@example.com"
        }
      }
    }])

  @use_guru()
  @responses.activate
  def test_removing_a_tag(self, g):
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/templates/cards", json=[{
      "content": "test",
      "description": "my description",
      "collection": {
        "id": "1111"
      },
      "tags": [{
        "id": "4444",
        "value": "test tag"
      }],
      "cardTitle": "my new card",
      "templateTitle": "my template",
      "id": "2222",
      "verificationInterval": 90,
      "cardVerifier": {
        "type": "user",
        "id": "user@example.com",
        "user": {
          "email": "user@example.com"
        }
      },
      "jsonContent": "{}"
    }])
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/templates/cards/2222", json={
      "content": "test",
      "collection": {
        "id": "1111"
      },
      "cardTitle": "my new card",
      "templateTitle": "my template",
      "id": "abcd",
      "cardVerifier": {"type": "user", "email": "user@example.com"},
      "jsonContent": "{}"
    })

    # this should trigger the GET call we're expecting.
    template = g.get_templates()[0]

    template.remove_tag("test tag")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/templates/cards"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/templates/cards/2222",
      "body": {
        "id": "2222",
        "tags": [],
        "boards": [],
        "content": "test",
        "description": "my description",
        "collection": {
          "id": "1111",
          "name": None,
          "type": None,
          "color": None
        },
        "shareStatus": None,
        "jsonContent": "{}",
        "verificationInterval": 90,
        "cardTitle": "my new card",
        "templateTitle": "my template",
        "cardVerifier": {
          "type": "user",
          "id": "user@example.com"
        }
      }
    }])
