
import json

from guru.util import read_file, write_file


class Publisher:
  def __init__(self, g, name="", metadata=None, silent=False):
    self.g = g
    self.name = name or self.__class__.__name__

    # manage the json config file.
    if metadata is not None:
      self.__metadata = metadata
    else:
      self.__metadata = json.loads(
        read_file("./%s.json" % self.name) or "{}"
      )
      if not self.__metadata:
        self.__metadata = {}
    
    self.silent = silent
    self.__results = {}

  def get_external_url(self, external_id, card):
    raise NotImplementedError("get_external_url needs to be implemented so we can convert links between guru cards to be links between external articles.")

  def process_deletions(self):
    # figure out what objects need to be deleted and delete them.
    for guru_id in list(self.__metadata.keys()):
      # __results contains every object that was processed this time.
      # if we have metadata for an object but it wasn't processed, that means
      # it was removed from guru and needs to be deleted externally too.
      if guru_id not in self.__results:
        type = self.get_type(guru_id)
        external_id = self.get_external_id(guru_id)
        if type == "card":
          self.delete_external_card(external_id)
        elif type == "section":
          self.delete_external_section(external_id)
        elif type == "board":
          self.delete_external_board(external_id)
        elif type == "board_group":
          self.delete_external_board_group(external_id)
        elif type == "collection":
          self.delete_external_collection(external_id)
        
        # we hard delete this from the metadata so the next time this runs if
        # the object comes back, we treat it like a brand new object and call
        # the method to create it.
        self.__delete_metadata(guru_id, external_id)

  def find_external_collection(self, collection):
    pass
  
  def find_external_board_group(self, board_group):
    pass
  
  def find_external_board(self, board):
    pass
  
  def find_external_section(self, section):
    pass
  
  def find_external_card(self, card):
    pass
  
  # crud operations for cards.
  # these have to be implemented because you're always publishing cards.
  # sections, boards, etc. may be unimplemented because it's possible
  # thoe don't have any meaning in the system you're publishing to.
  def create_external_card(self, card, section, board, board_group, collection):
    raise NotImplementedError()
  
  def update_external_card(self, external_id, card, section, board, board_group, collection):
    raise NotImplementedError()
  
  def delete_external_card(self, external_id):
    raise NotImplementedError()

  # crud operations for sections.
  def create_external_section(self, section, board, board_group, collection):
    pass
  
  def update_external_section(self, external_id, section, board, board_group, collection):
    pass
  
  def delete_external_section(self, external_id):
    pass

  # crud operations for boards.
  def create_external_board(self, board, board_group, collection):
    pass
  
  def update_external_board(self, external_id, board, board_group, collection):
    pass
  
  def delete_external_board(self, external_id):
    pass
  
  # crud operations for board groups.
  def create_external_board_group(self, board_group, collection):
    pass
  
  def update_external_board_group(self, external_id, board_group, collection):
    pass
  
  def delete_external_board_group(self, external_id):
    pass
  
  # crud operations for collections.
  def create_external_collection(self, collection):
    pass
  
  def update_external_collection(self, external_id, collection):
    pass
  
  def delete_external_collection(self, external_id):
    pass

  def get_external_id(self, guru_id):
    return self.__metadata.get(guru_id, {}).get("external_id")
  
  def get_type(self, guru_id):
    return self.__metadata.get(guru_id, {}).get("type")

  def get_last_updated(self, guru_id):
    return self.__metadata.get(guru_id, {}).get("last_updated")

  def __update_metadata(self, guru_id, external_id="", type="", last_modified_date=None):
    if not self.__metadata.get(guru_id):
      self.__metadata[guru_id] = {}
    
    if last_modified_date:
      self.__log("update metadata", guru_id, "->", external_id, "last modified at", last_modified_date)
      self.__metadata[guru_id]["last_updated"] = last_modified_date
    else:
      self.__log("update metadata", guru_id, "->", external_id)
    
    if type:
      self.__metadata[guru_id]["type"] = type

    if external_id:
      self.__metadata[guru_id]["external_id"] = external_id
    
    write_file("./%s.json" % self.name, json.dumps(self.__metadata, indent=2))

  def __delete_metadata(self, guru_id, external_id):
    if guru_id in self.__metadata:
      del self.__metadata[guru_id]
      write_file("./%s.json" % self.name, json.dumps(self.__metadata, indent=2))

  def __log(self, *args):
    if not self.silent:
      print(*args)

  def publish_collection(self, collection):
    collection = self.g.get_collection(collection)
    home_board = self.g.get_home_board(collection)

    # call create/update/delete_collection as needed.
    external_id = self.get_external_id(collection.id)

    # todo: if we don't have an external_id, call find_external_collection to try to find it.

    if external_id:
      self.__results[collection.id] = "update"
      self.__log("update collection", external_id, collection.title)
      self.update_external_collection(external_id, collection)
    else:
      self.__results[collection.id] = "create"
      self.__log("create collection", collection.title)
      external_id = self.create_external_collection(collection)
    
    if external_id:
      self.__update_metadata(collection.id, external_id, type="collection")
    
    for item in home_board.items:
      if item.type == "board":
        # we load the board here because the data we have might be a 'lite' board.
        board = self.g.get_board(item.id)
        self.publish_board(board, collection, None)
      else:
        self.publish_board_group(item, collection)    
  
  def publish_board_group(self, board_group, collection=None):
    if collection:
      collection = self.g.get_collection(collection)
    board_group = self.g.get_board_group(board_group, collection)

    # call create/update/delete_board_group as needed.
    external_id = self.get_external_id(board_group.id)

    # todo: if we don't have an external_id, call find_external_board_group to try to find it.

    if external_id:
      self.__results[board_group.id] = "update"
      self.__log("update board group", external_id, board_group.title)
      self.update_external_board_group(external_id, board_group, collection)
    else:
      self.__results[board_group.id] = "create"
      self.__log("create board group", board_group.title)
      external_id = self.create_external_board_group(board_group, collection)
    
    if external_id:
      self.__update_metadata(board_group.id, external_id, type="board_group")

    for item in board_group.items:
      # we load the board here because the data we have might be a 'lite' board.
      board = self.g.get_board(item.id)
      self.publish_board(board, collection, board_group)

  def publish_board(self, board, collection=None, board_group=None):
    # this could be called where 'board' is an ID, slug, or Board object,
    # the same goes for collection.
    if collection:
      collection = self.g.get_collection(collection)
    board = self.g.get_board(board, collection)
    
    # call create/update/delete_board as needed.
    external_id = self.get_external_id(board.id)

    # todo: if we don't have an external_id, call find_external_board to try to find it.

    if external_id:
      self.__results[board.id] = "update"
      self.__log("update board", external_id, board.title)
      self.update_external_board(external_id, board, board_group, collection)
    else:
      self.__results[board.id] = "create"
      self.__log("create board", board.title)
      external_id = self.create_external_board(board, board_group, collection)
    
    if external_id:
      self.__update_metadata(board.id, external_id, type="board")
    
    for item in board.items:
      if item.type == "section":
        self.publish_section(item, collection, board_group, board)
      else:
        self.publish_card(item, collection, board_group, board)

  def publish_section(self, section, collection=None, board_group=None, board=None):
    # this can't be called directly so we can assume the args are all objects.
    
    # call create/update/delete_section as needed.
    external_id = self.get_external_id(section.id)

    # todo: if we don't have an external_id, call find_external_section to try to find it.

    if external_id:
      self.__results[section.id] = "update"
      self.__log("update section", external_id, section.title)
      self.update_external_section(external_id, section, board, board_group, collection)
    else:
      self.__results[section.id] = "create"
      self.__log("create section", section.title)
      external_id = self.create_external_section(section, board, board_group, collection)
    
    if external_id:
      self.__update_metadata(section.id, external_id, type="section")

    for item in section.items:
      self.publish_card(item, collection, board_group, board, section)

  def publish_card(self, card, collection=None, board_group=None, board=None, section=None):
    # call create/update/delete_card as needed.
    external_id = self.get_external_id(card.id)

    # if the card hasn't been updated since we last published it, we can skip it.
    # todo: could we do this by checking its version number?
    last_published_date = self.get_last_updated(card.id)
    if last_published_date and last_published_date >= card.last_modified_date:
      self.__results[card.id] = "skip"
      self.__log("skip card", card.title)
      return

    # scan the guru card for card to card links.
    # these should become links between external articles.
    # look for the 'data-ghq-guru-card-id' attribute and
    # set href="https://www.example.com/articles/<id>"
    for link in card.doc.select("[data-ghq-guru-card-id]"):
      other_card_id = link.attrs.get("data-ghq-guru-card-id")
      other_card = self.g.get_card(other_card_id)
      if other_card:
        other_card_external_id = self.get_external_id(other_card.id)
        new_url = self.get_external_url(other_card_external_id, other_card)
        if new_url:
          link.attrs["href"] = new_url

    # it's possible our json doesn't have a record of this card being published but it
    # does already exist externally -- maybe it was created there separately, maybe you
    # imported your content into guru and this is the first publish, etc.
    # to help in this situation we can check to see if the article exists -- you'd likely
    # make a call to get all articles and scan to see if there's one with this same title.
    if not external_id:
      self.__log("find card", card.title)
      external_id = self.find_external_card(card)
      if external_id:
        self.__log("found card!", card.title, "->", external_id)
    
    if external_id:
      self.__results[card.id] = "update"
      self.__log("update card", external_id, card.title)
      self.update_external_card(external_id, card, section, board, board_group, collection)
    else:
      self.__results[card.id] = "create"
      self.__log("create card", card.title)
      external_id = self.create_external_card(card, section, board, board_group, collection)
    
    if external_id:
      self.__update_metadata(
        card.id,
        external_id,
        last_modified_date=card.last_modified_date,
        type="card"
      )
