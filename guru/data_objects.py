
import markdown
import copy
import re
from urllib.parse import quote
from bs4 import BeautifulSoup

from guru.util import clean_slug, find_by_name_or_id, find_by_id, compare_datetime_string


def find_urls_in_doc(doc):
  urls = set()
  # src and href attributes may contain urls.
  for image in doc.select('[src], [href]'):
    url = image.attrs.get("src")
    if url:
      urls.add(url)

    # todo: what if it's a relative url?
    url = image.attrs.get("href")
    if url:
      urls.add(url)

  return urls


class Section:
  """
  You can often refer to sections simply by their name. For example, when
  adding a card to a board, you can say `section="Onboarding"` to add the
  card to the Onboarding section.

  Sections do have more properties and if you need to reference them, you'll
  use the Section object. They have these properties:

  - `type`: always the string "section", but this is useful when you have a list
    of board items where each item could be a section or card and you want to check
    which type it is.
  - `title` the displayed title for this section.
  - `id` the internal Guru ID for the section.
  - `items` the list of Card objects for each card in the section.
  """

  def __init__(self, data, guru=None):
    self.guru = guru
    self.type = "section"
    self.title = data.get("title")
    self.id = data.get("id")
    self.item_id = data.get("itemId")
    self.items = [Card(i, guru=guru) for i in data.get("items") or []]

  def json(self):
    return {
        "type": "section",
        "id": self.id,
        "itemId": self.item_id,
        "items": [i.lite_json() for i in self.items]
    }

  def lite_json(self):
    return self.json()


class Folder:
  """
  The Folder object contains the folder's properties, like title and description,
  and also includes a list of the cards and other folders it contains.

  - `parent_folder` parameter is used to get a Folder reference to a Collection`s parent folder where other folders and Cards can exist.

  Here's a partial list of properties these objects have:

  - `title` is the folder's name as it's displayed in the UI.
  - `description` is an optional description.
  - `id` is the folder's internal ID.
  - `url` is the full URL for the folder.
  - `items` is the list of items on the folder, where each item can be a Card object or a Folder object.
  - `cards` is a list of Card objects for each card on the folder.
  - `folders` is a list of Folder objects for each folder on the folder.
  """

  def __init__(self, data, folder_items=[], guru=None, parent_folder=None):
    self.guru = guru
    self.parent_folder = parent_folder
    self.last_modified = data.get("lastModified")
    self.title = data.get("title")
    self.description = data.get("description")
    self.slug = data.get("slug")
    self.id = data.get("id")
    self.__item_id = data.get("itemId")
    self.type = "folder"
    self.__folder_items = folder_items
    self.__has_items = False

    if data.get("collection"):
      self.collection = Collection(data.get("collection"))
    else:
      self.collection = None

  # arrays to hold contents of the Folder.  Note: items array is exposed for other methods to add objects
  # such as cards or folders to the Folders object. e.g. add_card_to_folder() updates the items array
  # and will do a save_folder() call.
    self.__items = []
    self.__cards = []
    self.__folders = []

    # if folder_items were passed to Folders class, call __get_items to load them. Otherwise items will be lazy loaded when the .folders or .cards method is called.
    if self.__folder_items:
      self.__get_items()

  @property
  def url(self):
    if self.slug:
      return "https://app.getguru.com/folders/%s" % clean_slug(self.slug)
    else:
      return ""

  @property
  def item_id(self):
    if self.__item_id:
      return self.__item_id

    # load the parent folder (if necessary), find this folder, and set its item_id.
    if not self.parent_folder:
      self.parent_folder = self.get_parent_folder(self.collection)

    folder_item = find_by_id(self.parent_folder.folder, self.id)
    if not folder_item:
      print("could not find folder in the parent folder")
    else:
      self.__item_id = folder_item.item_id

    return self.__item_id

  @property
  def folders(self):
    # if we have already loaded items for this object...cool, if not go get em
    if not self.__has_items:
      self.__get_items()
    return tuple(self.__folders)

  @property
  def cards(self):
    # if we have already loaded items for this object...cool, if not go get em
    if not self.__has_items:
      self.__get_items()
    return tuple(self.__cards)

  @property
  def items(self):
    if not self.__has_items:
      self.__get_items()
    return tuple(self.__items)

  def update_lists(self, obj, action):
    """
    Updates internal items, and/or __card / __folders arrays when doing move/add/remove folders.

    Args: 
      obj (Folder/Card object, required) - the object to process
      action (add/remove, required) - what to do with the object

    Return: Nothing
    """
    if action == "remove" and self.__has_items:
      self.__items.remove(obj)
      if isinstance(obj, Card):
        self.__cards.remove(obj)
      elif isinstance(obj, Folder):
        self.__folders.remove(obj)
      else:
        return
    elif action == "add" and self.__has_items:
      self.__items.insert(0, obj)
      if isinstance(obj, Card):
        self.__cards.insert(0, obj)
      elif isinstance(obj, Folder):
        self.__folders.insert(0, obj)
      else:
        return

  def __get_items(self):
    """
      method to load items for a Folder.  Useful if the intent is to keep the references to the Folders and sub-Folders in tact.  Loads items on a Folder for those folders that were not already retrieved with a get_folder(<slug>) call.

    """

    # setting flag that we have attemped to retrieve items...
    self.__has_items = True

    # check to see if we have folder_items already in the object if we don't load them
    if not self.__folder_items:
      folder_items = self.guru.get_folder_items(self.slug)
    else:
      folder_items = self.__folder_items

    # process all items in the folder items and create appropriate objects
    for item in folder_items:
      if item.get("type") == "folder":
        folder = Folder(item, guru=self.guru)
        self.__items.append(folder)
        self.__folders.append(folder)
      else:
        card = Card(item, guru=self.guru)
        self.__items.append(card)
        self.__cards.append(card)

