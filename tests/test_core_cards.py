
import json
import yaml
import unittest
import responses

from unittest.mock import Mock, patch

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

    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/mycard3/extended", json={
      "verifiers": []
    })

    # this should trigger the GET call we're expecting.
    card1 = g.get_card("mycard1")
    card2 = g.get_card("mycard2")
    card3 = g.get_card("mycard3")

    self.assertEqual(card1.verifiers[0].type, "user")
    self.assertEqual(card1.verifiers[0].user.email, "jchappelle@getguru.com")
    self.assertEqual(card1.verifier_label, "jchappelle@getguru.com")

    self.assertEqual(card2.verifiers[0].type, "user-group")
    self.assertEqual(card2.verifiers[0].group.name, "Customer Experience")
    self.assertEqual(card2.verifier_label, "Customer Experience")

    self.assertEqual(card3.verifier_label, "no verifier")

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
    card.add_comment("")

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
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111", json=None, status=404)

    g.archive_card("1111")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111/extended"
    }])

  @use_guru()
  @responses.activate
  def test_restore_card(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", status=404)
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111", json={
      "id": "1111"
    })
    responses.add(responses.POST, "https://api.getguru.com/api/v1/cards/bulkop", status=200)

    g.get_card("1111", is_archived=True).restore()

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111/extended"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/cards/bulkop",
      "body": {
        "action": {
          "type": "restore-archived-card"
        },
        "items": {
          "type": "id",
          "cardIds": ["1111"]
        }
      }
    }])

  @use_guru()
  @responses.activate
  def test_restore_invalid_card(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", status=404)
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111", status=404)

    result = g.restore_card("1111")

    self.assertEqual(result, False)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111/extended"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111"
    }])

  @use_guru()
  @responses.activate
  def test_restore_cards_and_wait(self, g):
    responses.add(responses.POST, "https://api.getguru.com/api/v1/cards/bulkop", json={
      "id": "2222"
    }, status=202)
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/bulkop/2222", json={})

    with patch("time.sleep", Mock(return_value=None)):
      g.restore_cards("1111", "2222", timeout=1)
    
    self.assertEqual(get_calls(), [{
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/cards/bulkop",
      "body": {
        "action": {
          "type": "restore-archived-card"
        },
        "items": {
          "type": "id",
          "cardIds": ["1111", "2222"]
        }
      }
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/bulkop/2222"
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
  def test_find_verified_or_unverified_cards(self, g):
    responses.add(responses.POST, "https://api.getguru.com/api/v1/search/cardmgr", json=[])

    # these two are equivalent.
    g.find_cards(verified=True)
    g.find_cards(unverified=False)

    # these two are equivalent.
    g.find_cards(verified=False)
    g.find_cards(unverified=True)

    # these are contradictory so no filtering is done.
    g.find_cards(verified=True, unverified=True)
    g.find_cards(verified=False, unverified=False)

    post_body_verified = {
      "queryType": None,
      "sorts": [{
        "type": "verificationState",
        "dir": "ASC"
      }],
      "query": {
        "nestedExpressions": [{
          "type": "trust-state",
          "verificationState": "TRUSTED",
          "op": "EQ"
        }],
        "op": "AND",
        "type": "grouping"
      },
      "collectionIds": []
    }

    post_body_unverified = {
      "queryType": None,
      "sorts": [{
        "type": "verificationState",
        "dir": "ASC"
      }],
      "query": {
        "nestedExpressions": [{
          "type": "trust-state",
          "verificationState": "NEEDS_VERIFICATION",
          "op": "EQ"
        }],
        "op": "AND",
        "type": "grouping"
      },
      "collectionIds": []
    }

    post_body_no_filter = {
      "queryType": None,
      "sorts": [{
        "type": "verificationState",
        "dir": "ASC"
      }],
      "query": None,
      "collectionIds": []
    }

    self.assertEqual(get_calls(), [{
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/search/cardmgr",
      "body": post_body_verified
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/search/cardmgr",
      "body": post_body_verified
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/search/cardmgr",
      "body": post_body_unverified
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/search/cardmgr",
      "body": post_body_unverified
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/search/cardmgr",
      "body": post_body_no_filter
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/search/cardmgr",
      "body": post_body_no_filter
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
  def test_find_cards_created_in_date_range(self, g):
    responses.add(responses.POST, "https://api.getguru.com/api/v1/search/cardmgr", json=[])

    g.find_cards(
      created_after="2021-03-01",
      created_before="2021-03-15"
    )

    self.assertEqual(get_calls(), [{
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
            "type": "absolute-date",
            "value": "2021-03-15T00:00:00-00:00",
            "op": "LT",
            "field": "DATECREATED"
          }, {
            "type": "absolute-date",
            "value": "2021-03-01T00:00:00-00:00",
            "op": "GTE",
            "field": "DATECREATED"
          }],
          "op": "AND",
          "type": "grouping"
        },
        "collectionIds": []
      }
    }])

  @use_guru()
  @responses.activate
  def test_find_cards_by_last_modified(self, g):
    responses.add(responses.POST, "https://api.getguru.com/api/v1/search/cardmgr", json=[])

    g.find_cards(
      last_modified_by="user@example.com",
      last_modified_after="2021-03-01",
      last_modified_before="2021-03-15"
    )

    self.assertEqual(get_calls(), [{
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
            "type": "absolute-date",
            "value": "2021-03-15T00:00:00-00:00",
            "op": "LT",
            "field": "LASTMODIFIED"
          }, {
            "type": "absolute-date",
            "value": "2021-03-01T00:00:00-00:00",
            "op": "GTE",
            "field": "LASTMODIFIED"
          }, {
            "type": "last-modified-by",
            "email": "user@example.com",
            "op": "EQ"
          }],
          "op": "AND",
          "type": "grouping"
        },
        "collectionIds": []
      }
    }])

  @use_guru()
  @responses.activate
  def test_find_cards_with_multiple_filters(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/search/cardmgr", json=[])

    g.find_cards(collection="General", title="test", author="user@example.com", verified=True)

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
        "query": {
          "nestedExpressions": [{
            "type": "title",
            "value": "test",
            "op": "CONTAINS"
          }, {
            "type": "originalOwner",
            "email": "user@example.com",
            "op": "EQ"
          }, {
            "type": "trust-state",
            "verificationState": "TRUSTED",
            "op": "EQ"
          }],
          "op": "AND",
          "type": "grouping"
        },
        "collectionIds": ["1234"]
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

  @use_guru()
  @responses.activate
  def test_card_has_text(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1234/extended", json={
      "id": "1234",
      "content": """<p class="p">here's a guru <a href="url">link</a> in the card's content.</p>""",
      "preferredPhrase": "has_text test card title"
    })

    card = g.get_card("1234")

    # the word "content" is found only in the content and "title" is found only in its title.
    self.assertEqual(card.has_text("content", case_sensitive=False, include_title=False), True)
    self.assertEqual(card.has_text("title", case_sensitive=False, include_title=False), False)

    # test case sensitivity and including the title.
    self.assertEqual(card.has_text("CONTENT", case_sensitive=True, include_title=False), False)
    self.assertEqual(card.has_text("content", case_sensitive=True, include_title=False), True)
    self.assertEqual(card.has_text("TITLE", case_sensitive=True, include_title=True), False)
    self.assertEqual(card.has_text("title", case_sensitive=True, include_title=True), True)

    # test words that cross html tag boundaries.
    self.assertEqual(card.has_text("guru link", case_sensitive=False), True)

    # check for html attributes.
    self.assertEqual(card.has_text("class", case_sensitive=False), False)
    self.assertEqual(card.has_text("href", case_sensitive=False), False)

  @use_guru()
  @responses.activate
  def test_get_visible_cards(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/search/visible", headers={
      "x-guru-total-cards": "1234"
    })

    card_count = g.get_visible_cards()

    self.assertEqual(card_count, 1234)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/search/visible"
    }])

  @use_guru()
  @responses.activate
  def test_find_urls(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", json={
      "content": """<p>
  this paragraph has a <a href="https://www.example.com/link">link</a>.
</p>
<p>
  this paragraph has an image: <img src="http://www.example.com/image.png" /> and here's an iframe:
</p>
<p>
  <iframe src="https://www.example.com/embed"></iframe>
</p>"""
    })

    # test with a card that has a guru markdown block.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/2222/extended", json={
      "content": """<p>
  this card has a <a href="https://help.getguru.com/en/articles/4681211-using-markdown-in-guru-cards">guru markdown block</a>.
</p>
<p class="ghq-card-content__paragraph" data-ghq-card-content-type="paragraph">test</p><div class="ghq-card-content__markdown" data-ghq-card-content-type="MARKDOWN" data-ghq-card-content-markdown-content="this%20has%20a%20%5Bmarkdown%20link%5D%28https%3A//www.example.com/link1%29%20and%20an%20image%3A%0A%0A%21%5B%5D%28https%3A//www.example.com/image1.png%29%0A%0Ait%20also%20has%20inline%20html%20for%20a%20%3Ca%20href%3D%22https%3A//www.example.com/link2%22%3Elink%3C/a%3E%20and%20image%3A%0A%0A%3Cimg%20src%3D%22https%3A//www.example.com/image2.png%22%20/%3E"><p>this has a <a href="https://www.example.com/link1" target="_blank" rel="noopener noreferrer">markdown link</a> and an image:</p><p><img src="https://www.example.com/image1.png" alt=""></p><p>it also has inline html for a <a href="https://www.example.com/link2" target="_blank" rel="noopener noreferrer">link</a> and image:</p><img src="https://www.example.com/image2.png"></div>
"""
    })

    # test with a card whose content is entirely markdown.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/3333/extended", json={
      "content": """## test

this card's content is entirely [markdown](https://guides.github.com/features/mastering-markdown/).

1. test
2. numbered
3. list

here's an image:
![](https://pp.getguru.com/a4211b79b48446f589b8e0e53fc067d7.jpeg)"""
    })

    normal_card = g.get_card("1111")
    card_with_markdown = g.get_card("2222")
    markdown_card = g.get_card("3333")

    # we sort the urls because the elements and links aren't always enumerated in DOM order.
    self.assertEqual(sorted(normal_card.find_urls()), [
      "http://www.example.com/image.png",
      "https://www.example.com/embed",
      "https://www.example.com/link"
    ])

    self.assertEqual(sorted(card_with_markdown.find_urls()), [
      "https://help.getguru.com/en/articles/4681211-using-markdown-in-guru-cards",
      "https://www.example.com/image1.png",
      "https://www.example.com/image2.png",
      "https://www.example.com/link1",
      "https://www.example.com/link2"
    ])

    self.assertEqual(sorted(markdown_card.find_urls()), [
      "https://guides.github.com/features/mastering-markdown/",
      "https://pp.getguru.com/a4211b79b48446f589b8e0e53fc067d7.jpeg"
    ])

  @use_guru()
  @responses.activate
  def test_replace_url(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", json={
    "content": """<p>
this card has a <a href="https://help.getguru.com/en/articles/4681211-using-markdown-in-guru-cards">guru markdown block</a>.
</p>
<p class="ghq-card-content__paragraph" data-ghq-card-content-type="paragraph">test</p><div class="ghq-card-content__markdown" data-ghq-card-content-type="MARKDOWN" data-ghq-card-content-markdown-content="this%20has%20a%20%5Bmarkdown%20link%5D%28https%3A//www.example.com/link1%29%20and%20an%20image%3A%0A%0A%21%5B%5D%28https%3A//www.example.com/image1.png%29%0A%0Ait%20also%20has%20inline%20html%20for%20a%20%3Ca%20href%3D%22https%3A//www.example.com/link2%22%3Elink%3C/a%3E%20and%20image%3A%0A%0A%3Cimg%20src%3D%22https%3A//www.example.com/image2.png%22%20/%3E"><p>this has a <a href="https://www.example.com/link1" target="_blank" rel="noopener noreferrer">markdown link</a> and an image:</p><p><img src="https://www.example.com/image1.png" alt=""></p><p>it also has inline html for a <a href="https://www.example.com/link2" target="_blank" rel="noopener noreferrer">link</a> and image:</p><img src="https://www.example.com/image2.png"></div>
"""
    })

    card = g.get_card("1111")
    result1 = card.replace_url("https://help.getguru.com/en/articles/4681211-using-markdown-in-guru-cards", "https://www.example.com")
    card.replace_url("https://www.example.com/link1", "https://www.example.com/new-link")
    result2 = card.replace_url("https://help.getguru.com/en/articles/4681211-using-markdown-in-guru-cards", "https://www.example.com")
    self.assertEqual(result1, True)
    self.assertEqual(result2, False)
    self.assertEqual(card.content, """<p>
this card has a <a href="https://www.example.com">guru markdown block</a>.
</p>
<p class="ghq-card-content__paragraph" data-ghq-card-content-type="paragraph">test</p><div class="ghq-card-content__markdown" data-ghq-card-content-type="MARKDOWN" data-ghq-card-content-markdown-content="this%20has%20a%20%5Bmarkdown%20link%5D%28https%3A//www.example.com/new-link%29%20and%20an%20image%3A%0A%0A%21%5B%5D%28https%3A//www.example.com/image1.png%29%0A%0Ait%20also%20has%20inline%20html%20for%20a%20%3Ca%20href%3D%22https%3A//www.example.com/link2%22%3Elink%3C/a%3E%20and%20image%3A%0A%0A%3Cimg%20src%3D%22https%3A//www.example.com/image2.png%22%20/%3E"><p>this has a <a href="https://www.example.com/new-link" target="_blank" rel="noopener noreferrer">markdown link</a> and an image:</p><p><img src="https://www.example.com/image1.png" alt=""></p><p>it also has inline html for a <a href="https://www.example.com/link2" target="_blank" rel="noopener noreferrer">link</a> and image:</p><img src="https://www.example.com/image2.png"></div>
""")
