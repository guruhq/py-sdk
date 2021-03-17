
import json
import yaml
import unittest
import responses

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
        "id": "2222",
        "value": "troubleshooting"
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
        "id": "2222",
        "value": "troubleshooting"
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
        "id": "2222",
        "value": "troubleshooting"
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
        "id": "2222",
        "value": "troubleshooting"
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
        "id": "2222",
        "value": "troubleshooting"
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

  
  @use_guru()
  @responses.activate
  def test_add_tag_to_card(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1234/extended", json={
      "id": "1234"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/whoami", json={
      "team": {
        "id": "abcd"
      }
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/teams/abcd/tagcategories", json=[{
      "tags": [{
        "id": "abcd",
        "value": "tag1"
      }],
      "id": "1234",
      "name": "category"
    }])
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/cards/1234/tags/abcd", json={})
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/cards/1234", json={})

    card = g.get_card("1234")

    # we call this twice but expect only one PUT call.
    card.add_tag("tag1")
    card.add_tag("tag1")

    # calling add_tag() will save the card, but we want to make sure this
    # saves the card and also includes tag1 as part of its data.
    card.save()

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1234/extended"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/whoami"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/teams/abcd/tagcategories"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/cards/1234/tags/abcd"
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
  def test_add_new_tag_to_card(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1234/extended", json={
      "id": "1234"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/whoami", json={
      "team": {
        "id": "abcd"
      }
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/teams/abcd/tagcategories", json=[{
      "tags": [],
      "name": "category",
      "name": "Tags",
      "id": "2222"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/teams/abcd/tagcategories/tags", json={
      "id": "abcd",
      "value" : "new_tag",
      "categoryName" : "Tags",
      "categoryId" : "2222"
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/cards/1234/tags/abcd", json={})
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/cards/1234", json={})

    card = g.get_card("1234")
    card.add_tag("new_tag", create=True)

    # calling add_tag() will save the card, but we want to make sure this
    # saves the card and also includes 'new_tag' as part of its data.
    card.save()

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1234/extended"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/whoami"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/teams/abcd/tagcategories"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/teams/abcd/tagcategories/tags",
      "body": {
        "categoryId": "2222",
        "value": "new_tag"
      }
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/cards/1234/tags/abcd"
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
          "value": "new_tag",
          "categoryName": "Tags",
          "categoryId": "2222"
        }],
        "suppressVerification": True
      }
    }])
