
from guru.util import find_by_name_or_id, find_by_id

from bs4 import BeautifulSoup


class Section:
  def __init__(self, data):
    self.type = "section"
    self.title = data.get("title")
    self.id = data.get("id")
    self.item_id = data.get("itemId")
    self.items = [Card(i) for i in data.get("items") or []]

  def json(self):
    return {
      "type": "section",
      "id": self.id,
      "itemId": self.item_id,
      "items": [i.lite_json() for i in self.items]
    }
  
  def lite_json(self):
    return self.json()


class Board:
  def __init__(self, data, guru=None, home_board=None):
    self.guru = guru
    self.home_board = home_board
    self.last_modified = data.get("lastModified")
    self.title = data.get("title")
    self.slug = data.get("slug")
    self.id = data.get("id")
    self.__item_id = data.get("itemId")
    self.type = "board"
    
    if data.get("collection"):
      self.collection = Collection(data.get("collection"))
    else:
      self.collection = None
    
    self.items = []
    self.__cards = []
    self.__sections = []
    self.__all_items = []
    for item in data.get("items", []):
      if item.get("type") == "section":
        section = Section(item)
        self.items.append(section)
        self.__sections.append(section)
        self.__all_items.append(section)
        self.__all_items += section.items
        self.__cards += section.items
      else:
        card = Card(item)
        self.items.append(card)
        self.__all_items.append(card)
        self.__cards.append(card)

  @property
  def item_id(self):
    if self.__item_id:
      return self.__item_id
    
    # load the home board (if necessary), find this board, and set its item_id.
    if not self.home_board:
      self.home_board = self.guru.get_home_board(self.collection)
    
    board_item = find_by_id(self.home_board.boards, self.id)
    if not board_item:
      print("could not find board on home board")
    else:
      self.__item_id = board_item.item_id
    
    return self.__item_id

  @property
  def cards(self):
    return tuple(self.__cards)
  
  @property
  def sections(self):
    return tuple(self.__sections)
  
  @property
  def all_items(self):
    return tuple(self.__all_items)

  def add_section(self, name):
    self.guru.add_section_to_board(self, name)

  def set_item_order(self, *items):
    return self.guru.set_item_order(self.collection, self, *items)

  def get_card(self, card):
    if isinstance(card, Card):
      card = card.id
    return find_by_name_or_id(self.__cards, card)

  def add_card(self, card, section=None):
    return self.guru.add_card_to_board(card, self, section=section)

  def remove_card(self, card):
    return self.guru.remove_card_from_board(card, self)

  def get_groups(self):
    return self.guru.get_shared_groups(self)
  
  def add_group(self, group):
    return self.guru.add_shared_group(self, group)
  
  def remove_group(self, group):
    return self.guru.remove_shared_group(self, group)

  def move_to_collection(self, collection, timeout=0):
    self.guru.move_board_to_collection(self, collection, timeout)

  def json(self, include_items=True, include_item_id=False, include_collection=True):
    data = {
      "id": self.id,
      "type": self.type,
      "title": self.title,
    }

    if include_items:
      data["items"] = [i.lite_json() for i in self.items]
    if include_item_id:
      data["itemId"] = self.item_id
    if self.collection and include_collection:
      data["collection"] = self.collection.json()
    
    return data


class BoardPermission:
  def __init__(self, data, guru=None, board=None):
    self.guru = guru
    self.board = board
    self.id = data.get("id")
    self.group = Group(data.get("group"))


class BoardGroup:
  def __init__(self, data, guru=None, home_board=None):
    self.guru = guru
    self.home_board = home_board
    self.title = data.get("title")
    self.item_id = data.get("itemId")
    self.description = data.get("description") or ""
    self.slug = data.get("slug")
    self.id = data.get("id")
    self.type = "board-group"
    self.items = [Board(b, guru) for b in data.get("items") or []]

  def set_item_order(self, *items):
    return self.guru.set_item_order(self.home_board.collection, self, *items)

  def json(self, include_items=True, include_item_id=True, include_collection=True):
    return {
      "id": self.id,
      "type": "section",
      "itemId": self.item_id,
      "title": self.title,
      "items": [i.json(
        include_items=False,
        include_item_id=False,
        include_collection=False
      ) for i in self.items]
    }

  def add_board(self, board):
    collection = None
    if self.home_board:
      collection = self.home_board.collection
    return self.guru.add_board_to_board_group(board, self, collection=collection)

