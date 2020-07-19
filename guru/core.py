
# todo: make guru card links to boards work.
#       the problem here is it links to the board's url which gives us the board's ID but we
#       want to link to "{id}_content" instead of just linking to the ID.
# todo: add methods to the Guru object for doing searches, creating/updating cards, etc.
# 
# done: make an option to create "top-heavy" or "bottom-heavy" hierarchies.
#       one means you'd have: BOARD GROUP > BOARD > CARD
#       the other means you'd have: BOARD > SECTION > CARD
# done: collapse nested cards inside a section.
#       this was already getting flattened when we make the yaml so i just needed
#       to update how it prints the tree to limit the indentation it prints.
# done: check for cycles
#       if a node has its parent as a child the recursion will go on forever.
#       we can check for this inside add_child.
# done: convert URLs lacking a protocol to include "https:" (check src and srcset attributes)
#       for now we're just removing the srcset attribute.
# done: keep track of a node's parents (maybe replace the 'root' flag with a list of parent nodes).
#       this'll make it easier to check for cycles.
# done: split this into multiple files (util, sync, core)

import os
import re
import requests

from requests.auth import HTTPBasicAuth

from guru.sync import Sync
from guru.data_objects import Board, Card, Collection, Group, HomeBoard, Tag, User

# collection colors
# many of the names come from http://chir.ag/projects/name-that-color/
MAROON = "#C2185B"
RED = "#F44336"
ORANGE = "#FF9800"
AMBER = "#FFC107"
SAPPHIRE = "#303F9F"
CORNFLOWER = "#2196F3"
TEAL = "#00BCD4"
GREEN = "#009688"
MAGENTA = "#E040FB"
DODGER_BLUE = "#2962FF"
SALMON = "#FF8A65"
GREEN_APPLE = "#689F38"

MEMBER = "MEMBER"
AUTHOR = "AUTHOR"
COLLECTION_OWNER = "COLL_ADMIN"

def make_blue(*args):
  return " ".join(["\033[94m%s\033[0m" % text for text in args])

def make_red(*args):
  return " ".join(["\033[91m%s\033[0m" % text for text in args])

def make_gray(*args):
  return " ".join(["\033[90m%s\033[0m" % text for text in args])

def make_green(*args):
  return " ".join(["\033[92m%s\033[0m" % text for text in args])

def make_bold(*args):
  return " ".join(["\033[1m%s\033[0m" % text for text in args])

def get_link_header(response):
  link_header = response.headers.get("Link", "")
  return link_header[1:link_header.find(">")]

def status_to_bool(status_code):
  band = int(status_code / 100)
  return (band == 2 or band == 3)

class DummyResponse:
  def __init__(self, status_code=200):
    self.headers = {}
    self.status_code = status_code
  
  def json(self):
    return []

