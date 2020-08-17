
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
    self.item_id = data.get("itemId")
    self.type = "board"
    
    if data.get("collection"):
      self.collection = Collection(data.get("collection"))
    else:
      self.collection = None
    
    self.items = []
    for item in data.get("items", []):
      if item.get("type") == "section":
        self.items.append(Section(item))
      else:
        self.items.append(Card(item))
  
  def set_item_order(self, *items):
    return self.guru.set_item_order(self.collection, self, *items)

  def json(self, include_items=True, include_collection=True):
    data = {
      "id": self.id,
      "type": self.type,
      "itemId": self.item_id,
      "title": self.title,
    }

    if include_items:
      data["items"] = [i.lite_json() for i in self.items]
    if self.collection and include_collection:
      data["collection"] = self.collection.json()
    
    return data

class BoardGroup:
  def __init__(self, data, guru=None, home_board=None):
    self.guru = guru
    self.home_board = home_board
    self.title = data.get("title")
    self.item_id = data.get("itemId")
    self.slug = data.get("slug")
    self.id = data.get("id")
    self.type = "board-group"
    self.items = [Board(b, guru) for b in data.get("items") or []]

  def set_item_order(self, *items):
    return self.guru.set_item_order(self.home_board.collection, self, *items)

  def json(self, include_items=True, include_collection=True):
    return {
      "id": self.id,
      "type": "section",
      "itemId": self.item_id,
      "title": self.title,
      "items": [i.json(include_items=False, include_collection=False) for i in self.items]
    }

class HomeBoard:
  def __init__(self, data, guru=None):
    self.guru = guru
    self.last_modified = data.get("lastModified")
    self.slug = data.get("slug")
    self.id = data.get("id")
    self.collection = Collection(data.get("collection"))
    self.items = []
    for item in data.get("items", []):
      if item.get("type") == "board":
        self.items.append(Board(item, guru, home_board=self))
      elif item.get("type") == "section":
        self.items.append(BoardGroup(item, guru, home_board=self))

  def set_item_order(self, *items):
    return self.guru.set_item_order(self.collection, self, *items)

  def json(self):
    return {
      "id": self.id,
      "collection": self.collection.json(),
      "items": [
        i.json(
          include_items=isinstance(i, BoardGroup),
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
  def __init__(self, data):
    self.id = data.get("id")
    self.name = data.get("name")
    self.type = data.get("collectionType")
    self.slug = data.get("slug")
    self.color = data.get("color")
  
  def json(self):
    return {
      "id": self.id,
      "name": self.name,
      "type": self.type,
      "color": self.color,
    }

class User:
  def __init__(self, data):
    user_obj = data.get("user") or {}
    self.email = user_obj.get("email")
    self.first_name = user_obj.get("firstName")
    self.last_name = user_obj.get("lastName")
    self.image = user_obj.get("profilePicUrl")
    self.status = user_obj.get("status")
    self.groups = [Group(group) for group in data.get("groups", [])]

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

class Card:
  def __init__(self, data, guru=None):
    self.guru = guru
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
    self.version = data.get("version")
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

  def add_tag(self, tag, create=False):
    for t in self.tags:
      if t.value.lower() == tag.lower():
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

  def json(self, verify=False):
    # if you accessed the doc object then we want to use its HTML so
    # any modifications you made are captured here.
    content = str(self.__doc) if self.__doc else self.content

    return {
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

  def lite_json(self):
    return {
      "type": "fact",
      "id": self.id,
      "itemId": self.item_id
    }

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
