
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

    g.get_board("test")

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
    responses.add(responses.GET, "https://api.getguru.com/api/v1/boards", json=[{
      "id": "abcd",
      "title": "Board A",
    }, {
      "id": "efgh",
      "title": "Board B"
    }])

    g.set_item_order("General", "invalid", "a", "b", "c")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/boards"
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