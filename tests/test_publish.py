
import unittest

from tests.util import use_guru

import os
import guru

# these are valid credentials so these tests will hit our live API.
SDK_E2E_USER = os.environ.get("SDK_E2E_USER")
SDK_E2E_TOKEN = os.environ.get("SDK_E2E_TOKEN")


class PublisherTest(guru.Publisher):
  """
  this publisher class just keeps track of the calls it makes
  so we can do assertions on these values later.
  """

  def __init__(self, g, metadata=None, external_data=None, dry_run=False):
    self.calls = []
    self.external_data = external_data or []
    super().__init__(g, metadata=metadata, silent=True, dry_run=dry_run)

  def get_external_url(self, external_id, card):
    self.calls.append("get external url %s" % card.title)
    return "https://www.example.com/%s" % external_id

  def find_external_collection(self, collection):
    self.calls.append("find collection %s" % collection.name)
    return collection.id[0:4] if collection.name in self.external_data else ""

  def find_external_board_group(self, board_group):
    self.calls.append("find board group %s" % board_group.title)
    return board_group.id[0:4] if board_group.title in self.external_data else ""

  def find_external_board(self, board):
    self.calls.append("find board %s" % board.title)
    return board.id[0:4] if board.title in self.external_data else ""

  def find_external_section(self, section):
    self.calls.append("find section %s" % section.title)
    return section.id[0:4] if section.title in self.external_data else ""

  def find_external_card(self, card):
    self.calls.append("find card %s" % card.title)
    return card.id[0:4] if card.title in self.external_data else ""

  # crud operations for cards
  def create_external_card(self, card, section, board, board_group, collection):
    self.calls.append("create card %s" % card.title)
    return card.id[0:4]
  
  def update_external_card(self, external_id, card, section, board, board_group, collection):
    self.calls.append("update card %s" % card.title)
  
  def delete_external_card(self, external_id):
    self.calls.append("delete card %s" % external_id)

  # crud operations for sections.
  def create_external_section(self, section, board, board_group, collection):
    super().create_external_section(section, board, board_group, collection)
    self.calls.append("create section %s" % section.title)
    return section.id[0:4]
  
  def update_external_section(self, external_id, section, board, board_group, collection):
    super().update_external_section(external_id, section, board, board_group, collection)
    self.calls.append("update section %s" % section.title)
  
  def delete_external_section(self, external_id):
    super().delete_external_section(external_id)
    self.calls.append("delete section %s" % external_id)

  # crud operations for boards.
  def create_external_board(self, board, board_group, collection):
    super().create_external_board(board, board_group, collection)
    self.calls.append("create board %s" % board.title)
    return board.id[0:4]
  
  def update_external_board(self, external_id, board, board_group, collection):
    super().update_external_board(external_id, board, board_group, collection)
    self.calls.append("update board %s" % board.title)
  
  def delete_external_board(self, external_id):
    super().delete_external_board(external_id)
    self.calls.append("delete board %s" % external_id)
  
  # crud operations for board groups.
  def create_external_board_group(self, board_group, collection):
    super().create_external_board_group(board_group, collection)
    self.calls.append("create board group %s" % board_group.title)
    return board_group.id[0:4]
  
  def update_external_board_group(self, external_id, board_group, collection):
    super().update_external_board_group(external_id, board_group, collection)
    self.calls.append("update board group %s" % board_group.title)
  
  def delete_external_board_group(self, external_id):
    super().delete_external_board_group(external_id)
    self.calls.append("delete board group %s" % external_id)
  
  # crud operations for collections.
  def create_external_collection(self, collection):
    super().create_external_collection(collection)
    self.calls.append("create collection %s" % collection.title)
    return collection.id[0:4]

  def update_external_collection(self, external_id, collection):
    super().update_external_collection(external_id, collection)
    self.calls.append("update collection %s" % collection.title)
  
  def delete_external_collection(self, external_id):
    super().delete_external_collection(external_id)
    self.calls.append("delete collection %s" % external_id)