### BELOW ITEMS ARE NOT YET CONSIDERED FOR IMPLEMENTATION ###

  # def set_item_order(self, *items):
  #   """
  #   Rearranges the items on the board based on the list of strings
  #   you pass in here. For example, if you have a board about
  #   onboarding and it has sections called Week 1, Week 2, and Week 3,
  #   here's how you'd arrange them to make sure they're in order:

  #   ```
  #   board = g.get_board("TrE4qxgc")
  #   board.set_item_order("Week 1", "Week 2", "Week 3")
  #   ```

  #   Remember, the items on a board aren't all sections, it can be a
  #   mix of cards and sections. The strings you pass in here are expected
  #   to match section or card titles.

  #   Args:
  #     *items (str): Any number of strings that specifies the order
  #       you want the items to appear in.
  #   """
  #   return self.guru.set_item_order(self.collection, self, *items)

  # def get_card(self, card, section=None):
  #   if isinstance(card, Card):
  #     card = card.id

  #   # otherwise, first check for an immediate child card
  #   card_obj = find_by_name_or_id(self.items, card)
  #   if not card_obj:
  #     # then check all cards, including those in sections
  #     card_obj = find_by_name_or_id(self.__cards, card)
  #   return card_obj

  def add_card(self, card):
    """
    Adds a card to the folder. The card will be added to the top
    of the folder.

    Args:
      card (str or Card): The card to add to this folder. Can either be a Card object or a string
        that's the card's ID or slug.
    """
    return self.guru.add_card_to_folder(card, self)

  def move_card(self, card, folder):
    """
    Moves a card from this folder to another folder. The card will be added to the top of the folder

    Args:
      card (str, required) - The card Id or Ojbect in this folder to be moved
      folder (str, required) - The target folder Id or Object to move card to
    """
    return self.guru.move_card_to_folder(card, self, folder)

  # def remove_card(self, card):
  #   """
  #   Removes a card from the board.

  #   Args:
  #     card (str or Card): The card's ID or slug, or a Card object.
  #   """
  #   return self.guru.remove_card_from_board(card, self)

  # def get_groups(self):
  #   """
  #   Gets the list of groups the board has been shared with
  #   via board permissioning. This does not include the groups
  #   who can see the board due to the collection's permissioning.

  #   Returns:
  #     list of Group: A list of Group objects for each group the board has been shared with.
  #   """
  #   return self.guru.get_shared_groups(self)

  # def add_group(self, group):
  #   """
  #   Shares the board with an additional group.

  #   Args:
  #     group (str or Group): The group's ID or name, or a Group object.
  #   """
  #   return self.guru.add_shared_group(self, group)

  # def remove_group(self, group):
  #   """
  #   Removes a shared group from this board.

  #   Args:
  #     group (str or Group): The group's ID or name, or a Group object.
  #   """
  #   return self.guru.remove_shared_group(self, group)

  def move_to_collection(self, collection, timeout=0):
    #   """
    #   Moves the folder to a different collection.

    #   These operations are done asynchronously and can take a little while
    #   to complete. If you want to wait for the operation to complete you
    #   can pass in a `timeout` parameter -- this tells the SDK two things:
    #   first, that you want to wait for the operation to complete and second,
    #   how long it should wait.

    #   Args:
    #     collection (str or Collection): The collection's name or ID or a Collection object.
    #     timeout (int, optional): If you want to wait for the move to complete, this is the
    #       maximum amount of time (in seconds) that you'll wait. By default this is zero which
    #       means this function call returns before the folder has actually been moved to its
    #       new collection.
    #   """
    self.guru.move_folder_to_collection(self, collection, timeout)

  # def delete(self):
  #   """
  #   deletes board

  #   Returns:
  #     bool: True if it was successful and False otherwise.
  #   """
  #   return self.guru.delete_board(self, self.collection.id)

  def json(self, include_items=True, include_item_id=False, include_collection=True):
    data = {
        "id": self.id,
        "type": self.type,
        "title": self.title,
    }

    if include_items:
      data["items"] = [i.lite_json() for i in self.__items]
    if include_item_id:
      data["itemId"] = self.item_id
    if self.collection and include_collection:
      data["collection"] = self.collection.json()

    return data


