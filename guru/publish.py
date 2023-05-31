
import json
import requests

from guru.util import read_file, write_file


def is_successful(result):
  """
  result could either be a boolean or the response object.
  """
  if isinstance(result, requests.models.Response):
    return int(result.status_code / 100) == 2
  else:
    return result


class CardChanges:
  def __init__(self, content_changed, folders_added, folders_removed, tags_added, tags_removed):
    self.content_changed = content_changed
    self.folders_added = folders_added
    self.folders_removed = folders_removed
    self.tags_added = tags_added
    self.tags_removed = tags_removed

  def needs_publishing(self):
    if self.content_changed or self.folders_added or self.folders_removed or self.tags_added or self.tags_removed:
      return True
    else:
      return False


class Publisher:
  def __init__(self, g, name="", metadata=None, silent=False, dry_run=False, skip_unverified_cards=True):
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
    self.dry_run = dry_run
    self.skip_unverified_cards = skip_unverified_cards
    self.__results = {}
    self.messages = []

  def log_error(self, message):
    print("ERROR:", message)
    self.messages.append({
        "type": "error",
        "message": message
    })

  def log(self, message):
    print("LOG:", message)
    self.messages.append({
        "type": "info",
        "message": message
    })

  def get_external_url(self, external_id, card):
    raise NotImplementedError(
        "get_external_url needs to be implemented so we can convert links between guru cards to be links between external articles.")

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
        elif type == "folder":
          self.delete_external_folder(external_id)
        elif type == "collection":
          self.delete_external_collection(external_id)

        # we hard delete this from the metadata so the next time this runs if
        # the object comes back, we treat it like a brand new object and call
        # the method to create it.
        self.__delete_metadata(guru_id, external_id)

  def find_external_collection(self, collection):
    pass

  def find_external_folder(self, folder):
    pass

  def find_external_card(self, card):
    pass

  # crud operations for cards.
  # these have to be implemented because you're always publishing cards.
  # folders, etc. may be unimplemented because it's possible
  # thoe don't have any meaning in the system you're publishing to.
  def create_external_card(self, card, changes, folder, collection):
    raise NotImplementedError()

  def update_external_card(self, external_id, card, changes, folder, collection):
    raise NotImplementedError()

  def delete_external_card(self, external_id):
    raise NotImplementedError()

   # crud operations for folders.
  def create_external_folder(self, folder, collection):
    pass

  def update_external_folder(self, external_id, folder, collection):
    pass

  def delete_external_folder(self, external_id):
    pass

  def delete_external_folder(self, external_id):
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

  def get_folder_names(self, guru_id):
    return self.__metadata.get(guru_id, {}).get("folders") or []

  def get_tags(self, guru_id):
    return self.__metadata.get(guru_id, {}).get("tags") or []

  def get_card_changes(self, card):
    """
    This generates a CardChanges object which wraps up all the possible changes
    that can happen. Notably, this includes the folders the card was added to or
    removed from.
    """
    content_changed = False
    last_published_date = self.get_last_updated(card.id)
    if not last_published_date or card.last_modified_date > last_published_date:
      content_changed = True

    # figure out which folder assignments were added or removed.
    old_folder_names = set(self.get_folder_names(card.id))
    new_folder_names = set([f.title for f in card.folders])
    folders_added = list(new_folder_names - old_folder_names)
    folders_removed = list(old_folder_names - new_folder_names)

    # figure out which tags were added or removed.
    old_tags = set(self.get_tags(card.id))
    new_tags = set([t.value for t in card.tags])
    tags_added = list(new_tags - old_tags)
    tags_removed = list(old_tags - new_tags)

    return CardChanges(content_changed, folders_added, folders_removed, tags_added, tags_removed)

  def get_type(self, guru_id):
    return self.__metadata.get(guru_id, {}).get("type")

  def get_last_updated(self, guru_id):
    return self.__metadata.get(guru_id, {}).get("last_updated")

  def __update_metadata(self, guru_id, external_id="", type="", last_modified_date=None, folders=None, tags=None):
    if not self.__metadata.get(guru_id):
      self.__metadata[guru_id] = {}

    if last_modified_date:
      self.__log("update metadata", guru_id, "->", external_id,
                 "last modified at", last_modified_date)
      self.__metadata[guru_id]["last_updated"] = last_modified_date
    else:
      self.__log("update metadata", guru_id, "->", external_id)

    if type:
      self.__metadata[guru_id]["type"] = type

    if external_id:
      self.__metadata[guru_id]["external_id"] = external_id

    if folders != None:
      self.__metadata[guru_id]["folders"] = folders

    if tags != None:
      self.__metadata[guru_id]["tags"] = tags

    write_file("./%s.json" % self.name, json.dumps(self.__metadata, indent=2))

  def __delete_metadata(self, guru_id, external_id):
    if guru_id in self.__metadata:
      del self.__metadata[guru_id]
      write_file("./%s.json" % self.name,
                 json.dumps(self.__metadata, indent=2))

  def __log(self, *args):
    if not self.silent:
      print(*args)

  def publish_collection(self, collection):
    collection = self.g.get_collection(collection)
    home_folder = self.g.get_home_folder(collection)

    # call create/update/delete_collection as needed.
    external_id = self.get_external_id(collection.id)

    # if we don't have an external_id, call find_external_collection to try to find it.
    if not external_id:
      self.__log("find collection", collection.name)
      external_id = self.find_external_collection(collection)
      if external_id:
        self.__log("found collection!", collection.name, "->", external_id)

    successful = False
    if external_id:
      self.__results[collection.id] = "update"
      self.__log("update collection", external_id, collection.title)
      if not self.dry_run:
        result = self.update_external_collection(external_id, collection)
        successful = is_successful(result)
    else:
      self.__results[collection.id] = "create"
      self.__log("create collection", collection.title)
      if not self.dry_run:
        external_id = self.create_external_collection(collection)
        if external_id:
          successful = True

    if successful or external_id:
      self.__update_metadata(collection.id, external_id, type="collection")

    for item in home_folder.items:
      folder = self.g.get_folder(item.id)
      self.publish_folder(folder, collection, None)

  def publish_folder(self, folder, collection=None):
    # this could be called where 'folder' is an ID, slug, or Folder object,
    # the same goes for collection.
    if collection:
      collection = self.g.get_collection(collection)
    folder = self.g.get_folder(folder, collection)

    # call create/update/delete_folder as needed.
    external_id = self.get_external_id(folder.id)

    # if we don't have an external_id, call find_external_folder to try to find it.
    if not external_id:
      self.__log("find folder", folder.title)
      external_id = self.find_external_folder(folder)
      if external_id:
        self.__log("found folder!", folder.title, "->", external_id)

    successful = False
    if external_id:
      self.__results[folder.id] = "update"
      self.__log("update folder", external_id, folder.title)
      if not self.dry_run:
        result = self.update_external_folder(
            external_id, folder, collection)
        successful = is_successful(result)
    else:
      self.__results[folder.id] = "create"
      self.__log("create folder", folder.title)
      if not self.dry_run:
        external_id = self.create_external_folder(
            folder, collection)
        if external_id:
          successful = True

    if successful or external_id:
      self.__update_metadata(folder.id, external_id, type="folder")

    for item in folder.items:
      if item.type == "folder":
        self.publish_folder(item, collection, folder)
      else:
        self.publish_card(item, collection, folder)

  def publish_card(self, card, collection=None, folder=None):
    """
    This method figures out if the card has changes that need to be published and
    calls create/update_external_card based on whether the card has ever been
    published before or not.
    """
    external_id = self.get_external_id(card.id)

    # if we're configured to skip unverified cards and this one is unverified, skip it.
    if self.skip_unverified_cards and card.verification_state != "TRUSTED":
      self.__results[card.id] = "skip"
      self.__log("skip card", card.title)
      return

    # if there are no publish-worthy changes we can skip this card.
    changes = self.get_card_changes(card)
    if not changes.needs_publishing():
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

    successful = False
    if external_id:
      self.__results[card.id] = "update"
      self.__log("update card", external_id, card.title, card.folders)
      if not self.dry_run:
        result = self.update_external_card(
            external_id, card, changes, folder, collection)
        successful = is_successful(result)
    else:
      self.__results[card.id] = "create"
      self.__log("create card", card.title)
      if not self.dry_run:
        external_id = self.create_external_card(
            card, changes, folder, collection)
        if external_id:
          successful = True

    if successful:
      self.__update_metadata(
          card.id,
          external_id,
          last_modified_date=card.last_modified_date,
          folders=[f.title for f in card.folders],
          tags=[t.value for t in card.tags],
          type="card"
      )
    elif external_id:
      self.__update_metadata(
          card.id,
          external_id,
          type="card"
      )