class Guru:
  def __init__(self, username="", api_token="", silent=False, dry_run=False):
    self.username = username or os.environ.get("PYGURU_USER", "")
    self.api_token = api_token or os.environ.get("PYGURU_TOKEN", "")
    self.base_url = "https://api.getguru.com/api/v1"
    self.dry_run = dry_run
    self.__cache = {}

    if self.dry_run:
      self.debug = True
    elif silent:
      self.debug = False
    else:
      self.debug = True
  
  def __is_id(self, value):
    if re.match("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", str(value)):
      return True
    else:
      return False

  def __print(self, *args):
    print(" ".join([str(a) for a in args]))

  def sync(self, id="", clear=True, folder="/tmp/", verbose=False):
    return Sync(guru=self, id=id, clear=clear, folder=folder, verbose=verbose)
  
  def bundle(self, id="", clear=True, folder="/tmp/", verbose=False):
    return Sync(guru=self, id=id, clear=clear, folder=folder, verbose=verbose)
  
  def get_auth(self):
    return HTTPBasicAuth(self.username, self.api_token)

  def log(self, *args):
    if self.debug:
      if self.dry_run:
        self.__print(make_bold("[Dry Run]"), *args)
      else:
        self.__print(make_bold(make_green("[Live]")), *args)

  def log_response(self, response):
    if status_to_bool(response.status_code):
      self.log(make_gray("  response status:", response.status_code))
    else:
      self.log(make_gray("  response status:", response.status_code, "body:", response.content))

  def get(self, url, cache=False):
    if cache:
      # if we don't have a response for this call in our cache,
      # make the call and store the response.
      if not self.__cache.get(url):
        self.log(make_gray("  making a get call:", url))
        self.__cache[url] = requests.get(url, auth=self.get_auth())
      else:
        self.log(make_gray("  using cached get call:", url))
      return self.__cache[url]
    else:
      self.log(make_gray("  making a get call:", url))
      response = requests.get(url, auth=self.get_auth())
      self.__cache[url] = response
      self.log_response(response)
      return response
  
  def put(self, url, data):
    if self.dry_run:
      self.log(make_gray("  would make a put call:", url, data))
      return DummyResponse()

    self.log(make_gray("  making a put call:", url, data))
    response = requests.put(url, json=data, auth=self.get_auth())
    self.log_response(response)
    return response
    
  def post(self, url, data=None, files=None):
    if self.dry_run:
      self.log(make_gray("  would make a post call:", url, data))
      return DummyResponse()
      
    self.log(make_gray("  making a post call:", url, data))
    if files:
      response = requests.post(url, files=files, auth=self.get_auth())
      self.log_response(response)
      return response
    else:
      response = requests.post(url, json=data, auth=self.get_auth())
      self.log_response(response)
      return response
  
  def get_and_get_all(self, url):
    results = []
    auth = self.get_auth()
    page = 0

    while url:
      page += 1
      self.log("loading page:", page)
      response = self.get(url)
      results += response.json()
      url = get_link_header(response)
    
    return results

  def post_and_get_all(self, url, data):
    results = []
    auth = self.get_auth()
    page = 0

    while url:
      page += 1
      self.log("loading page:", page)
      response = self.post(url, data)
      results += response.json()
      url = get_link_header(response)
    
    return results

  def delete(self, url, data=None):
    if self.dry_run:
      self.log(make_gray("  would make a delete call:", url, data))
      return DummyResponse(204)

    self.log(make_gray("  making a delete call:", url, data))
    response = requests.delete(url, json=data, auth=self.get_auth())
    self.log_response(response)
    return response

  def get_members(self, search=""):
    members = []
    url = "%s/members?search=%s" % (self.base_url, search)
    users = self.get_and_get_all(url)
    users = [User(u) for u in users]
    return users

  def get_collection(self, collection, cache=False):
    """
    `collection` can either be its ID or its name.
    """
    if isinstance(collection, Collection):
      return collection
    elif self.__is_id(collection):
      url = "%s/collections/%s" % (self.base_url, collection)
      response = self.get(url, cache)
      return Collection(response.json())
    else:
      for c in self.get_collections(cache):
        # todo: handle the case where the name isn't unique.
        if c.name.lower() == collection.lower():
          return c

  def get_collections(self, cache=False):
    url = "%s/collections" % self.base_url
    response = self.get(url, cache)
    return [Collection(c) for c in response.json()]

  def get_group(self, group, cache=False):
    if isinstance(group, Group):
      return group

    groups = self.get_groups(cache)
    for g in groups:
      # todo: handle the case where the name isn't unique.
      if g.name.lower() == group.lower():
        return g

  def get_groups(self, cache=False):
    url = "%s/groups" % self.base_url
    response = self.get(url, cache)
    return [Group(g) for g in response.json()]
  
  def make_group(self, name):
    url = "%s/groups" % self.base_url
    data = {
      "id": "new-group",
      "name": name
    }
    response = self.post(url, data)
    return Group(response.json())

  def invite_user(self, email, *groups):
    groups = list(groups)
    
    if groups:
      self.log("invite user", make_blue(email), "and then add them to:", make_blue(groups))
    else:
      self.log("invite user", make_blue(email))
    
    data = { "emails": email }
    url = "%s/members/invite" % self.base_url
    response = self.post(url, data)

    # if there are remaining groups, call add_user_to_groups() for that.
    if groups:
      self.add_user_to_groups(email, *groups)
    
    return response.json(), response.status_code
  
  def add_user_to_groups(self, email, *groups):
    groups = list(groups)
    self.log("add user", make_blue(email), "to groups", make_blue(groups))

    # for each group, track whether the addition was successful or not.
    result = {}
    for group in groups:
      # we have the group name but we need its ID.
      group_obj = self.get_group(group, cache=True)
      if not group_obj:
        self.log(make_red("could not find group:", group))
        result[group] = False
        continue
      
      url = "%s/groups/%s/members" % (self.base_url, group_obj.id)
      response = self.post(url, [email])
      result[group] = status_to_bool(response.status_code)
    
    return result
  
  def add_user_to_group(self, email, group):
    return self.add_user_to_groups(email, group)
  
  def remove_user_from_groups(self, email, *groups):
    groups = list(groups)
    self.log("remove user", make_blue(email), "from groups", make_blue(groups))

    # for each group, track whether the addition was successful or not.
    result = {}
    for group in groups:
      group_obj = self.get_group(group, cache=True)
      if not group_obj:
        self.log(make_red("could not find group:", group))
        result[group] = False
        continue

      url = "%s/groups/%s/members/%s" % (self.base_url, group_obj.id, email)
      response = self.delete(url)
      result[group] = status_to_bool(response.status_code)
    
    return result
  
  def remove_user_from_group(self, email, group):
    return self.remove_user_from_groups(email, group)

  def remove_user_from_team(self, email):
    self.log("remove", make_blue(email), "from the team")
    data = {
      "collectionVerifiers": {}
    }
    url = "%s/members/%s/replaceverifier" % (self.base_url, email)
    response = self.delete(url, data)
    return response.status_code

  def get_card(self, id):
    url = "%s/cards/%s" % (self.base_url, id)
    response = self.get(url)
    return Card(response.json(), guru=self)

  def make_card(self, title, content, collection):
    # todo: add parameters for verifier, verification interval, share status, etc.
    card = Card({}, guru=self)
    card.title = title
    card.content = content
    if collection:
      card.collection = self.get_collection(collection, cache=True)
      if not card.collection:
        self.log(make_red("could not find collection:", collection))
        return
    return card.save()

  def get_tag(self, tag):
    if not tag:
      return

    tags = self.get_tags()
    for t in tags:
      if t.value.lower() == tag.lower():
        return t

  def get_tags(self):
    # todo: update this api so it doesn't just get tags that are being used
    #       but it gets the full list of all tags.
    url = "%s/search/inuse?boardId=&tagIds=&categoryIds=" % self.base_url

    # this returns a list of objects where each object represents a tag category
    # and looks like this:
    #   {
    #     "tags": [ tags... ],
    #     "id": "abcd1234",
    #     "name": "category"
    #   }
    response = self.get(url)

    tags = []
    for tag_category in response.json():
      tags += [Tag(t) for t in tag_category.get("tags", [])]
    return tags

  def find_card(self, **kwargs):
    cards = self.find_cards(**kwargs)
    if self.dry_run:
      return Card({}, guru=self)
    if cards:
      print("cards", cards)
      return cards[0]

  def find_cards(self, text="", title="", tag="", collection=""):
    # todo: look up the tag and get its id.
    url = "%s/search/cardmgr" % self.base_url
    # look up the tag and include its id here.

    data = {
      "queryType": None,
      "sorts": [
        {
          "type": "verificationState",
          "dir": "ASC"
        }
      ],
      "query": None,
      "collectionIds": []
    }

    # if a collection name was provided, look it up.
    if collection:
      c = self.get_collection(collection, cache=True)
      if not c:
        raise BaseException("collection '%s' not found" % collection)

      data["collectionIds"] = [c.id]

    # if no tag value was passed in, get_tag() will return nothing.
    if tag:
      tag_object = self.get_tag(tag)
      if not tag_object:
        self.log(make_red("could not find tag:", tag))
        return []
      
      data["query"] = {
        "nestedExpressions": [
          {
            "type": "tag",
            "ids": [
              tag_object.id
            ],
            "op": "EXISTS"
          }
        ],
        "op": "AND",
        "type": "grouping"
      }

    cards = self.post_and_get_all(url, data)
    cards = [Card(c, guru=self) for c in cards]
    if title:
      filtered_cards = []
      for c in cards:
        if c.title.lower() == title.lower():
          filtered_cards.append(c)
      cards = filtered_cards
    return cards

  def save_card(self, card, verify=False):
    if card.id:
      url = "%s/cards/%s" % (self.base_url, card.id)
      response = self.put(url, card.json(verify))
    else:
      url = "%s/cards" % self.base_url
      response = self.post(url, card.json(verify))
    if self.dry_run:
      return Card({}, guru=self), True
    else:
      return Card(response.json(), guru=self), status_to_bool(response.status_code)

  def archive_card(self, card):
    if card.id:
      url = "%s/cards/%s" % (self.base_url, card.id)
      response = self.delete(url)
      return status_to_bool(response.status_code)

  # def find_board(self, )
  def get_board(self, id="", slug=""):
    url = "%s/boards/%s" % (self.base_url, id or slug)
    response = self.get(url)
    return Board(response.json())
  
  def get_home_board(self, collection):
    collection_obj = self.get_collection(collection)
    if not collection_obj:
      self.log(make_red("could not find collection:", collection))
      return

    url = "%s/boards/home?collection=%s" % (self.base_url, collection_obj.id)
    response = self.get(url)
    return HomeBoard(response.json())

  def make_collection(self, name, desc="", color=GREEN, is_sync=False, group="All Members", public_cards=True):
    # if it's not a synced collection we need a group id for who'll be the author.
    data = {
      "name": name,
      "color": color,
      "description": desc,
      "collectionType": "EXTERNAL" if is_sync else "INTERNAL",
      "publicCardsEnabled": public_cards,
      "syncVerificationEnabled": False
    }

    group_obj = self.get_group(group, cache=True)
    if not group_obj:
      self.log(make_red("could not find group:", group))
      return
    data["initialAdminGroupId"] = group_obj.id

    url = "%s/collections" % self.base_url
    response = self.post(url, data)
    return Collection(response.json())

  def add_group_to_collection(self, group, collection, role):
    self.log("add group", make_blue(group), "to collection", make_blue(collection), "as", make_blue(role))
    group_obj = self.get_group(group, cache=True)
    collection_obj = self.get_collection(collection, cache=True)

    if not group_obj or not collection_obj:
      if not group_obj:
        self.log(make_red("could not find group:", group))
      if not collection_obj:
        self.log(make_red("could not find collection:", collection))
      return False

    data = {
      "groupId": group_obj.id,
      "role": role
    }
    url = "%s/collections/%s/groups" % (self.base_url, collection_obj.id)
    response = self.post(url, data)

    # a 400 response might mean the group is already assigned to the collection
    # and we need to do this as a put call instead of a post.
    if response.status_code == 400:
      url = "%s/collections/%s/groups/%s" % (self.base_url, collection_obj.id, group_obj.id)
      response = self.put(url, data)

    return status_to_bool(response.status_code)

  def remove_group_from_collection(self, group, collection):
    self.log("remove group", make_blue(group), "from collection", make_blue(collection))
    group_obj = self.get_group(group, cache=True)
    collection_obj = self.get_collection(collection, cache=True)

    if not group_obj or not collection_obj:
      if not group_obj:
        self.log(make_red("could not find group:", group))
      if not collection_obj:
        self.log(make_red("could not find collection:", collection))
      return False

    url = "%s/collections/%s/groups/%s" % (self.base_url, collection_obj.id, group_obj.id)
    response = self.delete(url)
    return status_to_bool(response.status_code)

  def delete_collection(self, collection):
    collection_obj = self.get_collection(collection, cache=True)
    if not collection_obj:
      self.log(make_red("could not find collection:", collection))
      return False
    
    url = "%s/collections/%s" % (self.base_url, collection_obj.id)
    response = self.delete(url)
    return status_to_bool(response.status_code)

  def upload_content(self, collection, filename, zip_path, is_sync=False):
    collection_obj = self.get_collection(collection)
    if not collection_obj:
      self.log(make_red("could not find collection:", collection))
      return

    with open(zip_path, "rb") as file_in:
      file_key = "file" if is_sync else "contentFile"
      files = {
        file_key: (filename, file_in, "application/zip")
      }

      # there's a slightly different url for syncs vs. imports.
      route = "contentsyncupload" if is_sync else "contentupload"
      url = "https://api.getguru.com/app/%s?collectionId=%s" % (route, collection_obj.id)
      response = self.post(url, files=files)

      if not status_to_bool(response.status_code):
        raise BaseException("%s returned a %s response: %s" % (
          route, response.status_code, response.text
        ))
      else:
        return response.json()