class Board:
  """
  The Board object contains the board's properties, like title and description,
  and also includes a list of the cards and sections it contains.

  Here's a partial list of properties these objects have:

  - `title` is the board's name as it's displayed in the UI.
  - `description` is an optional description.
  - `id` is the board's internal ID.
  - `url` is the full URL for the board.
  - `items` is the list of items on the board, where each item can be a Card object or a Section object.
  - `cards` is a flattened list of Card objects for each card on the board.
  - `sections` is the list of Section objects for each section on the board.
  - `all_items` is a flattened list where each is a Card object or Section object. This is similar to the `items` list
    except a board with 2 sections (each containing 1 card) will have two items (just the sections) but `all_items` will
    have all four items.
  """

  def __init__(self, data, guru=None, home_board=None):
    self.guru = guru
    self.home_board = home_board
    self.last_modified = data.get("lastModified")
    self.title = data.get("title")
    self.description = data.get("description")
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
        section = Section(item, guru=guru)
        self.items.append(section)
        self.__sections.append(section)
        self.__all_items.append(section)
        self.__all_items += section.items
        self.__cards += section.items
      else:
        card = Card(item, guru=guru)
        self.items.append(card)
        self.__all_items.append(card)
        self.__cards.append(card)

    self.__load_all_cards()

  def __update_cards_in_list(self, item_list, lookup):
    # we scan the list and replace any partial card with its full card from the lookup.
    # we don't bother checking if something is a partial card because if it's in the
    # lookup dict, that means it must've been a partial card.
    for i in range(0, len(item_list)):
      partial_item = item_list[i]
      full_item = lookup.get(partial_item.id)
      if full_item:
        full_item = copy.copy(full_item)
        item_list[i] = full_item
        if partial_item.item_id:
          full_item.item_id = partial_item.item_id

  def __load_all_cards(self):
    # identify the partially-loaded cards.
    # these come from boards that have more than 50 cards.
    # sometimes the API returns a 'lite' board that doesn't have items at all. these will
    # naturally skip over most of this logic because their items list is missing or empty
    # so we don't have any card IDs to try to load.
    unloaded_card_ids = []
    for card in self.__cards:
      if not card.title:
        unloaded_card_ids.append(card.id)

    # if the board has < 50 cards this list will be empty and we can stop early.
    if not unloaded_card_ids:
      return

    # load the unloaded cards in batches of 50.
    # our API does enforce a max of 50.
    card_lookup = {}
    for index in range(0, len(unloaded_card_ids), 50):
      batch_ids = unloaded_card_ids[index:index + 50]
      data = self.guru.get_cards(batch_ids)
      for id in data:
        card_lookup[id] = data[id]

    # now that we have the full card objects, we update the entries in all the existing lists.
    self.__update_cards_in_list(self.items, card_lookup)
    self.__update_cards_in_list(self.__cards, card_lookup)
    self.__update_cards_in_list(self.__all_items, card_lookup)
    for section in self.__sections:
      self.__update_cards_in_list(section.items, card_lookup)

  @property
  def url(self):
    if self.slug:
      return "https://app.getguru.com/boards/%s" % self.slug
    else:
      return ""

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

  def get_section(self, section):
    """
    Returns the Section object matching the specified section name or ID.

    Args:
      section (str): The section's name or ID.

    Returns:
      Section: the Section object or None if it wasn't found.
    """
    return find_by_name_or_id(self.sections, section)

  def has_section(self, section):
    """
    Returns True if the board contains the section and False if it doesn't.
    Other operations, like adding a section, doesn't check for duplicates
    so here's how we can do that:

    ```
    import guru
    g = guru.Guru()

    board = g.get_board("TrE4qxgc")
    if not board.has_section("Week 2"):
      board.add_section("Week 2"):
    ```

    Args:
      section (str): The section's name or ID.

    Returns:
      bool: True if the board contains the section and False otherwise.
    """
    return True if self.get_section(section) else False

  def add_section(self, name):
    """
    Adds a section to the board. The new section is added at the end of the
    board. If the board already has a section by this name, this _will_ add another.

    ```
    import guru
    g = guru.Guru()

    # we can load a board using its slug, which we find from its URL:
    # https://app.getguru.com/boards/TrE4qxgc/Onboarding
    board = g.get_board("TrE4qxgc")
    board.add_section("Week 2")
    ```

    Args:
      name (str): The name of the section to add.
    """
    self.guru.add_section_to_board(self, name)

  def set_item_order(self, *items):
    """
    Rearranges the items on the board based on the list of strings
    you pass in here. For example, if you have a board about
    onboarding and it has sections called Week 1, Week 2, and Week 3,
    here's how you'd arrange them to make sure they're in order:

    ```
    board = g.get_board("TrE4qxgc")
    board.set_item_order("Week 1", "Week 2", "Week 3")
    ```

    Remember, the items on a board aren't all sections, it can be a
    mix of cards and sections. The strings you pass in here are expected
    to match section or card titles.

    Args:
      *items (str): Any number of strings that specifies the order
        you want the items to appear in.
    """
    return self.guru.set_item_order(self.collection, self, *items)

  def get_card(self, card, section=None):
    if isinstance(card, Card):
      card = card.id

    # check in the given section if provided
    if section:
      section_obj = self.get_section(section)
      if not section_obj:
        return None
      return find_by_name_or_id(section_obj.items, card)

    # otherwise, first check for an immediate child card
    card_obj = find_by_name_or_id(self.items, card)
    if not card_obj:
      # then check all cards, including those in sections
      card_obj = find_by_name_or_id(self.__cards, card)
    return card_obj

  def add_card(self, card, section=None):
    """
    Adds a card to the board. The card will be added to the end
    of the board. If a section name is provided, the card will
    be added inside that section. If the section doesn't exist
    on the board it will _not_ be created.

    ```
    import guru
    g = guru.Guru()

    # we use slugs (the IDs found in URLs) to specify which
    # board we're loading and what card we're adding to it.
    board = g.get_board("TrE4qxgc")
    board.add_card("Tbbqo5pc")
    ```

    Args:
      card (str or Card): The card to add to this board. Can either be a Card object or a string
        that's the card's ID or slug.
      section (str, optional): The name of the section to add the card to.
    """
    return self.guru.add_card_to_board(card, self, section=section, collection=self.collection)

  def remove_card(self, card):
    """
    Removes a card from the board.

    Args:
      card (str or Card): The card's ID or slug, or a Card object.
    """
    return self.guru.remove_card_from_board(card, self)

  def get_groups(self):
    """
    Gets the list of groups the board has been shared with
    via board permissioning. This does not include the groups
    who can see the board due to the collection's permissioning.

    Returns:
      list of Group: A list of Group objects for each group the board has been shared with.
    """
    return self.guru.get_shared_groups(self)

  def add_group(self, group):
    """
    Shares the board with an additional group.

    Args:
      group (str or Group): The group's ID or name, or a Group object.
    """
    return self.guru.add_shared_group(self, group)

  def remove_group(self, group):
    """
    Removes a shared group from this board.

    Args:
      group (str or Group): The group's ID or name, or a Group object.
    """
    return self.guru.remove_shared_group(self, group)

  def move_to_collection(self, collection, timeout=0):
    """
    Moves the board to a different collection.

    These operations are done asynchronously and can take a little while
    to complete. If you want to wait for the operation to complete you
    can pass in a `timeout` parameter -- this tells the SDK two things:
    first, that you want to wait for the operation to complete and second,
    how long it should wait.

    Args:
      collection (str or Collection): The collection's name or ID or a Collection object.
      timeout (int, optional): If you want to wait for the move to complete, this is the
        maximum amount of time (in seconds) that you'll wait. By default this is zero which
        means this function call returns before the board has actually been moved to its
        new collection.
    """
    self.guru.move_board_to_collection(self, collection, timeout)

  def delete(self):
    """
    deletes board

    Returns:
      bool: True if it was successful and False otherwise.
    """
    return self.guru.delete_board(self, self.collection.id)

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
  """
  The Group object represents a group of users. Often we refer to
  these groups simply by name, but internally they each have an ID.
  You can do a lot of operation, like adding users to groups, only
  using each group's name. Other operations, like getting the list
  of groups with access to a collection, will return full Group objects.

  The Group object has these properties:

  - `id` the internal Guru ID for the group.
  - `name` the group's displayed name.
  - `date_created` the timestamp of when the group was created.
  - `modifiable` True if the group can be modified. Some groups, like All Members,
    are managed by Guru and aren't editable.
  """

  def __init__(self, data, guru=None):
    self.guru = guru
    self.date_created = data.get("dateCreated")
    self.modifiable = data.get("modifiable")
    self.id = data.get("id")
    self.identifier = data.get("groupIdentifier")
    self.name = data.get("name")

  def get_members(self):
    """
    Gets the list of all users in the group.

    Returns:
      list of User: a list of User objects representing the set of users in this group.
    """
    return self.guru.get_group_members(self)


