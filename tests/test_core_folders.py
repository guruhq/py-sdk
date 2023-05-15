
import json
import yaml
import time
import unittest
import responses

from unittest.mock import Mock, patch

from tests.util import use_guru, get_calls

import guru


class TestCore(unittest.TestCase):
  @use_guru()
  @responses.activate
  def test_get_folders(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders", json=[{
        "id": "1234",
        "title": "test folder"
    }, {
        "id": "5678",
        "title": "another test folder"
    }])

    folders = g.get_folders()

    self.assertEqual(len(folders), 2)

    self.assertEqual(get_calls(), [{
        "method": "GET",
        "url": "https://api.getguru.com/api/v1/folders"
    }])

  @use_guru()
  @responses.activate
  def test_get_folder(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/1234", json=[{
        "id": "1234",
        "title": "test"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/1234/items", json=[{
        "type": "folder",
        "title": "subfolder1"
    },
        {
        "type": "folder",
        "title": "subfolder2"
    },
        {
        "type": "card",
        "title": "card1"
    }])

    folder = g.get_folder("1234")

    self.assertEqual(len(folder.folders), 2)
    self.assertEqual(len(folder.cards), 2)
    self.assertEqual(len(folder.items), 3)

    self.assertEqual(get_calls(), [{
        "method": "GET",
        "url": "https://api.getguru.com/api/v1/folders"
    }, {
        "method": "GET",
        "url": "https://api.getguru.com/api/v1/boards/folders"
    }])

    @use_guru()
    @responses.activate
    def test_add_folder(self, g):
      responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
          "id": "1234",
          "name": "General"
      }])
      responses.add(
          responses.POST, "https://api.getguru.com/api/v1/folder/1234/action", json=[])
      responses.add(responses.GET, "https://api.getguru.com/api/v1/folders?collection=1234", json=[{
          "id": "1111",
          "title": "New Board"
      }])
      responses.add(
          responses.GET, "https://api.getguru.com/api/v1/folder/1111", json={})

      result = g.make_board(
          "New Board", collection="General", description="test")

      self.assertEqual(get_calls(), [{
          "method": "GET",
          "url": "https://api.getguru.com/api/v1/collections"
      }, {
          "method": "POST",
          "url": "https://api.getguru.com/api/v1/folders/action",
          "body": {
              "actionType": "add",
              "boardEntries": [{
                  "entryType": "board",
                  "title": "New Board",
                  "description": "test"
              }]
          }
      }, {
          "method": "GET",
          "url": "https://api.getguru.com/api/v1/folders?collection=1234"
      }, {
          "method": "GET",
          "url": "https://api.getguru.com/api/v1/folder/1111"
      }])
