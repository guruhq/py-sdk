
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
  def test_get_board(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards", json=[{
      "id": "1234",
      "title": "test"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/1234", json={
      "items": [{
        "type": "section",
        "title": "test",
        "items": [{
          "type": "fact"
        }]
      }, {
        "type": "fact"
      }]
    })

    board = g.get_board("test")

    self.assertEqual(len(board.items), 2)
    self.assertEqual(len(board.cards), 2)
    self.assertEqual(len(board.sections), 1)
    self.assertEqual(len(board.all_items), 3)

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/1234"
    }])

  @use_guru()
  @responses.activate
  def test_get_board_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/home?collection=1234", json={
      "collection": {
        "id": "1234"
      },
      "items": [{
        "type": "section",
        "title": "A",
        "items": [],
      }, {
        "type": "section",
        "title": "My Board Group",
        "items": [{
          "type": "board"
        }]
      }, {
        "type": "board"
      }]
    })

    g.get_board_group("my board group", "General")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/home?collection=1234"
    }])

  @use_guru()
  @responses.activate
  def test_get_home_board(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/home?collection=1234", json={
      "collection": {
        "id": "1234"
      },
      "items": [{
        "type": "section",
        "items": [{
          "type": "board"
        }]
      }, {
        "type": "board"
      }]
    })

    g.get_home_board("General")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/home?collection=1234"
    }])

  @use_guru()
  @responses.activate
  def test_get_home_board_by_invalid_collection(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/home?collection=1234", json={})

    g.get_home_board("General")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }])

  @use_guru()
  @responses.activate
  def test_set_home_board_item_order(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/home?collection=1234", json={
      "id": "home",
      "collection": {
        "id": "1234"
      },
      "items": [{
        "id": "1",
        "itemId": "i1",
        "type": "board",
        "title": "Board A"
      }, {
        "id": "2",
        "itemId": "i2",
        "type": "section",
        "title": "Board Group",
        "items": [{
          "type": "board"
        }]
      }, {
        "id": "3",
        "itemId": "i3",
        "type": "board",
        "title": "Board B"
      }]
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/boards/home", json={})

    home_board = g.get_home_board("General")
    home_board.set_item_order("Board B", "Board A", "Board Group")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/home?collection=1234"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/boards/home",
      "body": {
        "id": "home",
        "collection": {"id": "1234", "name": None, "type": None, "color": None},
        "items": [
          {"id": "3", "type": "board", "itemId": "i3", "title": "Board B"},
          {"id": "1", "type": "board", "itemId": "i1", "title": "Board A"},
          {"id": "2", "type": "section", "itemId": "i2", "title": "Board Group", "items": [
            {"id": None, "type": "board", "itemId": None, "title": None}
          ]}
        ]
      }
    }])
  
  @use_guru()
  @responses.activate
  def test_set_board_item_order(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards", json=[{
      "id": "1234",
      "title": "test"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/1234", json={
      "id": "1234",
      "collection": {
        "id": "abcd",
        "name": "General"
      },
      "items": [{
        "id": "1",
        "itemId": "i1",
        "type": "section",
        "title": "test",
        "items": [{
          "id": "2",
          "itemId": "i2",
          "title": "card 1",
          "type": "fact"
        }, {
          "id": "3",
          "itemId": "i3",
          "title": "card 2",
          "type": "fact"
        }]
      }, {
        "id": "4",
        "itemId": "i4",
        "title": "card 3",
        "type": "fact"
      }]
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/boards/1234", json={})

    board = g.get_board("test")
    board.set_item_order("card 3", "test")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/1234"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/boards/1234",
      "body": {
        "id": "1234", "type": "board", "itemId": None, "title": None,
        "collection": {"id": "abcd", "name": "General", "type": None, "color": None},
        "items": [
          {"type": "section", "id": "1", "itemId": "i1", "items": [
            {"type": "fact", "id": "2", "itemId": "i2"},
            {"type": "fact", "id": "3", "itemId": "i3"}
          ]},
          {"type": "fact", "id": "4", "itemId": "i4"}
        ]
      }
    }])
  
  @use_guru()
  @responses.activate
  def test_set_board_group_item_order(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/home?collection=1234", json={
      "id": "home",
      "collection": {
        "id": "1234"
      },
      "items": [{
        "type": "section",
        "title": "A",
        "items": [],
      }, {
        "type": "section",
        "title": "My Board Group",
        "items": [{
          "type": "board",
          "id": "1",
          "itemId": "i1",
          "title": "Board A"
        }, {
          "type": "board",
          "id": "2",
          "itemId": "i2",
          "title": "Board B"
        }, {
          "type": "board",
          "id": "3",
          "itemId": "i3",
          "title": "Board C"
        }]
      }, {
        "type": "board"
      }]
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/boards/home", json={})

    board_group = g.get_board_group("my board group", "General")
    board_group.set_item_order("board c", "board b", "board a")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/home?collection=1234"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/boards/home",
      "body": {
        "id": "home",
        "collection": {"id": "1234", "name": None, "type": None, "color": None},
        "items": [
          {"id": None, "type": "section", "itemId": None, "title": "A", "items": []},
          {
            # this is the board group we edited:
            "id": None,
            "type": "section",
            "itemId": None,
            "title": "My Board Group",
            "items": [
              {"id": "3", "type": "board", "itemId": "i3", "title": "Board C"},
              {"id": "2", "type": "board", "itemId": "i2", "title": "Board B"},
              {"id": "1", "type": "board", "itemId": "i1", "title": "Board A"}
            ]
          },
          {"id": None, "type": "board", "itemId": None, "title": None}
        ]
      }
    }])

  @use_guru()
  @responses.activate
  def test_set_item_order_with_invalid_collection(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])
    g.set_item_order("invalid", "My Board", "a", "b", "c")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }])
  
  @use_guru()
  @responses.activate
  def test_set_item_order_with_invalid_board(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/invalid", status=404)
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards?collection=1234", json=[{
      "id": "abcd",
      "title": "Board A",
    }, {
      "id": "efgh",
      "title": "Board B"
    }])

    g.set_item_order("General", "invalid", "a", "b", "c")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/invalid"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections",
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards?collection=1234"
    }])

  @use_guru()
  @responses.activate
  def test_make_board_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/home?collection=1234", json={
      "collection": {
        "id": "1234"
      },
      "items": [{
        "type": "section",
        "title": "A",
        "items": [],
      }, {
        "type": "section",
        "title": "My Board Group",
        "items": [{
          "type": "board"
        }]
      }, {
        "type": "board"
      }]
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/boards/home/entries?collection=1234", json={})

    g.make_board_group("General", "my board group", "desc...")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/boards/home/entries?collection=1234",
      "body": {
        "actionType": "add",
        "boardEntries": [{
          "description": "desc...",
          "entryType": "section",
          "title": "my board group"
        }]
      }
    }])
  
  @use_guru()
  @responses.activate
  def test_add_card_to_board(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111", json={
      "id": "1111"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222", json={
      "id": "22222222-2222-2222-2222-222222222222",
      "title": "my board",
      "items": []
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222", json={})

    g.add_card_to_board("1111", "22222222-2222-2222-2222-222222222222")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222",
      "body": {
        "id": "22222222-2222-2222-2222-222222222222",
        "itemId": None,
        "items": [{
          "id": "1111",
          "itemId": None,
          "type": "fact"
        }],
        "title": "my board",
        "type": "board"
      }
    }])

  @use_guru()
  @responses.activate
  def test_add_card_to_board_by_board_name(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111", json={
      "id": "1111"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards", json=[{
      "id": "2222",
      "title": "my board"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/2222", json={
      "id": "2222",
      "title": "my board",
      "items": []
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/boards/2222", json={})

    g.add_card_to_board("1111", "my board")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/2222"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/boards/2222",
      "body": {
        "id": "2222",
        "itemId": None,
        "items": [{
          "id": "1111",
          "itemId": None,
          "type": "fact"
        }],
        "title": "my board",
        "type": "board"
      }
    }])
  
  @use_guru()
  @responses.activate
  def test_add_card_to_board_by_board_slug(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111", json={
      "id": "1111"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/abcde", json={
      "id": "2222",
      "slug": "abcde/my-board",
      "title": "my board"
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/boards/2222", json={})

    g.add_card_to_board("1111", "abcde")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/abcde"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/boards/2222",
      "body": {
        "id": "2222",
        "itemId": None,
        "items": [{
          "id": "1111",
          "itemId": None,
          "type": "fact"
        }],
        "title": "my board",
        "type": "board"
      }
    }])

  @use_guru()
  @responses.activate
  def test_add_card_to_invalid_board(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111", json={
      "id": "1111"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards", json=[{
      "id": "2222",
      "title": "my board"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/2222", json={
      "id": "2222",
      "title": "my board",
      "items": []
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/boards/2222", json={})

    g.add_card_to_board("1111", "no match")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards"
    }])

  @use_guru()
  @responses.activate
  def test_add_invalid_card_to_board(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111", status=404)
    
    g.add_card_to_board("1111", "2222")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111"
    }])

  @use_guru()
  @responses.activate
  def test_add_card_to_board_and_existing_section(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111", json={
      "id": "1111"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222", json={
      "id": "22222222-2222-2222-2222-222222222222",
      "title": "my board",
      "items": [{
        "type": "section",
        "title": "section 8",
        "id": "3333"
      }]
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222", json={})

    g.add_card_to_board("1111", "22222222-2222-2222-2222-222222222222", "section 8")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222",
      "body": {
        "id": "22222222-2222-2222-2222-222222222222",
        "type": "board",
        "itemId": None,
        "title": "my board",
        "items": [{
          "type": "section",
          "id": "3333",
          "itemId": None,
          "items": [{
            "type": "fact",
            "id": "1111", 
            "itemId": None
          }]
        }]
      }
    }])

  @use_guru()
  @responses.activate
  def test_add_card_to_board_and_invalid_section(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111", json={
      "id": "1111"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222", json={
      "id": "22222222-2222-2222-2222-222222222222",
      "title": "my board",
      "items": []
    })
    # responses.add(responses.PUT, "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222", json={})

    g.add_card_to_board("1111", "22222222-2222-2222-2222-222222222222", "section 8")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222"
    }])
  
  @use_guru()
  @responses.activate
  def test_add_card_to_board_and_new_section(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111", json={
      "id": "1111"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222", json={
      "id": "22222222-2222-2222-2222-222222222222",
      "title": "my board",
      "items": []
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222/entries", status=204)
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222", json={
      "id": "22222222-2222-2222-2222-222222222222",
      "title": "my board",
      "items": [{
        "type": "section",
        "title": "section 8",
        "id": "3333"
      }]
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222", json={})

    g.add_card_to_board("1111", "22222222-2222-2222-2222-222222222222", "section 8", create_section_if_needed=True)

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222/entries",
      "body": {
        "actionType": "add",
        "boardEntries": [{
          "entryType": "section",
          "title": "section 8"
        }]
      }
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222",
      "body": {
        "id": "22222222-2222-2222-2222-222222222222",
        "type": "board",
        "itemId": None,
        "title": "my board",
        "items": [{
          "type": "section",
          "id": "3333",
          "itemId": None,
          "items": [{
            "type": "fact",
            "id": "1111",
            "itemId": None
          }]
        }]
      }
    }])
  
  @use_guru()
  @responses.activate
  def test_remove_card_from_board_by_card_id(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222", json={
      "id": "22222222-2222-2222-2222-222222222222",
      "title": "my board",
      "collection": {
        "id": "3333"
      },
      "items": [{
        "type": "fact",
        "id": "1111",
        "title": "my card"
      }]
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222/entries", json={})
    
    g.remove_card_from_board("1111", "22222222-2222-2222-2222-222222222222")
    
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222/entries",
      "body": {
        "actionType": "remove",
        "collectionId": "3333",
        "id": "22222222-2222-2222-2222-222222222222",
        "boardEntries": [{
          "entryType": "card",
          "id": None
        }]
      }
    }])
  
  @use_guru()
  @responses.activate
  def test_remove_card_from_board_with_invalid_card(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222", json={
      "id": "22222222-2222-2222-2222-222222222222",
      "title": "my board",
      "collection": {
        "id": "3333"
      },
      "items": [{
        "type": "fact",
        "id": "1111",
        "title": "my card"
      }]
    })
    
    g.remove_card_from_board("invalid", "22222222-2222-2222-2222-222222222222")
    
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222"
    }])

  @use_guru()
  @responses.activate
  def test_remove_card_from_board_with_invalid_board(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222", status=404)
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards", json=[])
    
    g.remove_card_from_board("1111", "22222222-2222-2222-2222-222222222222")
    
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/22222222-2222-2222-2222-222222222222"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards"
    }])
  
  @use_guru()
  @responses.activate
  def test_get_board_permissions(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/11111111-1111-1111-1111-111111111111", json={
      "id": "11111111-1111-1111-1111-111111111111",
      "items": []
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/11111111-1111-1111-1111-111111111111/permissions", json=[{
      "id": "1234",
      "group": {
        "id": "1111",
        "name": "Experts"
      }
    }])

    board = g.get_board("11111111-1111-1111-1111-111111111111")
    
    groups = board.get_groups()
    self.assertEqual(groups[0].id, "1234")
    self.assertEqual(groups[0].group.id, "1111")
    self.assertEqual(groups[0].group.name, "Experts")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/11111111-1111-1111-1111-111111111111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/11111111-1111-1111-1111-111111111111/permissions"
    }])
  
  @use_guru()
  @responses.activate
  def test_add_board_permission(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/11111111-1111-1111-1111-111111111111", json={
      "id": "11111111-1111-1111-1111-111111111111",
      "items": []
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1111",
      "name": "Experts"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/boards/11111111-1111-1111-1111-111111111111/permissions")

    board = g.get_board("11111111-1111-1111-1111-111111111111")
    board.add_group("Experts")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/11111111-1111-1111-1111-111111111111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/boards/11111111-1111-1111-1111-111111111111/permissions",
      "body": [{
        "type": "group",
        "role": "MEMBER",
        "group": {
          "id": "1111"
        }
      }]
    }])
  
  @use_guru()
  @responses.activate
  def test_remove_board_permission(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/11111111-1111-1111-1111-111111111111", json={
      "id": "11111111-1111-1111-1111-111111111111",
      "items": []
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/11111111-1111-1111-1111-111111111111/permissions", json=[{
      "id": "1234",
      "group": {
        "id": "1111",
        "name": "Experts"
      }
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1111",
      "name": "Experts"
    }])
    responses.add(responses.DELETE, "https://api.getguru.com/api/v1/boards/11111111-1111-1111-1111-111111111111/permissions/1234", status=204)

    board = g.get_board("11111111-1111-1111-1111-111111111111")
    result = board.remove_group("Experts")

    self.assertEqual(result, True)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/11111111-1111-1111-1111-111111111111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/11111111-1111-1111-1111-111111111111/permissions"
    }, {
      "method": "DELETE",
      "url": "https://api.getguru.com/api/v1/boards/11111111-1111-1111-1111-111111111111/permissions/1234"
    }])
  
  @use_guru()
  @responses.activate
  def test_get_board_permissions_with_invalid_board(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards", json=[{
      "id": "1234",
      "title": "test"
    }])

    result = g.get_shared_groups("my board")
    
    self.assertEqual(result, None)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards"
    }])
  
  @use_guru()
  @responses.activate
  def test_add_board_permission_with_invalid_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/11111111-1111-1111-1111-111111111111", json={
      "id": "11111111-1111-1111-1111-111111111111",
      "items": []
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[])

    board = g.get_board("11111111-1111-1111-1111-111111111111")
    board.add_group("Experts")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/11111111-1111-1111-1111-111111111111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }])
  
  @use_guru()
  @responses.activate
  def test_add_board_permission_with_invalid_board(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards", json=[])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1111",
      "name": "Experts"
    }])

    result = g.add_shared_group("my board", "Experts")

    self.assertEqual(result, None)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards"
    }])
  
  @use_guru()
  @responses.activate
  def test_remove_board_permission_with_invalid_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1111",
      "name": "other group"
    }])
    
    result = g.remove_shared_group("my board", "Experts")

    self.assertEqual(result, None)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }])
  
  @use_guru()
  @responses.activate
  def test_remove_board_permission_with_invalid_board(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1111",
      "name": "Experts"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards", json=[])
    
    result = g.remove_shared_group("my board", "Experts")

    self.assertEqual(result, None)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards"
    }])
  
  @use_guru()
  @responses.activate
  def test_remove_board_permission_with_unshared_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/11111111-1111-1111-1111-111111111111", json={
      "id": "11111111-1111-1111-1111-111111111111",
      "items": []
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards/11111111-1111-1111-1111-111111111111/permissions", json=[{
      "id": "1234",
      "group": {
        "id": "1111",
        "name": "Experts"
      }
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "2222",
      "name": "other group"
    }])

    board = g.get_board("11111111-1111-1111-1111-111111111111")
    result = board.remove_group("other group")

    self.assertEqual(result, None)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/11111111-1111-1111-1111-111111111111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards/11111111-1111-1111-1111-111111111111/permissions"
    }])