class Collection:
  """
  The Collection object is used to represent a collection. You can often
  reference a collection using only its name, like when you are creating a
  new card you can simply say `collection="Engineering"`. When you get a
  collection or list of all collections, these Collection objects are what
  you get back.

  It has these properties:

  - `id` the internal Guru ID for the collection.
  - `name` the collection's displayed name.
  - `title` is also the collection's name. You can use `title` or `name` interchangeably.
  - `description` the collection's displayed description.
  - `color` the collection's displayed color.
  - `type` either "INTERNAL" or "EXTERNAL", external collections are ones whose
    content is synced and is not editable in Guru.
  - `public_cards_enabled` whether or not public cards can be created in this collection.
  """

  def __init__(self, data, guru=None):
    self.guru = guru

    # these are the properties you always get, like when a card has a nested
    # collection object with just a few properties.
    self.id = data.get("id")
    self.name = data.get("name")
    self.type = data.get("collectionType")
    self.slug = data.get("slug")
    self.homeFolderSlug = data.get("homeBoardSlug")
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

  @ title.setter
  def title(self, title):
    self.name = title

  def add_group(self, group, role):
    """
    Gives a group access to the collection. When you add a group you have
    to also assign it a role: Read-only, Author, or Collection Owner.

    Args:
      group (str or Group): The name or ID of the group or a Group object.
      role (str): one of these values: guru.READ_ONLY, guru.AUTHOR, or guru.COLLECTION_OWNER.
    """
    return self.guru.add_group_to_collection(group, self, role)

  def remove_group(self, group):
    """
    Remove a group's access from the collection. When you do this, users may
    lose access to content in the collection. This can trigger some things that
    you can't easily undo -- for example, any cards in this collection that were
    in a user's favorites list will be removed (as they no longer have access to
    the card). Even if you restore their access, the card has already been
    removed from their favorites and won't be added back.

    If you're adjusting group permissions, it's best to add all new groups then
    remove the old ones. For example, if you're splitting the "Product" group into
    four smaller groups, you'd add the four new ones then remove the old one.
    """
    return self.guru.remove_group_from_collection(group, self)

  def get_groups(self):
    """
    Gets the list of all groups that have access to the collection.

    Returns:
      list of CollectionAccess: A list of CollectionAccess objects.
    """
    return self.guru.get_groups_on_collection(self)

  def json(self):
    return {
        "id": self.id,
        "name": self.name,
        "type": self.type,
        "color": self.color,
    }