class HomeBoard:
  def __init__(self, data, guru=None):
    self.guru = guru
    self.last_modified = data.get("lastModified")
    self.slug = data.get("slug")
    self.id = data.get("id")
    self.collection = Collection(data.get("collection"))
    
    self.items = []
    self.__board_groups = []
    self.__boards = []
    for item in data.get("items", []):
      if item.get("type") == "board":
        board = Board(item, guru, home_board=self)
        self.items.append(board)
        self.__boards.append(board)
      elif item.get("type") == "section":
        board_group = BoardGroup(item, guru, home_board=self)
        self.items.append(board_group)
        self.__board_groups.append(board_group)
        self.__boards += board_group.items

  @property
  def boards(self):
    return tuple(self.__boards)
  
  @property
  def board_groups(self):
    return tuple(self.__board_groups)

  def set_item_order(self, *items):
    return self.guru.set_item_order(self.collection, self, *items)

  def json(self, include_item_id=True):
    return {
      "id": self.id,
      "collection": self.collection.json(),
      "items": [
        i.json(
          include_items=isinstance(i, BoardGroup),
          include_item_id=include_item_id,
          include_collection=False
        ) for i in self.items
      ]
    }


class Group:
  def __init__(self, data):
    self.date_created = data.get("dateCreated")
    self.modifiable = data.get("modifiable")
    self.id = data.get("id")
    self.identifier = data.get("groupIdentifier")
    self.name = data.get("name")


class Collection:
  def __init__(self, data, guru=None):
    self.guru = guru

    # these are the properties you always get, like when a card has a nested
    # collection object with just a few properties.
    self.id = data.get("id")
    self.name = data.get("name")
    self.type = data.get("collectionType")
    self.slug = data.get("slug")
    self.color = data.get("color")

    # these are the expanded properties you get when loading a single collection
    # or list of collections.
    self.date_created = data.get("dateCreated")
    self.description = data.get("description")

    stats = data.get("collectionStats", {}).get("stats")
    self.stats = CollectionStats(stats) if stats else None
    
    self.roi_enabled = data.get("roiEnabled")
    self.public_cards_enabled = data.get("publicCardsEnabled")
    self.roles = data.get("roles")
  
  @property
  def title(self):
    return self.name

  @title.setter
  def title(self, title):
    self.name = title

  def add_group(self, group, role):
    return self.guru.add_group_to_collection(group, self, role)

  def remove_group(self, group):
    return self.guru.remove_group_from_collection(group, self)

  def get_groups(self):
    return self.guru.get_groups_on_collection(self)

  def json(self):
    return {
      "id": self.id,
      "name": self.name,
      "type": self.type,
      "color": self.color,
    }


class CollectionAccess:
  def __init__(self, data):
    self.group_name = data.get("groupName")
    self.group_id = data.get("groupId")
    self.role = data.get("role")


class CollectionStats:
  def __init__(self, data):
    self.trusted = data.get("collection-trust-score", {}).get("trustedCount")
    self.untrusted = data.get("collection-trust-score", {}).get("needsVerificationCount")
    self.cards = data.get("card-count", {}).get("count")


class User:
  def __init__(self, data):
    user_obj = data.get("user") or data or {}
    self.email = user_obj.get("email")
    self.first_name = user_obj.get("firstName")
    self.last_name = user_obj.get("lastName")
    self.image = user_obj.get("profilePicUrl")
    self.status = user_obj.get("status")
    self.groups = [Group(group) for group in data.get("groups", [])]

  def has_group(self, group):
    return True if find_by_name_or_id(self.groups, group) else False


class Tag:
  def __init__(self, data):
    self.id = data.get("id")
    self.value = data.get("value")
    self.category = data.get("categoryName")
    self.category_id = data.get("categoryId")
  
  def json(self):
    return {
      "id": self.id,
      "value": self.value,
      "categoryName": self.category,
      "categoryId": self.category_id,
    }


class Verifier:
  def __init__(self, data):
    self.id = data.get("id")
    self.type = data.get("type")
    self.user = User(data.get("user")) if data.get("user") else None
    self.group = Group(data.get("userGroup")) if data.get("userGroup") else None


