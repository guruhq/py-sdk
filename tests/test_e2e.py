
import unittest
import requests
import mimetypes

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
      "archived": False,
      "favorited": False,
      "boards": ""
    }

    self.check_attrs(card, expected)
    self.assertEqual(len(card.boards), 1)

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

    # test favoriting and unfavoriting.
    card.favorite()
    card = g.get_card(card.id)
    self.assertEqual(card.favorited, True)
    card.unfavorite()
    card = g.get_card(card.id)
    self.assertEqual(card.favorited, False)
  
  @use_guru(SDK_E2E_USER, SDK_E2E_TOKEN)
  def test_card_comments(self, g):
    card = g.get_card("cddaekgi")
    comments = g.get_card_comments(card)

    # there should be 2 comments and they're returned in reverse order.
    self.assertEqual(len(comments), 2)
    self.check_attrs(comments[0], {
      "content": "and there's a second comment.",
      "owner": "",
      "last_modified_date": "",
      "id": "",
      "created_date": "",
      "card": ""
    })
    self.check_attrs(comments[1], {
      "content": "here's the first comment",
      "owner": "",
      "last_modified_date": "",
      "id": "",
      "created_date": "",
      "card": ""
    })

    # test create/update/delete for comments:
    # add a comment.
    comment = card.add_comment("new comment")

    # check that it was added.
    comments = g.get_card_comments(card)
    self.assertEqual(len(comments), 3)
    self.assertEqual(comments[0].content, "new comment")

    # update it.
    comment.content = "updated comment"
    g.update_card_comment(comment)

    # check that it was updated.
    comments = g.get_card_comments(card)
    self.assertEqual(len(comments), 3)
    self.assertEqual(comments[0].content, "updated comment")

    # delete it.
    g.delete_card_comment(card, comment.id)

    # check that it was deleted.
    comments = g.get_card_comments(card)
    self.assertEqual(len(comments), 2)
    self.assertEqual(comments[0].content, "and there's a second comment.")
    self.assertEqual(comments[1].content, "here's the first comment")

  @use_guru(SDK_E2E_USER, SDK_E2E_TOKEN)
  def test_find_card(self, g):
    cards = g.find_cards(tag="api")
    self.assertEqual(len(cards), 3)

    card = g.find_card(title="Onboarding", collection="Engineering")
    self.assertEqual(card.id, "09643e16-0794-4550-9bb9-25e65014dfe1")

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

    # this is commented out because getting an archived cards returns a 404 error.
    # there's a ticket open to get this fixed (#52080).
    # card = g.get_card(card.id)
    # self.check_attrs(card, {
    #   "title": title,
    #   "content": html,
    #   "verification_state": "TRUSTED",
    #   "share_status": "TEAM",
    #   "version": 3,
    #   "archived": True
    # })

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
  def test_creating_collections(self, g):
    # check that a collection doesn't exist.
    collection = g.get_collection("New Collection")
    self.assertIsNone(collection)

    # make a collection.
    # (self, name, desc="", color=GREEN, is_sync=False, group="All Members", public_cards=True):
    g.make_collection("New Collection", desc="test", group="Experts")
    collection = g.get_collection("New Collection")
    self.assertEqual(collection.description, "test")

    # add a group to it.
    collection.add_group("Support", guru.READ_ONLY)

    # check the groups on it.
    groups = collection.get_groups()
    self.assertEqual(len(groups), 2)
    self.assertEqual(groups[0].group_name, "Experts")
    self.assertEqual(groups[0].role, guru.COLLECTION_OWNER)
    self.assertEqual(groups[1].group_name, "Support")
    self.assertEqual(groups[1].role, guru.READ_ONLY)

    # promote one group and remove another.
    collection.add_group("Support", guru.COLLECTION_OWNER)
    collection.remove_group("Experts")

    # check the groups on it.
    groups = collection.get_groups()
    self.assertEqual(len(groups), 1)
    self.assertEqual(groups[0].group_name, "Support")
    self.assertEqual(groups[0].role, guru.COLLECTION_OWNER)

    # delete the collection.
    g.delete_collection(collection)

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

  @use_guru(SDK_E2E_USER, SDK_E2E_TOKEN)
  def test_board_permissions(self, g):
    board = g.get_board("zTBG4GbT")

    # make sure it's not shared with any groups.
    groups1 = board.get_groups()
    self.assertEqual(groups1, [])

    # add a group and check that it worked.
    board.add_group("Support")
    groups2 = board.get_groups()
    self.assertEqual(groups2[0].group.name, "Support")

    # remove the group and make sure that worked too.
    board.remove_group("Support")
    groups3 = board.get_groups()
    self.assertEqual(groups3, [])

  @use_guru(SDK_E2E_USER, SDK_E2E_TOKEN)
  def test_adding_card_to_board(self, g):
    # make sure the card is not on the 'Other Docs' board.
    board = g.get_board("zTBG4GbT")
    self.assertIsNone(board.get_card("Getting Started with the SDK"))

    # add the SDK card to the 'Other Docs' board.
    # https://app.getguru.com/card/TbbGKLac/Getting-Started-with-the-SDK
    card = g.get_card("TbbGKLac")
    board.add_card(card)

    # make sure the card got added.
    board = g.get_board("zTBG4GbT")
    card2 = board.get_card("Getting Started with the SDK")
    self.assertEqual(card.id, card2.id)

    # remove the SDK card from 'Other Docs' and make sure it worked.
    board.remove_card(card)
    board = g.get_board("zTBG4GbT")
    self.assertIsNone(board.get_card("Getting Started with the SDK"))

  @use_guru(SDK_E2E_USER, SDK_E2E_TOKEN)
  def test_groups(self, g):
    # make sure loading a group works.
    experts = g.get_group("Experts")
    experts2 = g.get_group(experts)

    self.assertEqual(experts.id, "f2a04eea-615b-41d5-8e2e-641ce5fc3728")
    self.assertEqual(experts, experts2)

    # try loading a 'managed' group, like All Members.
    # also, make sure its name matching is _not_ case sensitive.
    all_members = g.get_group("all members")
    self.assertEqual(all_members.id, "471fd096-2027-4366-bfdc-b8613992545f")

    # try loading a group that doesn't exist.
    doesnt_exist = g.get_group("doesn't exist")
    self.assertIsNone(doesnt_exist)

    # make a group and check that it exists.
    g.make_group("test group")
    self.assertIsNotNone(g.get_group("test group"))

    # delete the group and check that it got deleted.
    g.delete_group("test group")
    self.assertIsNone(g.get_group("test group"))

  @use_guru(SDK_E2E_USER, SDK_E2E_TOKEN)
  def test_invite_user(self, g):
    users = g.get_members("sdk_test")
    self.assertEqual(len(users), 0)

    # invite the user and make sure they are on the team and in the correct groups.
    g.invite_user("rmiller+sdk_test@getguru.com", "Experts", "Support")
    users = g.get_members("sdk_test")
    self.assertEqual(len(users), 1)
    self.assertEqual(users[0].has_group("Experts"), True)
    self.assertEqual(users[0].has_group("Support"), True)
    self.assertEqual(users[0].has_group("Other Group"), False)

    # remove the user from a group.
    g.remove_user_from_group("rmiller+sdk_test@getguru.com", "Support")
    users = g.get_members("sdk_test")
    self.assertEqual(len(users), 1)
    self.assertEqual(users[0].has_group("Experts"), True)
    self.assertEqual(users[0].has_group("Support"), False)

    # remove the user from the team.
    g.remove_user_from_team("rmiller+sdk_test@getguru.com")
    users = g.get_members("sdk_test")
    self.assertEqual(len(users), 0)

  @use_guru(SDK_E2E_USER, SDK_E2E_TOKEN)
  def test_drafts(self, g):
    drafts = g.get_drafts()
    self.assertEqual(drafts, [])

  @use_guru(SDK_E2E_USER, SDK_E2E_TOKEN)
  def test_analytics(self, g):
    events = g.get_events(max_pages=1)
    self.assertEqual(len(events), 500)
    self.assertEqual(events[0], {
      "properties": {"source": "UI"},
      "type": "login",
      "eventType": "login",
      "user": "rmiller@getguru.com",
      "eventDate": "2020-09-14T19:54:44.096+0000"
    })

  @use_guru(SDK_E2E_USER, SDK_E2E_TOKEN)
  def test_upload_file(self, g):
    # write a local text file then try uploading it.
    guru.write_file("/tmp/upload.txt", "sample file")
    guru_url = g.upload_file("/tmp/upload.txt")

    # download the file to check that it worked.
    response = requests.get(guru_url, auth=(SDK_E2E_USER, SDK_E2E_TOKEN))
    self.assertEqual(response.content.decode("utf-8"), "sample file")
  
  @use_guru(SDK_E2E_USER, SDK_E2E_TOKEN)
  def test_mimetype_return(self, g):
    # write a local text file.
    filename = "/tmp/upload.txt"
    guru.write_file(filename, "sample file")
    file_mimetype, file_encoding = mimetypes.guess_type(filename)

    # assert that the mimetype we get from the filestack response matches the mimetype we get from the mimetype module
    fs_data = g.upload_to_filestack(filename)
    self.assertEqual(fs_data.get("type"), file_mimetype)

  @use_guru(SDK_E2E_USER, SDK_E2E_TOKEN)
  def test_find_and_replace_e2e(self, g):
    # do a dry run of find and replace
    term = "card"
    replacement = "guru-knowledge"
    existing_card_id = "9220612a-f3e6-4fe4-984c-045df329c0aa"

    find_and_replace = guru.FindAndReplace(g, term, replacement, replace_title=True, collection="Getting Started with Guru", task_name="find_and_replace_e2e", show_preview=False)
    find_and_replace_with_exclusions = guru.FindAndReplace(g, term, replacement, replace_title=True, collection="Getting Started with Guru", task_name="find_and_replace_e2e_with_exclusions", excluded_ids=[existing_card_id], show_preview=False)

    # assert that the replacement content file is generated and contains the replacement term
    find_and_replace.run()
    self.assertIn(f'<span class="sdk-replacement-highlight">{replacement}</span>'.lower(), guru.read_file(f"/tmp/find_and_replace_e2e/new_content/new_{existing_card_id}.html").lower())
    
    # assert that the excluded card's html file doesn't exist
    find_and_replace_with_exclusions.run()
    with self.assertRaises(FileNotFoundError):
      with open(f"/tmp/find_and_replace_e2e_with_exclusions/new_content/new_{existing_card_id}.html", "r") as file_in:
        return file_in.read()
    

  
# these are the methods that aren't tested yet:
# add_users_to_group
# make_board_group (there is no 'delete_board_group' yet)
# add_board_to_board_group (there is no 'remove_board_from_board_group' yet)
# add_section_to_board (there is no 'remove_section_from_board' yet)
# merge_tags, delete_tag (there is no 'make_tag' yet)
# upload_content