class Framework:
  """
  The Framework object is used to represent a framework, used to a import as a new collection.
  These objects simply have these properties:
  - `id`
  - `collection`
  """

  def __init__(self, data, guru=None):
    self.guru = guru
    self.id = data.get("id")
    self.name = data.get("collection").get("name")
    self.collection = Collection(data.get("collection"), guru=guru)

  @property
  def title(self):
    return self.name

  @ title.setter
  def title(self, title):
    self.name = title

  def import_framework(self):
    return self.guru.import_framework(self)


class CollectionAccess:
  """
  The CollectionAccess object is used to represent a group's assignment
  to a collection. These objects simply have these properties:

  - `group_name`
  - `group_id`
  - `role`
  """

  def __init__(self, data):
    self.group_name = data.get("groupName")
    self.group_id = data.get("groupId")
    self.role = data.get("role")


class CollectionStats:
  def __init__(self, data):
    self.trusted = data.get(
        "collection-trust-score", {}).get("trustedCount")
    self.untrusted = data.get(
        "collection-trust-score", {}).get("needsVerificationCount")
    self.cards = data.get("card-count", {}).get("count")


class User:
  """
  The User object represents data we get back when loading a list of
  users or as a card's author, verifier, etc.

  These objects have properties like:

  - `email`
  - `first_name`
  - `last_name`
  - `groups` - when you load a list of users (i.e. from calling `g.get_members()`) the User
    objects that come back have a list of groups for each user.
  """

  def __init__(self, data):
    user_obj = data.get("user") or data or {}
    user_attr = data.get("userAttributes", {})
    self.email = user_obj.get("email")
    self.first_name = user_obj.get("firstName")
    self.last_name = user_obj.get("lastName")
    self.image = user_obj.get("profilePicUrl")
    self.status = user_obj.get("status")
    self.billing_type = user_attr.get("BILLING_TYPE")
    self.access_type = user_attr.get("ACCESS_TYPE")
    self.groups = [Group(group) for group in data.get("groups", [])]

  @property
  def full_name(self):
    """String combining first and last name of `User`

    Returns:
        str | None: first and last name ( if none exists, will return `None`)
    """
    if self.first_name and self.last_name:
      return '%s %s' % (self.first_name, self.last_name)
    else:
      return self.email

  @property
  def is_light(self):
    """Boolean telling if user is a light user"""
    return self.access_type == "READ_ONLY" and self.billing_type == "FREE"

  @property
  def is_core(self):
    """Boolean telling if user is a core user"""
    return self.access_type == "CORE" and self.billing_type == "CORE"

  def has_group(self, group):
    """
    Returns True if the user is a member of the specified group.

    ```
    import guru
    g = guru.Guru()

    for user in g.get_members():
      if user.has_group("Engineering") and user.has_group("Product"):
        print("%s is in the Engineering and Product groups" % user.email)
    ```

    Args:
      group (str or Group): The name or ID of the group or the Group object.

    Returns
      bool: True if the user is in that group and False if they're not.
    """
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
  """
  A card's verifier can be an individual user or a group, so we
  use the Verifier object to represent that. Each Card object has
  a `verifier` property, which is a Verifier object that'll have
  a reference to a User object or Group object.

  Question objects also use a Verifier object as their `answerer`
  property, since questions can be asked to an individual or a group.

  These are the properties a Verifier object has:

  - `type`: Either the string `"user-group"` or `"user"`.
  - `id`: The user's email address (if it's an individual verifier) or
    the ID of the Group verifier.
  - `user`: A User object, if the verifier is an individual user. `None`
    if the verifier is a group.
  - `group`: A Group object, if the verifier is a group. `None` if the
    verifier is a user.
  """

  def __init__(self, data):
    self.id = data.get("id")
    self.type = data.get("type")
    self.user = User(data.get("user")) if data.get("user") else None
    self.group = Group(data.get("userGroup")) if data.get(
        "userGroup") else None