class Card:
  def __init__(self, data, guru=None):
    analytics = data.get("cardInfo", {}).get("analytics", {})
    self.guru = guru
    self.board_count = analytics.get("boards")
    self.copies = analytics.get("copies")
    self.favorites = analytics.get("favorites")
    self.unverified_copies = analytics.get("unverifiedCopies")
    self.unverified_views = analytics.get("unverifiedViews")
    self.views = analytics.get("views")
    self.type = data.get("cardType") or "CARD"
    self.collection = Collection(data.get("collection")) if data.get("collection") else None
    self.__content = data.get("content", "")
    self.created_date = data.get("dateCreated")
    self.id = data.get("id")
    self.item_id = data.get("itemId")
    self.last_modified_date = data.get("lastModified")
    self.last_modified_by = User(data.get("lastModifiedBy")) if data.get("lastModifiedBy") else None
    self.last_verified_by = User(data.get("lastVerifiedBy")) if data.get("lastVerifiedBy") else None
    self.next_verification_date = data.get("nextVerificationDate")
    self.owner = User(data.get("owner")) if data.get("owner") else None
    self.original_owner = User(data.get("originalOwner")) if data.get("originalOwner") else None
    self.title = data.get("preferredPhrase", "")
    self.share_status = data.get("shareStatus", "TEAM")
    self.slug = data.get("slug")
    self.tags = [Tag(item) for item in data.get("tags", [])]
    self.team_id = data.get("teamId")
    self.verification_initiation_date = data.get("verificationInitiationDate")
    self.verification_initiator = User(data.get("verificationInitiator")) if data.get("verificationInitiator") else None
    self.verification_interval = data.get("verificationInterval")
    self.verification_reason = data.get("verificationReason")
    self.verification_state = data.get("verificationState")
    self.verification_type = data.get("verificationType")
    self.verifiers = [Verifier(v) for v in data.get("verifiers") or []]
    self.version = data.get("version")
    self.archived = data.get("archived", False)
    self.favorited = data.get("favorited", False)
    self.boards = [Board(b, guru) for b in data.get("boards") or []]
    self.__doc = None

  @property
  def doc(self):
    if not self.__doc:
      self.__doc = BeautifulSoup(self.content, "html.parser")
    return self.__doc

  @property
  def content(self):
    return str(self.__doc) if self.__doc else self.__content

  @content.setter
  def content(self, content):
    self.__content = content
    if self.__doc:
      self.__doc = BeautifulSoup(content, "html.parser")

  @property
  def url(self):
    if self.slug:
      return "https://app.getguru.com/card/%s" % self.slug
    else:
      return ""

  def archive(self):
    return self.guru.archive_card(self)

  def favorite(self):
    return self.guru.favorite_card(self)
  
  def unfavorite(self):
    return self.guru.unfavorite_card(self)

  def patch(self, keep_verification=True):
    saved_card, status = self.guru.patch_card(self, keep_verification)
    return saved_card

  def save(self, verify=False):
    saved_card, status = self.guru.save_card(self, verify)
    # todo: figure out what all the properties are that we'd need to update.
    self.id = saved_card.id
    self.last_modified_by = saved_card.last_modified_by
    self.last_modified_date = saved_card.last_modified_date
    self.last_verified_by = saved_card.last_verified_by
    self.next_verification_date = saved_card.next_verification_date
    return saved_card
  
  def verify(self):
    return self.guru.verify_card(self)

  def unverify(self):
    return self.guru.unverify_card(self)

  def has_tag(self, tag):
    for t in self.tags:
      if t.value.lower() == tag.lower():
        return True
    return False
  
  def has_text(self, text, case_sensitive=False, include_title=True):
    card_title = self.title if case_sensitive else self.title.lower()
    card_content = self.doc.text if case_sensitive else self.doc.text.lower()
    text = text if case_sensitive else text.lower()

    if include_title and text in card_title:
      return True

    return text in card_content

  def add_tag(self, tag, create=False):
    if self.has_tag(tag):
      return True
    
    tag_object = self.guru.get_tag(tag)
    if tag_object:
      self.tags.append(tag_object)
      return True
    else:
      # todo: if create is True, make the tag.
      return False

  def comment(self, comment):
    return self.guru.add_comment_to_card(self, comment)

  def add_to_board(self, board, section=None):
    return self.guru.add_card_to_board(self, board, section)

  def json(self, verify=False):
    # if you accessed the doc object then we want to use its HTML so
    # any modifications you made are captured here.
    content = str(self.__doc) if self.__doc else self.content

    data = {
      "cardType": self.type,
      "collection": self.collection.json() if self.collection else None,
      "content": content,
      "id": self.id,
      "preferredPhrase": self.title,
      "shareStatus": self.share_status,
      "tags": [tag.json() for tag in self.tags],
      # if verify is false then we do want to suppress verification.
      "suppressVerification": not verify
    }

    if self.verification_interval:
      data["verificationInterval"] = self.verification_interval

    return data

  def lite_json(self):
    return {
      "type": "fact",
      "id": self.id,
      "itemId": self.item_id
    }


class Draft:
  def __init__(self, data, guru=None):
    self.guru = guru
    self.last_modified = data.get("lastModified")
    self.version = data.get("version")
    self.content = data.get("content")
    self.title = data.get("title")
    self.id = data.get("id")
    self.user = User(data.get("user") or {})
    self.json_content = data.get("jsonContent")
    self.save_type = data.get("saveType")


class CardComment:
  def __init__(self, data, card=None, guru=None):
    self.guru = guru
    self.card = card
    self.id = data.get("id")
    self.content = data.get("content")
    self.owner = User(data.get("owner")) if data.get("owner") else None
    self.created_date = data.get("dateCreated")
    self.last_modified_date = data.get("lastModified")

  def delete(self):
    return self.guru.delete_card_comment(self.card.id, self.id)
  
  def save(self):
    return self.guru.update_card_comment(self)
  
  def json(self):
    return {
      "content": self.content,
    }