@unittest.skipUnless(os.environ.get("PUB"), "publishing tests not enabled")
class TestPublish(unittest.TestCase):
  @use_guru(SDK_E2E_USER, SDK_E2E_TOKEN)
  def test_publishing_a_collection(self, g):
    publisher = PublisherTest(g, metadata={})
    publisher.publish_collection("Engineering")

    self.assertEqual(publisher.calls, [
      "find collection Engineering",
      "create collection Engineering",
      "find board Other Docs",
      "create board Other Docs",
      "find card Onboarding",
      "create card Onboarding",
      "find board group API Docs",
      "create board group API Docs",
      "find board API",
      "create board API",
      "find section General Information",
      "create section General Information",
      "get external url Pagination",
      "find card Authentication",
      "create card Authentication",
      "find card Pagination",
      "create card Pagination",
      "find section User & Groups",
      "create section User & Groups",
      "find card Inviting Users",
      "create card Inviting Users",
      "find board SDK",
      "create board SDK",
      "get external url Authentication",
      "find card Getting Started with the SDK",
      "create card Getting Started with the SDK"
    ])

  @use_guru(SDK_E2E_USER, SDK_E2E_TOKEN)
  def test_publishing_a_board(self, g):
    publisher = PublisherTest(g, metadata={})
    publisher.publish_board("KTgKBoGT")

    self.assertEqual(publisher.calls, [
      "find board API",
      "create board API",
      "find section General Information",
      "create section General Information",
      "get external url Pagination",
      "find card Authentication",
      "create card Authentication",
      "find card Pagination",
      "create card Pagination",
      "find section User & Groups",
      "create section User & Groups",
      "find card Inviting Users",
      "create card Inviting Users"
    ])

  @use_guru(SDK_E2E_USER, SDK_E2E_TOKEN)
  def test_republishing_some_content(self, g):
    metadata = {
      "68fafb96-0446-46f4-b9e9-f778fdd85eb1": {
        "type": "card",
        "external_id": "1234",
        "last_updated": "2020-01-01T00:00:00.000+0000"
      }
    }
    
    publisher = PublisherTest(g, metadata)
    publisher.publish_board("9cxgG7jc")

    self.assertEqual(publisher.calls, [
      "find board SDK",
      "create board SDK",
      "get external url Authentication",
      "update card Getting Started with the SDK"
    ])
  
  @use_guru(SDK_E2E_USER, SDK_E2E_TOKEN)
  def test_skipping_a_card(self, g):
    # we set the card's last_updated date to the year 2030
    # which makes us thing the card in guru has not changed
    # and we don't need to call update_card().
    metadata = {
      "68fafb96-0446-46f4-b9e9-f778fdd85eb1": {
        "type": "card",
        "external_id": "1234",
        "last_updated": "2030-01-01T00:00:00.000+0000"
      }
    }
    
    publisher = PublisherTest(g, metadata)
    publisher.publish_board("9cxgG7jc")

    self.assertEqual(publisher.calls, [
      "find board SDK",
      "create board SDK"
    ])

  @use_guru(SDK_E2E_USER, SDK_E2E_TOKEN)
  def test_republishing_a_whole_collection(self, g):
    metadata = {
      "6adf5f61-077e-415c-98c2-87942daaacb2": {
        "type": "collection",
        "external_id": "6adf",
        "last_updated": "2020-01-01T00:00:00.000+0000"
      },
      "516405af-dcbe-4478-94b6-6e2a16c2fde7": {
        "type": "board_group",
        "external_id": "5164",
        "last_updated": "2020-01-01T00:00:00.000+0000"
      },
      "d32d4329-6894-486f-9dd0-834077576f08": {
        "type": "board",
        "external_id": "d32d",
        "last_updated": "2020-01-01T00:00:00.000+0000"
      },
      "68fafb96-0446-46f4-b9e9-f778fdd85eb1": {
        "type": "card",
        "external_id": "68fa",
        "last_updated": "2020-01-01T00:00:00.000+0000"
      },
      "4c6086fc-0f5d-47be-b053-2fcf7c8ecc24": {
        "type": "board",
        "external_id": "4c60",
        "last_updated": "2020-01-01T00:00:00.000+0000"
      },
      "6e0010d6-6486-40c8-8624-d5095462e52b": {
        "type": "section",
        "external_id": "6e00",
        "last_updated": "2020-01-01T00:00:00.000+0000"
      },
      "7bc34e16-4854-47bd-bcf1-0b84c3586cfa": {
        "type": "section",
        "external_id": "7bc3",
        "last_updated": "2020-01-01T00:00:00.000+0000"
      },
      "d14dfa34-f237-4986-b0b9-ff4a1bb57fa2": {
        "type": "card",
        "external_id": "d14d",
        "last_updated": "2020-01-01T00:00:00.000+0000"
      },
      "ff6ae1f2-57a4-48b9-92b3-a80a2ae99f9a": {
        "type": "card",
        "external_id": "ff6a",
        "last_updated": "2020-01-01T00:00:00.000+0000"
      },
      "c6ce0381-12cc-452c-9634-c8766d5e72e7": {
        "type": "board",
        "external_id": "c6ce",
        "last_updated": "2020-01-01T00:00:00.000+0000"
      }
    }

    publisher = PublisherTest(g, metadata)
    publisher.publish_collection("Engineering")

    # the metadata above only has some of the objects so some calls
    # are creates and some are updates.
    self.assertEqual(publisher.calls, [
      "update collection Engineering",
      "update board Other Docs",
      "find card Onboarding",
      "create card Onboarding",
      "update board group API Docs",
      "update board API",
      "update section General Information",
      "get external url Pagination",
      "update card Authentication",
      "update card Pagination",
      "update section User & Groups",
      "find card Inviting Users",
      "create card Inviting Users",
      "update board SDK",
      "get external url Authentication",
      "update card Getting Started with the SDK"
    ])
  
  @use_guru(SDK_E2E_USER, SDK_E2E_TOKEN)
  def test_processing_a_deletion(self, g):
    metadata = {
      # this ID won't match a real card so when we call process_deletions() this'll
      # look like a card that was previously published and no longer exists, so we'll
      # make the call to delete it.
      "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa": {
        "type": "card",
        "external_id": "aaaa",
        "last_updated": "2020-01-01T00:00:00.000+0000"
      },
      "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb": {
        "type": "section",
        "external_id": "bbbb",
        "last_updated": "2020-01-01T00:00:00.000+0000"
      },
      "cccccccc-cccc-cccc-cccc-cccccccccccc": {
        "type": "board",
        "external_id": "cccc",
        "last_updated": "2020-01-01T00:00:00.000+0000"
      },
      "dddddddd-dddd-dddd-dddd-dddddddddddd": {
        "type": "board_group",
        "external_id": "dddd",
        "last_updated": "2020-01-01T00:00:00.000+0000"
      },
      "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee": {
        "type": "collection",
        "external_id": "eeee",
        "last_updated": "2020-01-01T00:00:00.000+0000"
      }
    }
    
    publisher = PublisherTest(g, metadata)
    publisher.publish_board("9cxgG7jc")
    publisher.process_deletions()

    self.assertEqual(publisher.calls, [
      "find board SDK",
      "create board SDK",
      "get external url Authentication",
      "find card Getting Started with the SDK",
      "create card Getting Started with the SDK",
      "delete card aaaa",
      "delete section bbbb",
      "delete board cccc",
      "delete board group dddd",
      "delete collection eeee"
    ])
  
  @use_guru()
  def test_the_base_class(self, g):
    publisher = guru.Publisher(g)
    
    with self.assertRaises(NotImplementedError):
      publisher.get_external_url(None, None)
    with self.assertRaises(NotImplementedError):
      publisher.create_external_card(None, None, None, None, None)
    with self.assertRaises(NotImplementedError):
      publisher.update_external_card(None, None, None, None, None, None)
    with self.assertRaises(NotImplementedError):
      publisher.delete_external_card(None)

  @use_guru(SDK_E2E_USER, SDK_E2E_TOKEN)
  def test_dry_run(self, g):
    publisher = PublisherTest(g, metadata={}, dry_run=True)
    publisher.publish_collection("Engineering")

    self.assertEqual(publisher.calls, [
      "find collection Engineering",
      "find board Other Docs",
      "find card Onboarding",
      "find board group API Docs",
      "find board API",
      "find section General Information",
      "get external url Pagination",
      "find card Authentication",
      "find card Pagination",
      "find section User & Groups",
      "find card Inviting Users",
      "find board SDK",
      "get external url Authentication",
      "find card Getting Started with the SDK"
    ])

  @use_guru(SDK_E2E_USER, SDK_E2E_TOKEN)
  def test_when_objects_are_found(self, g):
    # external_data is a list of object names and we pretend they already exist in the external
    # system so find_external_* will return an ID if the object's name is in this list.
    external_data = [
      "Engineering",                 # collection
      "Other Docs",                  # board
      "Onboarding",                  # card
      "API Docs",                    # board group
      "API",                         # board
      "General Information",         # section
      "Authentication",              # card
      # we leave out this so one card is not found.
      # "Pagination",                # card
      "User & Groups",               # section
      "Inviting Users",              # card
      "SDK",                         # board
      "Getting Started with the SDK" # card
    ]

    publisher = PublisherTest(g, metadata={}, external_data=external_data)
    publisher.publish_collection("Engineering")

    self.assertEqual(publisher.calls, [
      "find collection Engineering",
      "update collection Engineering",
      "find board Other Docs",
      "update board Other Docs",
      "find card Onboarding",
      "update card Onboarding",
      "find board group API Docs",
      "update board group API Docs",
      "find board API",
      "update board API",
      "find section General Information",
      "update section General Information",
      "get external url Pagination",
      "find card Authentication",
      "update card Authentication",
      "find card Pagination",
      # this is a 'create' call because we intentionally left 'Pagination' out of external_data to test this.
      "create card Pagination",
      "find section User & Groups",
      "update section User & Groups",
      "find card Inviting Users",
      "update card Inviting Users",
      "find board SDK",
      "update board SDK",
      "get external url Authentication",
      "find card Getting Started with the SDK",
      "update card Getting Started with the SDK",
    ])
