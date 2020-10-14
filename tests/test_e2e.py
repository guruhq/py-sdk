
import unittest

from tests.util import use_guru

import os
import guru

# these are valid credentials so these tests will hit our live API.
SDK_E2E_USER = os.environ.get("SDK_E2E_USER")
SDK_E2E_TOKEN = os.environ.get("SDK_E2E_TOKEN")


@unittest.skipUnless(os.environ.get("E2E"), "end-to-end tests not enabled")
class TestEndToEnd(unittest.TestCase):
  def check_attrs(self, object, expected):
    for key in expected:
      if expected[key] != "":
        self.assertEqual(getattr(object, key), expected[key])
      else:
        self.assertEqual(hasattr(object, key), True)
        
  @use_guru(SDK_E2E_USER, SDK_E2E_TOKEN)
  def test_cards(self, g):
    # first we'll load the card by slug.
    card = g.get_card("iadG4kpT")

    # make some assertions about the card.
    expected = {
      "type": "CARD",
      "collection": "",
      "created_date": "",
      "id": "d14dfa34-f237-4986-b0b9-ff4a1bb57fa2",
      "last_modified_date": "",
      "last_modified_by": "",
      "last_verified_by": "",
      "next_verification_date": "",
      "owner": "",
      "title": "Authentication",
      "share_status": "TEAM",
      "slug": "iadG4kpT/Authentication",
      "tags": "",
      "team_id": "6adf5f61-077e-415c-98c2-87942daaacb2",
      "verification_initiation_date": "",
      "verification_initiator": "",
      "verification_interval": "",
      "verification_reason": "",
      "verification_state": "",
      "version": "",
      "boards": ""
    }

    self.check_attrs(card, expected)

    # use the doc to check some things.
    self.assertEqual(len(card.doc.select("a[href]")), 3)

    # load the same card by ID and make sure it's equivalent.
    card2 = g.get_card(card.id)

    json1 = card.json()
    json2 = card2.json()

    for key in json1:
      # for some reason the HTML content comes back with attributes in a different order.
      if key != "content":
        self.assertEqual(json1[key], json2[key])
  
  @use_guru(SDK_E2E_USER, SDK_E2E_TOKEN)
  def test_card_creation(self, g):
    title = "end to end test card"
    html = """<p>this card was created from the sdk's end to end test.</p><p>it has two paragraphs and a <a href="www.getguru.com">link</a>!</p>"""
    card = g.make_card(title, html, "Sandbox")

    self.assertEqual(card.title, title)
    self.assertEqual(card.content, html)
    self.assertEqual(card.collection.name, "Sandbox")
    self.assertEqual(len(card.doc.select("p")), 2)
    self.assertEqual(len(card.doc.select("a[href]")), 1)
    self.assertEqual(card.tags, [])

    # add a tag.
    # i think this bumps the version number because of how it saves the card.
    # add_tag() doesn't make an API call, it adds the card locally then calling
    # save() makes it record the changes as a new version.
    card.add_tag("support")
    card.save()
    
    # load the card again and compare some things.
    card = g.get_card(card.id)
    self.check_attrs(card, {
      "title": title,
      "content": html,
      "verification_state": "TRUSTED",
      "share_status": "TEAM",
      "version": 2
    })
    self.assertEqual(card.collection.name, "Sandbox")
    self.assertEqual(len(card.doc.select("p")), 2)
    self.assertEqual(len(card.doc.select("a[href]")), 1)

    # check that the tag is there.
    self.assertEqual(len(card.tags), 1)
    self.assertEqual(card.tags[0].json(), {
      "id": "ed08a0b4-6893-46a6-a782-c05ce83666e7",
      "categoryId": "94b81d5e-504b-406f-96eb-69dc2d9e2af0",
      "categoryName": "Support Tags",
      "value": "support"
    })

    # add the card to a board.
    # load the board before and after so we can check that its
    # number of items changed as expected.
    board_before = g.get_board("Bored Board", collection="Sandbox")
    card.add_to_board("Bored Board")
    board_after = g.get_board("Bored Board", collection="Sandbox")
    card = g.get_card(card.id)

    self.assertEqual(len(board_before.items) + 1, len(board_after.items))

    # unverify then verify the card.
    card.unverify()
    card = g.get_card(card.id)
    self.check_attrs(card, {
      "title": title,
      "content": html,
      "verification_state": "NEEDS_VERIFICATION",
      "share_status": "TEAM",
      "version": 2
    })

    card.verify()
    card = g.get_card(card.id)
    self.check_attrs(card, {
      "title": title,
      "content": html,
      "verification_state": "TRUSTED",
      "share_status": "TEAM",
      "version": 2
    })

    # archive the card.
    card.archive()
    card = g.get_card(card.id)
    self.check_attrs(card, {
      "title": title,
      "content": html,
      "verification_state": "TRUSTED",
      "share_status": "TEAM",
      "version": 3,
      "archived": True
    })

    board_after_archive = g.get_board("Bored Board", collection="Sandbox")
    self.assertEqual(len(board_before.items), len(board_after_archive.items))

  @use_guru(SDK_E2E_USER, SDK_E2E_TOKEN)
  def test_boards(self, g):
    # load the board using its slug.
    board = g.get_board("KTgKBoGT")

    # make some assertions about the board.
    expected = {
      "last_modified": "",
      "title": "API",
      "slug": "KTgKBoGT/API",
      "id": "4c6086fc-0f5d-47be-b053-2fcf7c8ecc24",
      "item_id": "",
      "type": "board",
      "collection": "",
      "items": ""
    }

    self.check_attrs(board, expected)

    # check its items.
    self.assertEqual(board.json().get("items"), [{
      "type": "section",
      "id": "6e0010d6-6486-40c8-8624-d5095462e52b",
      "itemId": "6e0010d6-6486-40c8-8624-d5095462e52b",
      "items": [{
        "type": "fact",
        "id": "d14dfa34-f237-4986-b0b9-ff4a1bb57fa2",
        "itemId": "01107039-a096-45fd-8440-24d382a72658"
      }, {
        "type": "fact",
        "id": "ff6ae1f2-57a4-48b9-92b3-a80a2ae99f9a",
        "itemId": "7eb560eb-839c-4ae6-9dbb-9f3fc0dea0ce"
      }]
    }, {
      "type": "section",
      "id": "7bc34e16-4854-47bd-bcf1-0b84c3586cfa",
      "itemId": "7bc34e16-4854-47bd-bcf1-0b84c3586cfa",
      "items": [{
        "type": "fact",
        "id": "3a3bc011-8787-495b-8675-60cefad76822",
        "itemId": "c0e4bb4e-7c39-4ad2-b205-f3870d202583"
      }]
    }])

    # also load the board using its name and ID.
    board2 = g.get_board(board.id)
    board3 = g.get_board(board.title)

    self.assertEqual(board.json(), board2.json())
    self.assertEqual(board.json(), board3.json())
  
  @use_guru(SDK_E2E_USER, SDK_E2E_TOKEN)
  def test_collections(self, g):
    # load the collection using its name.
    collection = g.get_collection("Engineering")

    # make some assertions about the collection.
    expected = {
      "id": "6adf5f61-077e-415c-98c2-87942daaacb2",
      "name": "Engineering",
      "title": "Engineering", # title is a property that's an alias for name.
      "type": "INTERNAL",
      "slug": "x8n3l/Engineering",
      "color": "#303F9F",
      "description": "Keep your team working smoothly with an active knowledge base and a location to host all your engineering processes, updated code standards, QA guidelines and more.",
      "date_created": "",
      "stats": "",
      "roi_enabled": False,
      "public_cards_enabled": True,
      "roles": ""
    }

    self.check_attrs(collection, expected)
    self.assertEqual(collection.stats.trusted + collection.stats.untrusted, collection.stats.cards)
    self.assertEqual(collection.stats.cards, 5)

    # also load the collection using its ID and slug.
    collection2 = g.get_collection(collection.id)
    collection3 = g.get_collection("x8n3l")

    self.assertEqual(collection.json(), collection2.json())
    self.assertEqual(collection.json(), collection3.json())

  @use_guru(SDK_E2E_USER, SDK_E2E_TOKEN)
  def test_home_board_item_order(self, g):
    home_board = g.get_home_board("Engineering")
    home_board.set_item_order("API Docs", "Other Docs")

    # assert that this worked.
    home_board = g.get_home_board("Engineering")
    self.assertEqual(home_board.items[0].title, "API Docs")
    self.assertEqual(home_board.items[1].title, "Other Docs")

    # switch them back.
    home_board.set_item_order("Other Docs", "API Docs")
    home_board = g.get_home_board("Engineering")
    self.assertEqual(home_board.items[0].title, "Other Docs")
    self.assertEqual(home_board.items[1].title, "API Docs")

  @use_guru(SDK_E2E_USER, SDK_E2E_TOKEN)
  def test_board_group_item_order(self, g):
    board_group = g.get_board_group("API Docs", "Engineering")
    board_group.set_item_order("SDK", "API")

    # assert that this worked.
    board_group = g.get_board_group("API Docs", "Engineering")
    self.assertEqual(board_group.items[0].title, "SDK")
    self.assertEqual(board_group.items[1].title, "API")

    # switch them back.
    board_group.set_item_order("API", "SDK")
    board_group = g.get_board_group("API Docs", "Engineering")
    self.assertEqual(board_group.items[0].title, "API")
    self.assertEqual(board_group.items[1].title, "SDK")

  @use_guru(SDK_E2E_USER, SDK_E2E_TOKEN)
  def test_board_item_order(self, g):
    board = g.get_board("API", "Engineering")
    board.set_item_order("User & Groups", "General Information")
    
    # assert that this worked.
    board = g.get_board("API", "Engineering")
    self.assertEqual(board.items[0].title, "User & Groups")
    self.assertEqual(board.items[1].title, "General Information")

    # switch them back.
    board.set_item_order("General Information", "User & Groups")
    board = g.get_board("API", "Engineering")
    self.assertEqual(board.items[0].title, "General Information")
    self.assertEqual(board.items[1].title, "User & Groups")