class Card:
  """
  The Card object is used to represent card data we get back from
  calls like get_card or find_cards.

  ```
  import guru
  g = guru.Guru()

  # we can use the 'slug' part of this URL to load a card:
  # https://app.getguru.com/card/Tbbqo5pc/Getting-Started-with-the-Guru-SDK
  card = g.get_card("Tbbqo5pc")
  card.favorite()
  card.add_tag("SDK")
  card.add_to_board("Shared Docs", section="API & SDK")
  ```

  This object has a lot of properties and I encourage you to experiment
  and see what all is available, but here's a short list:

  - `id` is the 8-4-4-4-12 hexadecimal ID assigned to this card. These IDs
    are helpful when matching cards to events returned by `get_events()`.
  - `title` is the card's title.
  - `content` is the card's HTML content as a string.
  - `doc` is the card's content parsed as an HTML document. This uses Beautiful
    Soup and you check check [its docs](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
    for more info.
  - `collection` is a Collection object representing the collection this card is in.
  - `boards` is a list of Board objects for all the boards this card is on.
  - `url` is the full URL you can use to access the card in Guru's webapp.
  - `verifier_label` is a string representing the verifier -- either the group name if it's
    assigned to a group or the individual verifier's email address.

  This object also has a lot of methods that make it easy to do
  things like verify, unverify, update, archive, add tags, add
  comments, etc.
  """

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
    self.collection = Collection(
        data.get("collection")) if data.get("collection") else None
    self.__content = data.get("content", "")
    self.created_date = data.get("dateCreated")
    self.id = data.get("id")
    self.item_id = data.get("itemId")
    self.last_modified_date = data.get("lastModified")
    self.last_modified_by = User(data.get("lastModifiedBy")) if data.get(
        "lastModifiedBy") else None
    self.last_verified_by = User(data.get("lastVerifiedBy")) if data.get(
        "lastVerifiedBy") else None
    self.last_verified_date = data.get("lastVerified")
    self.next_verification_date = data.get("nextVerificationDate")
    self.owner = User(data.get("owner")) if data.get("owner") else None
    self.original_owner = User(data.get("originalOwner")) if data.get(
        "originalOwner") else None
    self.title = data.get("preferredPhrase", "")
    self.share_status = data.get("shareStatus", "TEAM")
    self.slug = data.get("slug")
    self.tags = [Tag(item) for item in data.get("tags", [])]
    self.team_id = data.get("teamId")
    self.verification_initiation_date = data.get(
        "verificationInitiationDate")
    self.verification_initiator = User(data.get(
        "verificationInitiator")) if data.get("verificationInitiator") else None
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
    """
    The `doc` property is a [BeautifulSoup object](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
    that represents the card's content. This is created by parsing the card's
    HTML content so you can easily do operations like finding all images in
    a card and printing their URLs:

    ```
    for card in g.find_cards(collection="General"):
      for image in card.doc.select("img"):
        print(image.attrs.get("src"))
    ```
    """
    if not self.__doc:
      self.__doc = BeautifulSoup(self.content, "html.parser")
    return self.__doc

  @property
  def content(self):
    """
    The card's content as either HTML or Markdown. Most cards
    have HTML content. Any card created through Guru's UI will
    have HTML content but cards created through the API can have
    their content as Markdown.
    """
    return str(self.__doc) if self.__doc else self.__content

  @ content.setter
  def content(self, content):
    self.__content = content
    if self.__doc:
      self.__doc = BeautifulSoup(content, "html.parser")

  @property
  def url(self):
    """
    Returns the card's URL. You can piece this together yourself
    using the card's `slug` property, but why bother!

    ```
    card = g.get_card("Tbbqo5pc")

    # prints: Tbbqo5pc/Getting-Started-with-the-Guru-SDK
    print(card.slug)

    # prints: https://app.getguru.com/card/Tbbqo5pc/Getting-Started-with-the-Guru-SDK
    print(card.url)
    ```
    """
    if self.slug:
      return "https://app.getguru.com/card/%s" % self.slug
    else:
      return ""

  @property
  def verifier_label(self):
    """
    This is a string that represents the card's verifier.
    Since the verifier can be a group or user, rather than figuring out
    if you want to use the group's name or the user's email address, you
    can simply refer to `card.verifier_label`, like this:

    ```
    import guru
    g = guru.Guru()

    # print the verifier for each card in the Engineering collection:
    for card in g.find_cards(collection="Engineering"):
      print(card.verifier_label, card.url)
    ```

    Some cards do not have a verifier, in which case the label will be
    the string `"no verifier"`.
    """
    if not self.verifiers:
      return "no verifier"

    verifier = self.verifiers[0]
    if verifier.group:
      return verifier.group.name
    else:
      return verifier.user.email

  @property
  def interval_label(self):
    """
    This is a string that represents the card's verification interval,
    like it is displayed in Card Manager.
    It can be used like this:

    ```
    import guru
    g = guru.Guru()

    # print the text representation of the verification interval
    # for each card in the Engineering collection:
    for card in g.find_cards(collection="Engineering"):
      print(card.interval_label)

    # outputs: 3 months, etc...
    ```

    If a card has an absolute date interval, the label will be
    the string `"On a specific date"`.
    """
    interval = self.verification_interval
    interval_string = "Every %s"
    interval_map = {
        7: interval_string % "week",
        14: interval_string % "2 weeks",
        30: interval_string % "month",
        90: interval_string % "3 months",
        180: interval_string % "6 months",
        365: interval_string % "year",
    }
    return interval_map.get(interval, "On a specific date")

  def archive(self):
    """
    Archives the card.
    """
    return self.guru.archive_card(self)

  def restore(self):
    """
    Restores an archived card.
    """
    return self.guru.restore_card(self)

  def favorite(self):
    """
    Adds the card to your favorites list. The Guru object is given a username
    and API token -- that's the user whose favorites list we're adding to. If
    you want to favorite a card for someone else you'll need to have their
    username and API token.
    """
    return self.guru.favorite_card(self)

  def unfavorite(self):
    """
    Removes a card from your favorites list.
    """
    return self.guru.unfavorite_card(self)

  def patch(self, keep_verification=True):
    """
    Updates the card's title and content. If you're a collection owner you can also
    use the `keep_verification` flag to make this update without affecting the card's
    trust state -- normally, if you're not the verifier, the card will become
    unverified when you edit it. With keep_verification=True, it'll remain verified
    even if you're not the verifier! This is especially helpful when you're updating
    a card to replace a term in its content or title.

    Args:
      keep_verification (bool): True if you want the card to remain in its current
        trust state, False if you want the normal verification rules to apply (meaning
        your edit may cause the card to become unverified).
    """
    saved_card, status = self.guru.patch_card(self, keep_verification)
    return saved_card, status

  def save(self, verify=False):
    """
    Saves the card. You can pass an optional `verify` parameter to say whether
    you want to save & verify, or just save -- similar to the two buttons you'd
    see in the editor while editing a card.

    Args:
      verify (bool, optional): True if you want to also verify the card, False if
        you want to leave its trust state alone. Defaults to False.
    """
    saved_card, status = self.guru.save_card(self, verify)
    # todo: figure out what all the properties are that we'd need to update.
    self.id = saved_card.id
    self.last_modified_by = saved_card.last_modified_by
    self.last_modified_date = saved_card.last_modified_date
    self.last_verified_by = saved_card.last_verified_by
    self.next_verification_date = saved_card.next_verification_date
    return saved_card

  def verify(self):
    """
    Verifies the card.
    """
    return self.guru.verify_card(self)

  def unverify(self):
    """
    Unverifies the card.
    """
    return self.guru.unverify_card(self)

  def has_tag(self, tag):
    """
    Checks if the card has a particular tag applied to it.

    Args:
      tag (str): The name of the tag you're looking for.

    Returns:
      bool: True if the card has the tag and False otherwise.
    """
    for t in self.tags:
      if t.value.lower() == tag.lower():
        return True
    return False

  def has_text(self, text, case_sensitive=False, include_title=True):
    """
    Checks if the card contains a particular string. This is useful when you're
    looking to update a term or name. For eample, if you changed the name of your
    product-feedback channel, you can use this to find the affected cards:

    ```
    import guru
    g = guru.Guru()

    for card in g.find_cards():
      if card.has_text("product-feedback"):
        print(card.url)
    ```

    If you searched Guru for "product-feedback" you'll find cards that contain
    just the word "feedback". Using `has_text()` checks that the card contains
    this exact string.

    Args:
      case_sensitive (bool, optional): True if you want the comparison to be case
        sensitive (i.e. has_text("guru") will _not_ match "Guru"). False if you
        want it to be case insensitive (i.e. "guru" _will_ match "Guru"). This
        parameter is False by default.
      include_title (bool, optional): True if you want to check the card's title
        too and False if you want to skip checking the title. This is True (it checks
        the title) by default.

    Returns:
      bool: True if the card contains the term, False if it doesn't.
    """
    card_title = self.title if case_sensitive else self.title.lower()
    # note: if the card contains markdown blocks, this'll work fine. if the card is
    #       entirely a markdown card, checking doc.text will consider link and image
    #       urls since it essentially treats the card as one big text node.
    card_content = self.doc.text if case_sensitive else self.doc.text.lower()
    text = text if case_sensitive else text.lower()

    if include_title and text in card_title:
      return True

    return text in card_content

  def find_urls(self):
    """
    Gets a list of all URLs found in the card's content. This includes
    images, iframes, and links. It also includes links inside Markdown
    blocks or in cards whose content is pure Markdown. It does not
    include URLs that are just text, like if you type "https://www.example.com"
    in a paragraph but it's not a link.
    """
    # this checks images, iframes, and links.
    urls = find_urls_in_doc(self.doc)

    # the card may be entirely markdown or just contain some markdown so we convert its text
    # to html then look for urls there.
    html = markdown.markdown(self.doc.text)
    doc = BeautifulSoup(html, "html.parser")
    urls = urls.union(find_urls_in_doc(doc))

    return list(urls)

  def replace_url(self, old_url, new_url):
    """
    Replaces the occurrence of one URL with another. This is different
    than replacing text because we want to target HTML attributes (image
    URLs, link URLs, etc.). It also handles making replacements inside
    of Markdown blocks.

    Args:
      old_url (str): The URL to be replaced.
      new_url (str): The value to replace it with.

    Returns:
      bool: True if any replacements were made, False if no changes were made.
    """
    modified = False
    if old_url in self.content:
      # todo: what if we match a prefix of a URL? like, the card contains example.com/test.png
      #       and we replace "example.com" with "google.com", should it become google.com/test.png?
      self.content = self.content.replace(old_url, new_url)
      modified = True

    # escape the url and then do the replacement so markdown blocks are covered too.
    old_md_url = quote(old_url)
    new_md_url = quote(new_url)

    if old_md_url in self.content:
      self.content = self.content.replace(old_md_url, new_md_url)
      modified = True

    return modified

  def add_tag(self, tag, create=False):
    """
    Adds the tag to the card and saves this change.

    Args:
      tag (Tag or str): Either the name of the tag (e.g. "case study") or the Tag object.
      create (bool, optional): This tells the SDK if it should create the tag if it doesn't
        already exist. Defaults to False.
    """
    if self.has_tag(tag):
      return True

    tag_object = self.guru.add_tag_to_card(tag, self, create=create)
    self.tags.append(tag_object)

  def remove_tag(self, tag):
    """
    Removes the tag from the card and saves this change.

    Args:
      tag (Tag or str): Either the name of the tag (e.g. "case study") or the Tag object.

    Returns:
      bool: True if it was successful and False otherwise.
    """
    # it's possible we won't find the tag in the card's list of tags but the card
    # does really have the tag. this could happen because the card data didn't include
    # its list of tags or because the data is out of sync. so, we use 'tag' as a
    # fallback because passing a string into remove_tag_from_card will make it look
    # up the tag ID.
    tag = find_by_name_or_id(self.tags, tag) or tag
    result = self.guru.remove_tag_from_card(tag, self)

    # if it was successful, we update the card object.
    if result and isinstance(tag, Tag):
      self.tags.remove(tag)

    return result

  def add_comment(self, comment):
    """
    Adds a comment to the card. Remmeber, the Guru object is given a single user's
    username and API token and all comments will be made as that user. If you want
    to make comments as different users, you'll need each user's username and API
    token.

    Args:
      comment (str): The content of the comment.
    """
    return self.guru.add_comment_to_card(self, comment)

  def get_open_card_comments(self):
    return self.guru.get_card_comments(self, status="OPEN")

  def get_resolved_card_comments(self):
    return self.guru.get_card_comments(self, status="RESOLVED")

  def add_to_board(self, board, section=None, board_group=None):
    """
    Adds the card to a board.

    Args:
      board (str or Board): The name of the board you're adding the card to, or the Board object.
      section (str, optional): The name of the section to add this card to.
    """
    return self.guru.add_card_to_board(self, board, section, collection=self.collection)

  def remove_from_board(self, board):
    """
    Removes the card from a board.

    Args:
      board (str or Board): The name of the board you're removing the card from, or the Board object.

    Returns:
      bool: True if it was successful and False otherwise.
    """
    return self.guru.remove_card_from_board(self, board, self.collection)

  def move_to_collection(self, collection, timeout=0):
    return self.guru.move_card_to_collection(self, collection, timeout=timeout)

  def download_as_pdf(self, filename):
    return self.guru.download_card_as_pdf(self, filename)

  def json(self, verify=False):
    """internal"""
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
    """internal"""
    data = {
        "type": "fact",
        "id": self.id
    }
    if self.item_id:
      data["itemId"] = self.item_id

    return data


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

  def resolve(self):
    return self.guru.resolve_card_comment(self)

  def unresolve(self):
    return self.guru.reopen_card_comment(self)

  def save(self):
    return self.guru.update_card_comment(self)

  def is_before(self, date):
    return compare_datetime_string(self.created_date, "lt", date_to_compare_against=date)

  def is_after(self, date):
    return compare_datetime_string(self.created_date, "gt", date_to_compare_against=date)

  def json(self):
    return {
        "content": self.content,
    }


