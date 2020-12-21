
import json
import yaml
import unittest
import responses

from tests.util import use_guru, get_calls

import guru


class TestCore(unittest.TestCase):
  @use_guru()
  @responses.activate
  def test_get_card(self, g):
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/cardid/extended", json={})

    # this should trigger the GET call we're expecting.
    card = g.get_card("cardid")

    # assert that the only API activity was the one call we expected to see.
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/cardid/extended"
    }])

  @use_guru()
  @responses.activate
  def test_get_card_and_use_doc(self, g):
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/cardid/extended", json={
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
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", json={})
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/2222/extended", json={
      "slug": "abcd"
    })

    # this should trigger the GET call we're expecting.
    card1 = g.get_card("1111")
    card2 = g.get_card("2222")

    # assert that the only API activity was the one call we expected to see.
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111/extended"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/2222/extended"
    }])

    self.assertEqual(card1.url, "")
    self.assertEqual(card2.url, "https://app.getguru.com/card/abcd")

  @use_guru()
  @responses.activate
  def test_get_card_and_check_verifier(self, g):
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/mycard1/extended", json={
      "verifiers": [
        {
          "type": "user",
          "user": {
            "status": "ACTIVE",
            "email": "jchappelle@getguru.com",
            "firstName": "John",
            "lastName": "Chappelle",
            "profilePicUrl": "/assets/common/images/default-user-pic.png"
          },
          "id": "jchappelle@getguru.com"
        }
      ]
    })

    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/mycard2/extended", json={
      "verifiers": [
        {
          "type": "user-group",
          "userGroup": {
            "name": "Customer Experience",
            "id": "123472f8-a1e7-4b99-8849-7a7186323203",
            "modifiable": False
          },
          "id": "123472f8-a1e7-4b99-8849-7a7186323203"
        }
      ]
    })

    # this should trigger the GET call we're expecting.
    card1 = g.get_card("mycard1")
    card2 = g.get_card("mycard2")

    self.assertEqual(card1.verifiers[0].type, "user")
    self.assertEqual(card1.verifiers[0].user.email, "jchappelle@getguru.com")

    self.assertEqual(card2.verifiers[0].type, "user-group")
    self.assertEqual(card2.verifiers[0].group.name, "Customer Experience")

  @use_guru()
  @responses.activate
  def test_get_card_and_check_card_info(self, g):
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/mycard/extended", json={
      "id": "aaaabbbb-cccc-dddd-eeee-ffffffffffff",
      "cardInfo": {
        "analytics": {
          "boards": 1,
          "copies": 5,
          "favorites": 2,
          "unverifiedCopies": 0,
          "unverifiedViews": 0,
          "views": 36,
        }
      }
    })

    card = g.get_card("mycard")

    self.assertEqual(card.copies, 5)
    self.assertEqual(card.views, 36)

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
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", json={
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
      "url": "https://api.getguru.com/api/v1/cards/1111/extended"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/cards/1111/comments",
      "body": {"content": "comment text"}
    }])
  
  @use_guru()
  @responses.activate
  def test_update_card_comment(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", json={
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
      "url": "https://api.getguru.com/api/v1/cards/1111/extended"
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
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", json={
      "id": "1111"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/2222/extended", json=None)

    card = g.get_card("1111")
    card.comment("")

    g.add_comment_to_card("2222", "test")
    g.get_card_comments("2222")
    g.delete_card_comment("2222", "3333")

  @use_guru()
  @responses.activate
  def test_delete_card_comment(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", json={
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
      "url": "https://api.getguru.com/api/v1/cards/1111/extended"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111/comments"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111/extended"
    }, {
      "method": "DELETE",
      "url": "https://api.getguru.com/api/v1/cards/1111/comments/2222"
    }])

  @use_guru()
  @responses.activate
  def test_archive_invalid_card(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", json=None, status=404)

    g.archive_card("1111")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111/extended"
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
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1234/extended", json={
      "id": "1234"
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/cards/1234", json={})

    card = g.get_card("1234")
    card.verification_interval = 90
    card.save()

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1234/extended"
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
        "verificationInterval": 90,
        "tags": []
      },
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
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/cards/1234", json={})

    card = g.get_card("1234")
    card.add_tag("tag1")
    card.add_tag("tag1")
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
      "id": "1234",
      "name": "category"
    }])

    card = g.get_card("1234")
    card.add_tag("tag1")
    
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1234/extended"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/whoami"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/teams/abcd/tagcategories"
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
  def test_find_archived_cards(self, g):
    responses.add(responses.POST, "https://api.getguru.com/api/v1/search/cardmgr", json=[])

    g.find_cards(archived=True)

    self.assertEqual(get_calls(), [{
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/search/cardmgr",
      "body": {
        "queryType": "archived",
        "sorts": None,
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
    responses.add(responses.POST, "https://api.getguru.com/api/v1/search/cardmgr", json=[])

    g.find_cards(tag="tag1")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/whoami"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/teams/abcd/tagcategories"
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
    responses.add(responses.POST, "https://api.getguru.com/api/v1/search/cardmgr", json=[{}])

    g.find_card(tag="tag1")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/whoami"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/teams/abcd/tagcategories"
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
    responses.add(responses.GET, "https://api.getguru.com/api/v1/whoami", json={
      "team": {
        "id": "abcd"
      }
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/teams/abcd/tagcategories", json=[{
      "tags": [],
      "id": "1234",
      "name": "category"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/search/cardmgr", json=[])

    g.find_cards(tag="tag1")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/whoami",
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/teams/abcd/tagcategories"
    }])
  
  @use_guru()
  def test_get_invalid_tag(self, g):
    self.assertIsNone(g.get_tag(""))

  @use_guru()
  @responses.activate
  def test_verify_card(self, g):
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1234/extended", json={
      "id": "1234"
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/cards/1234/verify", json={})

    # this should trigger the GET call we're expecting.
    card = g.get_card("1234")
    result = card.verify()

    # assert that the only API activity was the one call we expected to see.
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1234/extended"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/cards/1234/verify"
    }])
    self.assertEqual(result, True)

  @use_guru()
  @responses.activate
  def test_unverify_card(self, g):
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1234/extended", json={
      "id": "1234"
    })
    responses.add(responses.POST, "https://api.getguru.com/api/v1/cards/1234/unverify", json={})

    # this should trigger the GET call we're expecting.
    card = g.get_card("1234")
    result = card.unverify()

    # assert that the only API activity was the one call we expected to see.
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1234/extended"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/cards/1234/unverify"
    }])
    self.assertEqual(result, True)
  
  @use_guru()
  @responses.activate
  def test_favorite_card(self, g):
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/favoritelists", json=[{
      "id": "1111"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1234/extended", json={
      "id": "1234"
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/favoritelists/1111/entries", json={})

    card = g.get_card("1234")
    result = card.favorite()

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1234/extended"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/favoritelists"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/favoritelists/1111/entries",
      "body": {
        "prevSiblingItem": "last",
        "actionType": "add",
        "boardEntries": [{
          "cardId": "1234",
          "entryType": "card"
        }]
      }
    }])
    self.assertEqual(result, True)

  @use_guru()
  @responses.activate
  def test_unfavorite_card(self, g):
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1234/extended", json={
      "id": "1234"
    })
    responses.add(responses.DELETE, "https://api.getguru.com/api/v1/cards/1234/favorite", json={})

    card = g.get_card("1234")
    result = card.unfavorite()

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1234/extended"
    }, {
      "method": "DELETE",
      "url": "https://api.getguru.com/api/v1/cards/1234/favorite"
    }])
    self.assertEqual(result, True)

  @use_guru()
  @responses.activate
  def test_favorite_invalid_card(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", json=None, status=404)
    responses.add(responses.GET, "https://api.getguru.com/api/v1/favoritelists", json=[{
      "id": "1234"
    }])

    g.favorite_card("1111")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/favoritelists"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111/extended"
    }])

  @use_guru()
  @responses.activate
  def test_favorite_card_list_error(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/favoritelists", json=[])

    g.favorite_card("1111")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/favoritelists"
    }])

  @use_guru()
  @responses.activate
  def test_unfavorite_invalid_card(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", json=None, status=404)
    
    g.unfavorite_card("1111")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111/extended"
    }])

  @use_guru()
  @responses.activate
  def test_patch_card(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1234/extended", json={
      "id": "1234"
    })
    responses.add(responses.PATCH, "https://api.getguru.com/api/v1/cards/1234?keepVerificationState=true", json={})

    card = g.get_card("1234")
    card.verification_interval = 90
    card.title = "test"
    card.patch()

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1234/extended"
    }, {
      "method": "PATCH",
      "url": "https://api.getguru.com/api/v1/cards/1234?keepVerificationState=true",
      "body": {
        "content": "",
        "preferredPhrase": "test",
        "verificationInterval": 90
      },
    }])

  @use_guru()
  @responses.activate
  def test_get_card_version(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1234/extended", json={
      "id": "1234",
      "version": 2,
      "content": "version 2"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1234/versions/1", json={
      "id": "1234",
      "version": 1,
      "content": "version 1"
    })

    card = g.get_card("1234")
    card_v1 = g.get_card_version(card, 1)

    self.assertEqual(card.content, "version 2")
    self.assertEqual(card_v1.content, "version 1")
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1234/extended"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1234/versions/1"
    }])

  @use_guru()
  @responses.activate
  def test_get_card_version_with_invalid_card(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1234/extended", status=404)

    card = g.get_card_version("1234", 1)

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1234/extended"
    }])

  @use_guru()
  @responses.activate
  def test_get_card_version_with_invalid_version(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1234/extended", json={
      "id": "1234"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1234/versions/3", status=404, json={
      "description" : "HTTP 404 Not Found"
    })

    card = g.get_card("1234")
    card_v3 = g.get_card_version(card, 3)

    self.assertEqual(card.id, "1234")
    self.assertEqual(card_v3, None)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1234/extended"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1234/versions/3"
    }])
