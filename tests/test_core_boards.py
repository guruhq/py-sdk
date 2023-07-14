
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
  def test_get_folder(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders", json=[{
      "id": "1234",
      "title": "test"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/1234", json={
      "items": [{
        "type": "section",
        "title": "test",
        "items": [{
          "type": "fact",
          "preferredPhrase": "card 1"
        }]
      }, {
        "type": "fact",
        "preferredPhrase": "card 2"
      }]
    })

    folder = g.get_folder("test")

    self.assertEqual(len(folder.items), 2)
    self.assertEqual(len(folder.cards), 2)
    self.assertEqual(len(folder.sections), 1)
    self.assertEqual(len(folder.all_items), 3)

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/1234"
    }])

  @use_guru()
  @responses.activate
  def test_get_folder_with_duplicate_name(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1111",
      "name": "Engineering"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/home?collection=1111", json={
      "collection": {
        "id": "1111"
      },
      "items": [{
        "type": "folder",
        "title": "My Folder",
        "id": "2222"
      }, {
        "type": "section",
        "title": "Onfoldering",
        "items": [{
          # this it the folder we should find because it's inside the 'Onfoldering' folder group.
          "type": "folder",
          "title": "My Folder",
          "id": "3333"
        }]
      }]
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/3333", json={
      "id": "3333",
      "title": "My Folder"
    })

    folder = g.get_folder("My Folder", collection="Engineering", folder_group="Onfoldering")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/home?collection=1111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/3333"
    }])

  @use_guru()
  @responses.activate
  def test_get_folder_with_110_cards(self, g):
    # we build the list of items that comes back in the initial get call to load the folder.
    # we also build the responses that come back for loading the first page of 50 and the page of 10 cards.
    folder_items = []
    first_batch = {}
    second_batch = {}
    for i in range(110):
      if i < 50:
        folder_items.append({
          "type": "fact",
          "preferredPhrase": "card %s" % i,
          "id": str(i)
        })
      else:
        folder_items.append({
          "type": "fact",
          "id": str(i)
        })

        if i < 100:
          first_batch[str(i)] = {
            "preferredPhrase": "card %s" % i
          }
        else:
          second_batch[str(i)] = {
            "preferredPhrase": "card %s" % i
          }

    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders", json=[{
      "id": "1234",
      "title": "test"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/1234", json={
      "items": folder_items
    })
    responses.add(responses.POST, "https://api.getguru.com/api/v1/cards/bulk", json=first_batch)
    responses.add(responses.POST, "https://api.getguru.com/api/v1/cards/bulk", json=second_batch)

    folder = g.get_folder("test")

    self.assertEqual(len(folder.items), 110)
    self.assertEqual(len(folder.cards), 110)
    self.assertEqual(folder.cards[75].title, "card 75")
    self.assertEqual(folder.cards[105].title, "card 105")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/1234"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/cards/bulk",
      "body": {
        "ids": [str(i) for i in range(50, 100)]
      }
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/cards/bulk",
      "body": {
        "ids": [str(i) for i in range(100, 110)]
      }
    }])

  @use_guru()
  @responses.activate
  def test_make_folder(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/folders/home/entries?collection=1234", json=[])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders?collection=1234", json=[{
      "id": "1111",
      "title": "New Folder"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/1111", json={})

    result = g.make_folder("New Folder", collection="General", description="test")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/folders/home/entries?collection=1234",
      "body": {
        "actionType": "add",
        "folderEntries": [{
          "entryType": "folder",
          "title": "New Folder",
          "description": "test"
        }]
      }
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders?collection=1234"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/1111"
    }])

  @use_guru()
  @responses.activate
  def test_delete_folder(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders", json=[{
      "id": "abcd",
      "title": "General",
      "collection": {
        "id": "ababab"
      }
    },
    {
      "id": "4321",
      "title": "Test",
      "collection": {
        "id": "cdcdcd"
      }
    }])
    # responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/General", json={})
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/abcd", json={
      "id": "abcd",
      "title": "General",
      "collection": {
        "id": "ababab"
      }
    })
    responses.add(responses.DELETE, "https://api.getguru.com/api/v1/folders/abcd")

    folder = g.get_folder("General")
    folder.delete()


    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/abcd"
    }, {
      "method": "DELETE",
      "url": "https://api.getguru.com/api/v1/folders/abcd"
    }])

  @use_guru()
  @responses.activate
  def test_delete_folder_with_invalid_folder(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders", json=[])
    responses.add(responses.DELETE, "https://api.getguru.com/api/v1/folders/abcd")

    g.delete_folder("123456")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders"
    }])


  @use_guru()
  @responses.activate
  def test_get_folder_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/home?collection=1234", json={
      "collection": {
        "id": "1234"
      },
      "items": [{
        "type": "section",
        "title": "A",
        "items": [],
      }, {
        "type": "section",
        "title": "My Folder Group",
        "items": [{
          "type": "folder"
        }]
      }, {
        "type": "folder"
      }]
    })

    g.get_folder_group("my folder group", "General")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/home?collection=1234"
    }])

  @use_guru()
  @responses.activate
  def test_get_home_folder(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/home?collection=1234", json={
      "collection": {
        "id": "1234"
      },
      "items": [{
        "type": "section",
        "items": [{
          "type": "folder"
        }]
      }, {
        "type": "folder"
      }]
    })

    g.get_home_folder("General")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/home?collection=1234"
    }])

  @use_guru()
  @responses.activate
  def test_get_home_folder_by_invalid_collection(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/home?collection=1234", json={})

    g.get_home_folder("General")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }])

  @use_guru()
  @responses.activate
  def test_set_home_folder_item_order(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/home?collection=1234", json={
      "id": "home",
      "collection": {
        "id": "1234"
      },
      "items": [{
        "id": "1",
        "itemId": "i1",
        "type": "folder",
        "title": "Folder A"
      }, {
        "id": "2",
        "itemId": "i2",
        "type": "section",
        "title": "Folder Group",
        "items": [{
          "type": "folder"
        }]
      }, {
        "id": "3",
        "itemId": "i3",
        "type": "folder",
        "title": "Folder B"
      }]
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/folders/home", json={})

    home_folder = g.get_home_folder("General")
    home_folder.set_item_order("Folder B", "Folder A", "Folder Group")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/home?collection=1234"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/folders/home",
      "body": {
        "id": "home",
        "collection": {"id": "1234", "name": None, "type": None, "color": None},
        "items": [
          {"id": "3", "type": "folder", "title": "Folder B"}, # "itemId": "i3",
          {"id": "1", "type": "folder", "title": "Folder A"}, # "itemId": "i1",
          {"id": "2", "type": "section", "itemId": "i2", "title": "Folder Group", "items": [
            {"id": None, "type": "folder", "title": None}
          ]}
        ]
      }
    }])

  @use_guru()
  @responses.activate
  def test_set_folder_item_order(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders", json=[{
      "id": "1234",
      "title": "test"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/1234", json={
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
          "preferredPhrase": "card 1",
          "type": "fact"
        }, {
          "id": "3",
          "itemId": "i3",
          "preferredPhrase": "card 2",
          "type": "fact"
        }]
      }, {
        "id": "4",
        "itemId": "i4",
        "preferredPhrase": "card 3",
        "type": "fact"
      }]
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/folders/1234", json={})

    folder = g.get_folder("test")
    folder.set_item_order("card 3", "test")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/1234"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/folders/1234",
      "body": {
        "id": "1234", "type": "folder", "title": None,
        "collection": {"id": "abcd", "name": "General", "type": None, "color": None},
        "items": [
          {"type": "fact", "id": "4", "itemId": "i4"},
          {"type": "section", "id": "1", "itemId": "i1", "items": [
            {"type": "fact", "id": "2", "itemId": "i2"},
            {"type": "fact", "id": "3", "itemId": "i3"}
          ]}
        ]
      }
    }])

  @use_guru()
  @responses.activate
  def test_set_folder_group_item_order(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/home?collection=1234", json={
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
        "title": "My Folder Group",
        "items": [{
          "type": "folder",
          "id": "1",
          "itemId": "i1",
          "title": "Folder A"
        }, {
          "type": "folder",
          "id": "2",
          "itemId": "i2",
          "title": "Folder B"
        }, {
          "type": "folder",
          "id": "3",
          "itemId": "i3",
          "title": "Folder C"
        }]
      }, {
        "type": "folder"
      }]
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/folders/home", json={})

    folder_group = g.get_folder_group("my folder group", "General")
    folder_group.set_item_order("folder c", "folder b", "folder a")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/home?collection=1234"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/folders/home",
      "body": {
        "id": "home",
        "collection": {"id": "1234", "name": None, "type": None, "color": None},
        "items": [
          {"id": None, "type": "section", "itemId": None, "title": "A", "items": []},
          {
            # this is the folder group we edited:
            "id": None,
            "type": "section",
            "itemId": None,
            "title": "My Folder Group",
            "items": [
              {"id": "3", "type": "folder", "title": "Folder C"}, # "itemId": "i3"
              {"id": "2", "type": "folder", "title": "Folder B"}, # "itemId": "i2"
              {"id": "1", "type": "folder", "title": "Folder A"}  # "itemId": "i1"
            ]
          },
          {"id": None, "type": "folder", "title": None} # "itemId": None,
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
    g.set_item_order("invalid", "My Folder", "a", "b", "c")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }])

  @use_guru()
  @responses.activate
  def test_set_item_order_with_invalid_folder(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/isinvalid", status=404)
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders?collection=1234", json=[{
      "id": "abcd",
      "title": "Folder A",
    }, {
      "id": "efgh",
      "title": "Folder B"
    }])

    g.set_item_order("General", "isinvalid", "a", "b", "c")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/isinvalid"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections",
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders?collection=1234"
    }])

  @use_guru()
  @responses.activate
  def test_make_folder_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/home?collection=1234", json={
      "collection": {
        "id": "1234"
      },
      "items": [{
        "type": "section",
        "title": "A",
        "items": [],
      }, {
        "type": "section",
        "title": "My Folder Group",
        "items": [{
          "type": "folder"
        }]
      }, {
        "type": "folder"
      }]
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/folders/home/entries?collection=1234", json={})

    g.make_folder_group("General", "my folder group", "desc...")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/folders/home/entries?collection=1234",
      "body": {
        "actionType": "add",
        "folderEntries": [{
          "description": "desc...",
          "entryType": "section",
          "title": "my folder group"
        }]
      }
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/home?collection=1234"
    }])

  @use_guru()
  @responses.activate
  def test_add_card_to_folder(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", json={
      "id": "1111"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222", json={
      "id": "22222222-2222-2222-2222-222222222222",
      "title": "my folder",
      "items": []
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222", json={})

    g.add_card_to_folder("1111", "22222222-2222-2222-2222-222222222222")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111/extended"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222",
      "body": {
        "id": "22222222-2222-2222-2222-222222222222",
        "items": [{
          "id": "1111",
          "itemId": None,
          "type": "fact"
        }],
        "title": "my folder",
        "type": "folder"
      }
    }])

  @use_guru()
  @responses.activate
  def test_add_card_to_folder_by_folder_name(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", json={
      "id": "1111"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders", json=[{
      "id": "2222",
      "title": "my folder"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/2222", json={
      "id": "2222",
      "title": "my folder",
      "items": []
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/folders/2222", json={})

    g.add_card_to_folder("1111", "my folder")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111/extended"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/2222"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/folders/2222",
      "body": {
        "id": "2222",
        "items": [{
          "id": "1111",
          "itemId": None,
          "type": "fact"
        }],
        "title": "my folder",
        "type": "folder"
      }
    }])

  @use_guru()
  @responses.activate
  def test_add_card_to_folder_by_folder_slug(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", json={
      "id": "1111"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/abcde123", json={
      "id": "2222",
      "slug": "abcde123/my-folder",
      "title": "my folder"
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/folders/2222", json={})

    g.add_card_to_folder("1111", "abcde123")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111/extended"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/abcde123"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/folders/2222",
      "body": {
        "id": "2222",
        "items": [{
          "id": "1111",
          "itemId": None,
          "type": "fact"
        }],
        "title": "my folder",
        "type": "folder"
      }
    }])

  @use_guru()
  @responses.activate
  def test_add_card_to_invalid_folder(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", json={
      "id": "1111"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders", json=[{
      "id": "2222",
      "title": "my folder"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/2222", json={
      "id": "2222",
      "title": "my folder",
      "items": []
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/folders/2222", json={})

    g.add_card_to_folder("1111", "no match")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111/extended"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders"
    }])

  @use_guru()
  @responses.activate
  def test_add_invalid_card_to_folder(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", status=404)

    g.add_card_to_folder("1111", "2222")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111/extended"
    }])

  @use_guru()
  @responses.activate
  def test_add_card_to_folder_and_existing_section(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", json={
      "id": "1111"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222", json={
      "id": "22222222-2222-2222-2222-222222222222",
      "title": "my folder",
      "items": [{
        "type": "section",
        "title": "section 8",
        "id": "3333"
      }]
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222", json={})

    g.add_card_to_folder("1111", "22222222-2222-2222-2222-222222222222", "section 8")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111/extended"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222",
      "body": {
        "id": "22222222-2222-2222-2222-222222222222",
        "type": "folder",
        "title": "my folder",
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
  def test_add_card_to_folder_and_invalid_section(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", json={
      "id": "1111"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222", json={
      "id": "22222222-2222-2222-2222-222222222222",
      "title": "my folder",
      "items": []
    })
    # responses.add(responses.PUT, "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222", json={})

    g.add_card_to_folder("1111", "22222222-2222-2222-2222-222222222222", "section 8")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111/extended"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222"
    }])

  @use_guru()
  @responses.activate
  def test_add_card_to_folder_and_new_section(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", json={
      "id": "1111"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222", json={
      "id": "22222222-2222-2222-2222-222222222222",
      "title": "my folder",
      "items": []
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222/entries", status=204)
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222", json={
      "id": "22222222-2222-2222-2222-222222222222",
      "title": "my folder",
      "items": [{
        "type": "section",
        "title": "section 8",
        "id": "3333"
      }]
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222", json={})

    g.add_card_to_folder("1111", "22222222-2222-2222-2222-222222222222", "section 8", create_section_if_needed=True)

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/cards/1111/extended"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222/entries",
      "body": {
        "actionType": "add",
        "folderEntries": [{
          "entryType": "section",
          "title": "section 8"
        }]
      }
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222",
      "body": {
        "id": "22222222-2222-2222-2222-222222222222",
        "type": "folder",
        "title": "my folder",
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
  def test_remove_card_from_folder_by_card_id(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222", json={
      "id": "22222222-2222-2222-2222-222222222222",
      "title": "my folder",
      "collection": {
        "id": "3333"
      },
      "items": [{
        "type": "fact",
        "id": "1111",
        "preferredPhrase": "my card"
      }]
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222/entries", json={})

    g.remove_card_from_folder("1111", "22222222-2222-2222-2222-222222222222")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222/entries",
      "body": {
        "actionType": "remove",
        "collectionId": "3333",
        "id": "22222222-2222-2222-2222-222222222222",
        "folderEntries": [{
          "entryType": "card",
          "id": None
        }]
      }
    }])

  @use_guru()
  @responses.activate
  def test_remove_card_from_folder_with_invalid_card(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222", json={
      "id": "22222222-2222-2222-2222-222222222222",
      "title": "my folder",
      "collection": {
        "id": "3333"
      },
      "items": [{
        "type": "fact",
        "id": "1111",
        "preferredPhrase": "my card"
      }]
    })

    g.remove_card_from_folder("invalid", "22222222-2222-2222-2222-222222222222")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222"
    }])

  @use_guru()
  @responses.activate
  def test_remove_card_from_folder_with_invalid_folder(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222", status=404)
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders", json=[])

    g.remove_card_from_folder("1111", "22222222-2222-2222-2222-222222222222")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/22222222-2222-2222-2222-222222222222"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders"
    }])

  @use_guru()
  @responses.activate
  def test_get_folder_permissions(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111", json={
      "id": "11111111-1111-1111-1111-111111111111",
      "items": []
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111/permissions", json=[{
      "id": "1234",
      "group": {
        "id": "1111",
        "name": "Experts"
      }
    }])

    folder = g.get_folder("11111111-1111-1111-1111-111111111111")

    groups = folder.get_groups()
    self.assertEqual(groups[0].id, "1234")
    self.assertEqual(groups[0].group.id, "1111")
    self.assertEqual(groups[0].group.name, "Experts")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111/permissions"
    }])

  @use_guru()
  @responses.activate
  def test_add_folder_permission(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111", json={
      "id": "11111111-1111-1111-1111-111111111111",
      "items": []
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1111",
      "name": "Experts"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111/permissions")

    folder = g.get_folder("11111111-1111-1111-1111-111111111111")
    folder.add_group("Experts")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111/permissions",
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
  def test_remove_folder_permission(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111", json={
      "id": "11111111-1111-1111-1111-111111111111",
      "items": []
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111/permissions", json=[{
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
    responses.add(responses.DELETE, "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111/permissions/1234", status=204)

    folder = g.get_folder("11111111-1111-1111-1111-111111111111")
    result = folder.remove_group("Experts")

    self.assertEqual(result, True)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111/permissions"
    }, {
      "method": "DELETE",
      "url": "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111/permissions/1234"
    }])

  @use_guru()
  @responses.activate
  def test_get_folder_permissions_with_invalid_folder(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders", json=[{
      "id": "1234",
      "title": "test"
    }])

    result = g.get_shared_groups("my folder")

    self.assertEqual(result, None)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders"
    }])

  @use_guru()
  @responses.activate
  def test_add_folder_permission_with_invalid_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111", json={
      "id": "11111111-1111-1111-1111-111111111111",
      "items": []
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[])

    folder = g.get_folder("11111111-1111-1111-1111-111111111111")
    folder.add_group("Experts")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }])

  @use_guru()
  @responses.activate
  def test_add_folder_permission_with_invalid_folder(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders", json=[])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1111",
      "name": "Experts"
    }])

    result = g.add_shared_group("my folder", "Experts")

    self.assertEqual(result, None)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders"
    }])

  @use_guru()
  @responses.activate
  def test_remove_folder_permission_with_invalid_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1111",
      "name": "other group"
    }])

    result = g.remove_shared_group("my folder", "Experts")

    self.assertEqual(result, None)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }])

  @use_guru()
  @responses.activate
  def test_remove_folder_permission_with_invalid_folder(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1111",
      "name": "Experts"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders", json=[])

    result = g.remove_shared_group("my folder", "Experts")

    self.assertEqual(result, None)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders"
    }])

  @use_guru()
  @responses.activate
  def test_remove_folder_permission_with_unshared_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111", json={
      "id": "11111111-1111-1111-1111-111111111111",
      "items": []
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111/permissions", json=[{
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

    folder = g.get_folder("11111111-1111-1111-1111-111111111111")
    result = folder.remove_group("other group")

    self.assertEqual(result, None)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111/permissions"
    }])

  @use_guru()
  @responses.activate
  def test_add_folder_to_folder_group_by_uuid(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/home?collection=1234", json={
      "collection": {
        "id": "1234"
      },
      "items": [{
        "type": "section",
        "title": "Test",
        "itemId": "bg1",
        "items": [{
          "type": "folder",
          "id": "22222222-2222-2222-2222-222222222222",
          "itemId": "i2",
          "title": "folder 2"
        }],
      }, {
        "type": "folder",
        "id": "11111111-1111-1111-1111-111111111111",
        "itemId": "i1",
        "title": "folder 1"
      }]
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111", json={
      "id": "11111111-1111-1111-1111-111111111111",
      "title": "folder 2",
      "collection": {
        "id": "1234"
      }
    })
    responses.add(responses.PUT, "https://api.getguru.com/api/v1/folders/home/entries?collection=1234", json={})

    folder_group = g.get_folder_group("Test", collection="General")
    folder_group.add_folder("11111111-1111-1111-1111-111111111111")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/home?collection=1234"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/home?collection=1234"
    }, {
      "method": "PUT",
      "url": "https://api.getguru.com/api/v1/folders/home/entries?collection=1234",
      "body": {
        "sectionId": "bg1",
        "actionType": "move",
        "folderEntries": [
          {
            "id": "i1",
            "entryType": "folder"
          }
        ],
        "prevSiblingItem": "i2"
      }
    }
  ])

  @use_guru()
  @responses.activate
  def test_move_folder_to_collection(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111", json={
      "id": "11111111-1111-1111-1111-111111111111",
      "items": []
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/folders/bulkop", json={
      "id": "2222"
    })

    folder = g.get_folder("11111111-1111-1111-1111-111111111111")
    folder.move_to_collection("General")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/folders/bulkop",
      "body": {
        "action": {
          "collectionId": "1234",
          "type": "move-folder"
        },
        "items": {
          "itemIds": ["11111111-1111-1111-1111-111111111111"],
          "type": "id"
        }
      }
    }])

  @use_guru()
  @responses.activate
  def test_move_folder_to_collection_and_wait(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111", json={
      "id": "11111111-1111-1111-1111-111111111111",
      "items": []
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/folders/bulkop", json={
      "id": "2222"
    }, status=202)
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/bulkop/2222", json={})

    with patch("time.sleep", Mock(return_value=None)):
      folder = g.get_folder("11111111-1111-1111-1111-111111111111")
      folder.move_to_collection("General", timeout=1)

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/folders/bulkop",
      "body": {
        "action": {
          "collectionId": "1234",
          "type": "move-folder"
        },
        "items": {
          "itemIds": ["11111111-1111-1111-1111-111111111111"],
          "type": "id"
        }
      }
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/bulkop/2222"
    }])

  @use_guru()
  @responses.activate
  def test_move_folder_to_invalid_collection(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111", json={
      "id": "11111111-1111-1111-1111-111111111111",
      "items": []
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[])

    folder = g.get_folder("11111111-1111-1111-1111-111111111111")
    result = folder.move_to_collection("General")

    self.assertEqual(result, None)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }])

  @use_guru()
  @responses.activate
  def test_move_invalid_folder_to_collection(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/11111111", status=404)
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders?collection=1234", json=[])

    result = g.move_folder_to_collection("11111111", "General")

    self.assertEqual(result, None)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/11111111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders?collection=1234"
    }])

  @use_guru()
  @responses.activate
  def test_move_folder_to_its_current_collection(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111", json={
      "id": "11111111-1111-1111-1111-111111111111",
      "collection": {
        "id": "1234"
      },
      "items": []
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])

    folder = g.get_folder("11111111-1111-1111-1111-111111111111")
    folder.move_to_collection("General")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }])

  @use_guru()
  @responses.activate
  def test_move_folder_to_collection_and_it_times_out(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111", json={
      "id": "11111111-1111-1111-1111-111111111111",
      "items": []
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1234",
      "name": "General"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/folders/bulkop", json={
      "id": "2222"
    }, status=202)
    responses.add(responses.GET, "https://api.getguru.com/api/v1/folders/bulkop/2222", status=204)

    with patch("time.sleep", Mock(return_value=None)):
      folder = g.get_folder("11111111-1111-1111-1111-111111111111")
      folder.move_to_collection("General", timeout=3)

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/11111111-1111-1111-1111-111111111111"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/collections"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/folders/bulkop",
      "body": {
        "action": {
          "collectionId": "1234",
          "type": "move-folder"
        },
        "items": {
          "itemIds": ["11111111-1111-1111-1111-111111111111"],
          "type": "id"
        }
      }
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/bulkop/2222"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/folders/bulkop/2222"
    }])