class Question:
  """
  Represents a question we get back from calling `get_questions_inbox()`.

  ```
  import guru
  g = guru.Guru()

  # print each question and who asked it:
  for question in g.get_questions_inbox():
    print(question.asker.email, question.question)
  ```

  Here are some of the properties that Questions have:

  - `answerer` is a Verifier object which contains a reference to a Group object or a User object.
  - `asker` is the User object of who asked the question.
  - `created_date` is when the question was asked.
  """

  def __init__(self, data, guru=None):
    self.guru = guru
    self.answerer = Verifier(
        data.get("answerer")) if data.get("answerer") else None
    self.answerable = data.get("answerable", None)
    self.archivable = data.get("archivable", None)
    self.asker = User(data.get("asker")) if data.get("asker") else None
    self.id = data.get("id")
    self.question = data.get("question")
    self.created_date = data.get("createdDate")
    # i am not sure what we use this for, so i don't know if customers would need it.
    # when we archive a question we use its id, not its question_id.
    # self.question_id = data.get("questionId")
    self.last_activity = data.get("lastActivityType")
    self.last_activity_date = data.get("lastActivityDate")
    self.last_activity_by = User(data.get("lastActivityUser")) if data.get(
        "lastActivityUser") else None

  def archive(self):
    """
    Deletes a question.

    Returns
      bool: True if it was successful and False otherwise.
    """
    return self.guru.delete_question(self)

  def dismiss(self):
    """
    Deletes a question. This does the same thing as the `archive()` method
    the different is just its name. We say "dismiss" when we're deleting a
    question in your inbox and "archive" when it's a question you sent.

    Returns
      bool: True if it was successful and False otherwise.
    """
    return self.guru.delete_question(self)
