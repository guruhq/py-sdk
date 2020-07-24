
import os
import re
import requests

from requests.auth import HTTPBasicAuth

from guru.sync import Sync
from guru.data_objects import Board, Card, CardComment, Collection, Group, HomeBoard, Tag, User

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

READ_ONLY = "MEMBER"
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
    """
    Creates a Sync object that can be used to bulk import content.
    """
    return Sync(guru=self, id=id, clear=clear, folder=folder, verbose=verbose)
  
  def bundle(self, id="", clear=True, folder="/tmp/", verbose=False):
    """
    bundle() is an alias for sync().
    """
    return Sync(guru=self, id=id, clear=clear, folder=folder, verbose=verbose)
  
  def __get_auth(self):
    return HTTPBasicAuth(self.username, self.api_token)

  def __log(self, *args):
    if self.debug:
      if self.dry_run:
        self.__print(make_bold("[Dry Run]"), *args)
      else:
        self.__print(make_bold(make_green("[Live]")), *args)

  def __log_response(self, response):
    if status_to_bool(response.status_code):
      self.__log(make_gray("  response status:", response.status_code))
    else:
      self.__log(make_gray("  response status:", response.status_code, "body:", response.content))

  def __get(self, url, cache=False):
    if cache:
      # if we don't have a response for this call in our cache,
      # make the call and store the response.
      if not self.__cache.get(url):
        self.__log(make_gray("  making a get call:", url))
        self.__cache[url] = requests.get(url, auth=self.__get_auth())
      else:
        self.__log(make_gray("  using cached get call:", url))
      return self.__cache[url]
    else:
      self.__log(make_gray("  making a get call:", url))
      response = requests.get(url, auth=self.__get_auth())
      self.__cache[url] = response
      self.__log_response(response)
      return response
  
  def __put(self, url, data):
    if self.dry_run:
      self.__log(make_gray("  would make a put call:", url, data))
      return DummyResponse()

    self.__log(make_gray("  making a put call:", url, data))
    response = requests.put(url, json=data, auth=self.__get_auth())
    self.__log_response(response)
    return response
    
  def __post(self, url, data=None, files=None):
    if self.dry_run:
      self.__log(make_gray("  would make a post call:", url, data))
      return DummyResponse()
      
    self.__log(make_gray("  making a post call:", url, data))
    if files:
      response = requests.post(url, files=files, auth=self.__get_auth())
      self.__log_response(response)
      return response
    else:
      response = requests.post(url, json=data, auth=self.__get_auth())
      self.__log_response(response)
      return response
  
  def __get_and_get_all(self, url):
    results = []
    auth = self.__get_auth()
    page = 0

    while url:
      page += 1
      self.__log("loading page:", page)
      response = self.__get(url)
      results += response.json()
      url = get_link_header(response)
    
    return results

  def __post_and_get_all(self, url, data):
    results = []
    auth = self.__get_auth()
    page = 0

    while url:
      page += 1
      self.__log("loading page:", page)
      response = self.__post(url, data)
      results += response.json()
      url = get_link_header(response)
    
    return results

  def __delete(self, url, data=None):
    if self.dry_run:
      self.__log(make_gray("  would make a delete call:", url, data))
      return DummyResponse(204)

    self.__log(make_gray("  making a delete call:", url, data))
    response = requests.delete(url, json=data, auth=self.__get_auth())
    self.__log_response(response)
    return response

  def get_members(self, search=""):
    """
    Gets a list of users on the team.

    Args:
      search (str, optional): A text string to search for. This will be
        matched against each user's first name, last name, or email address.
        By default there's no filter and it'll return all users.
    
    Returns:
      list of User: a list of users on the team.
    """

    members = []
    url = "%s/members?search=%s" % (self.base_url, search)
    users = self.__get_and_get_all(url)
    users = [User(u) for u in users]
    return users

  def get_collection(self, collection, cache=False):
    """
    Loads a collection.

    Args:
      collection (str): Either a collection name or ID. If it's a name, it'll
        return the first matching collection and the comparison is not case
        sensitive.
      cache (bool, optional): If we're looking up a collection by name we'll
        fetch all collections and then look for a match in the results and this
        flag tells us whether we should use the results from the previous
        /collections API call or make a new call. Defaults to False.
    
    Returns:
      Collection: An object representing the collection.
    """
    if isinstance(collection, Collection):
      return collection
    elif self.__is_id(collection):
      url = "%s/collections/%s" % (self.base_url, collection)
      response = self.__get(url, cache)
      return Collection(response.json())
    else:
      for c in self.get_collections(cache):
        # todo: handle the case where the name isn't unique.
        if c.name.lower() == collection.lower():
          return c

  def get_collections(self, cache=False):
    """
    Loads a list of all collections you have access to.

    Args:
      cache (bool, optional): Tells us whether we should reuse the results
        from the previous call or not. Defaults to False. Set this to True
        if it's not likely the set of collections has changed since the
        previous call.
    
    Returns:
      list of Collection: All of the collections you have access to.
    """
    url = "%s/collections" % self.base_url
    response = self.__get(url, cache)
    return [Collection(c) for c in response.json()]

  def get_group(self, group, cache=False):
    """
    Loads a group.

    Args:
      group (str): Either a group name or ID. If it's a name, it'll return
        the first matching collection and the comparison is not case sensitive.
      cache (bool, optional): If we're looking up a group by name we'll fetch
        all groups and then look for a match in the results and this flag tells
        us whether we should use the results from the previous /groups API call
        or make a new call. Defaults to False.
    
    Returns:
      Group: An object representing the group.
    """
    if isinstance(group, Group):
      return group

    groups = self.get_groups(cache)
    for g in groups:
      # todo: handle the case where the name isn't unique.
      if g.name.lower() == group.lower():
        return g

  def get_groups(self, cache=False):
    """
    Loads a list of all groups.

    Args:
      cache (bool, optional): Tells us whether we should reuse the results
        from the previous call or not. Defaults to False. Set this to True
        if it's not likely the set of groups has changed since the previous
        call.
    
    Returns:
      list of Group: All of the groups.
    """
    url = "%s/groups" % self.base_url
    response = self.__get(url, cache)
    return [Group(g) for g in response.json()]
  
  def make_group(self, name):
    """
    Creates a new group.

    Args:
      name (str): The group's name.

    Returns:
      Group: An object representing the new group.
    """
    url = "%s/groups" % self.base_url
    data = {
      "id": "new-group",
      "name": name
    }
    response = self.__post(url, data)
    return Group(response.json())

  def delete_group(self, group):
    """
    Deletes a group. You can't undo this using the API or SDK
    so be sure you want to delete it.

    Args:
      group (str): The name or ID of the group to delete.
    
    Returns:
      bool: True if it was successful and False otherwise.
    """
    group_obj = self.get_group(group)
    if not group_obj:
      self.__log(make_red("could not find group:", group))
      return False
    
    url = "%s/groups/%s" % (self.base_url, group_obj.id)
    response = self.__delete(url)
    return status_to_bool(response.status_code)

  def invite_user(self, email, *groups):
    """
    Adds a user to the team and adds them to the groups provided.
    The user may receive an email because of this -- this is configured
    in the webapp's Team Settings section.

    If the user is already on the team this still adds them to the
    groups.

    Args:
      email (str): The email address of the user to add to the team.
      *groups (str): Any number of groups to add the user to.
    
    Returns:
      todo: fill this out.
    """
    groups = list(groups)
    
    if groups:
      self.__log("invite user", make_blue(email), "and then add them to:", make_blue(groups))
    else:
      self.__log("invite user", make_blue(email))
    
    data = { "emails": email }
    url = "%s/members/invite" % self.base_url
    response = self.__post(url, data)

    # if there are remaining groups, call add_user_to_groups() for that.
    if groups:
      self.add_user_to_groups(email, *groups)
    
    return response.json(), response.status_code
  
  def add_users_to_group(self, emails, group):
    """
    Adds a list of users to a single group. If you're adding many users
    to the same group, this call is more efficient than calling
    ass_user_to_group once for each individual user-to-group assignment.

    Args:
      emails (list of str): The list of email address of the users to add to the group.
      group (str): The name or ID of the group.
    
    Returns:
      dict of str: bool: The keys are email addresses and the value is
        True if the user was added to the group and False otherwise.
    """
    group_obj = self.get_group(group)
    if not group_obj:
      self.__log(make_red("could not find group:", group))
      return
    
    results = {}

    # do it in batches of 100 users per call.
    for index in range(0, len(emails), 100):
      batch = emails[index:index + 100]
      
      url = "%s/groups/%s/members" % (self.base_url, group_obj.id)
      response = self.__post(url, batch)

      if status_to_bool(response.status_code):
        for obj in response.json():
          email = obj.get("id")
          if email:
            results[email] = True
      else:
        for email in batch:
          results[email] = False
    
    # todo: do the ones who failed one at a time.
    return results


  def add_user_to_groups(self, email, *groups):
    """
    Adds a user to one or more groups. If the user is already in some
    of the groups provided, that's ok.

    Args:
      email (str): The user being added to groups.
      *groups (str): Any number of groups to add the user to. Can be
        group names, IDs, or group objects (like what you'd get from
        calling get_group()).

    Returns:
      dict of str: bool: The keys are the group names and the values
        indicate whether the addition was successful (True) or not (False).
    """
    groups = list(groups)
    self.__log("add user", make_blue(email), "to groups", make_blue(groups))

    # for each group, track whether the addition was successful or not.
    result = {}
    for group in groups:
      # we have the group name but we need its ID.
      group_obj = self.get_group(group, cache=True)
      if not group_obj:
        self.__log(make_red("could not find group:", group))
        result[group] = False
        continue
      
      url = "%s/groups/%s/members" % (self.base_url, group_obj.id)
      response = self.__post(url, [email])
      result[group_obj.name] = status_to_bool(response.status_code)
    
    return result
  
  def add_user_to_group(self, email, group):
    """
    Adds a user to a single group.

    Args:
      email (str): The user being added to the group.
      group (str): The name or ID of the group to add the user to.

    Returns:
      dict of str: bool: The key is the group name and the value
        indicates whether the addition was successful (True) or not (False).
    """
    return self.add_user_to_groups(email, group)
  
  def remove_user_from_groups(self, email, *groups):
    """
    Removes a single user from one or more groups.

    Args:
      email (str): The user being removed from groups.
      *groups (str): Any number of group to remove the user from. Can
        be group names, IDs, or group objects (like what you'd get
        from calling get_group()).

    Returns:
      dict of str: bool: The keys are the group names and the values
        indicate whether the removal was successful (True) or not (False).
    """
    groups = list(groups)
    self.__log("remove user", make_blue(email), "from groups", make_blue(groups))

    # for each group, track whether the addition was successful or not.
    result = {}
    for group in groups:
      group_obj = self.get_group(group, cache=True)
      if not group_obj:
        self.__log(make_red("could not find group:", group))
        result[group] = False
        continue

      url = "%s/groups/%s/members/%s" % (self.base_url, group_obj.id, email)
      response = self.__delete(url)
      result[group_obj.name] = status_to_bool(response.status_code)
    
    return result
  
  def remove_user_from_group(self, email, group):
    """
    Removes a single user from a single group

    Args:
      email (str): The user being removed from the group.
      group (str): The name or ID of the group to remove the user from.

    Returns:
      dict of str: bool: The key is the group name and the value
        indicates whether the removal was successful (True) or not (False).
    """
    return self.remove_user_from_groups(email, group)

  def remove_user_from_team(self, email):
    """
    Removes a user from the whole team.

    Args:
      email (str): The email address of the user to remove.
    
    Returns:
      bool: True if it was successful and False otherwise.
    """
    self.__log("remove", make_blue(email), "from the team")
    data = {
      "collectionVerifiers": {}
    }
    url = "%s/members/%s/replaceverifier" % (self.base_url, email)
    response = self.__delete(url, data)
    return status_to_bool(response.status_code)

  def get_card(self, card):
    """
    Loads a single card by its ID.

    Args:
      card (str): The card's ID or slug.
    
    Returns:
      Card: An object representing the card.
    """
    if isinstance(card, Card):
      return card

    url = "%s/cards/%s" % (self.base_url, card)
    response = self.__get(url)
    if status_to_bool(response.status_code):
      try:
        return Card(response.json(), guru=self)
      except:
        return None

  def make_card(self, title, content, collection):
    """
    Makes a new card and saves it.

    Args:
      title (str): The title of the new card.
      content (str): The HTML content of the new card.
      collection (str): The name or ID of the collection this card
        will be added to.
    
    Returns:
      Card: An object representing the new card.
    """
    # todo: add parameters for verifier, verification interval, share status, etc.
    card = Card({}, guru=self)
    card.title = title
    card.content = content
    if collection:
      card.collection = self.get_collection(collection, cache=True)
      if not card.collection:
        self.__log(make_red("could not find collection:", collection))
        return
    return card.save()

  def get_tag(self, tag):
    # todo: update this to work by ID or value.
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
    response = self.__get(url)

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

  def find_cards(self, title="", tag="", collection=""):
    """
    Gets a list of cards that match the criteria defined by the parameters.
    You can include any combination of title, tag, and collection to
    filter by a single value or multiple.

    Args:
      title (str, optional): A title to match against cards. The matching
        is not case sensitive.
      tag (str, optional): The name or ID of a tag.
      collection (str, optional): The name or ID of a collection.
    
    Returns:
      list of Card: The cards that matched the parameters you provided.
    """
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
        self.__log(make_red("could not find tag:", tag))
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

    cards = self.__post_and_get_all(url, data)
    cards = [Card(c, guru=self) for c in cards]
    if title:
      filtered_cards = []
      for c in cards:
        if c.title.lower() == title.lower():
          filtered_cards.append(c)
      cards = filtered_cards
    return cards

  def save_card(self, card, verify=False):
    """
    Saves changes to a card.

    Args:
      card (Card): The Card object for the card you're saving.
      verify (bool, optional): True if saving the card should make it become
        verified and False if an untrusted card should remain untrusted.
        Defaults to False.
    
    Returns:
      Card: An updated card object.
    """
    if card.id:
      url = "%s/cards/%s" % (self.base_url, card.id)
      response = self.__put(url, card.json(verify))
    else:
      url = "%s/cards" % self.base_url
      response = self.__post(url, card.json(verify))
    if self.dry_run:
      return Card({}, guru=self), True
    else:
      return Card(response.json(), guru=self), status_to_bool(response.status_code)

  def archive_card(self, card):
    """
    Archives a card. Archived cards can still be restored.

    Args:
      card (str or Card): The card's ID or slug, or a Card object.
    
    Returns:
      bool: True if it was successful and False otherwise.
    """
    card_obj = self.get_card(card)
    if not card_obj:
      self.__log(make_red("could not find card:", card))
      return False

    url = "%s/cards/%s" % (self.base_url, card_obj.id)
    response = self.__delete(url)
    return status_to_bool(response.status_code)

  def add_comment_to_card(self, card, comment):
    """
    Adds a comment to a card.

    Args:
      card (str): The name or ID of the card to add a comment to.
      comment (str): The text content of the comment.
    
    Returns:
      CardComment: An object representing the card comment.
    """
    card_obj = self.get_card(card)
    if not card_obj:
      self.__log(make_red("could not find card:", card))
      return
    
    if not comment:
      return

    data = {"content": comment}
    url = "%s/cards/%s/comments" % (self.base_url, card_obj.id)
    response = self.__post(url, data)
    return CardComment(response.json(), card=card_obj, guru=self)

  def get_card_comments(self, card):
    """
    Gets all comments on a card.

    Args:
      card (str): The name or ID of the card.
    
    Returns:
      list of CardComment: The card's comments.
    """
    card_obj = self.get_card(card)
    if not card_obj:
      self.__log(make_red("could not find card:", card))
      return
    
    url = "%s/cards/%s/comments" % (self.base_url, card_obj.id)
    comments = self.__get_and_get_all(url)
    comments = [CardComment(c, card=card_obj, guru=self) for c in comments]
    return comments

  def update_card_comment(self, comment_obj):
    """
    Updates a card comment.

    Args:
      comment_obj (CardComment): The CardComment object that has changes to save.
    
    Returns:
      CardComment: An updated CardComment object.
    """
    # https://api.getguru.com/api/v1/cards/a0201644-5dcf-4a90-868c-fb5e4981aa17/comments/2ecb2e09-e78a-4de8-90ac-f075e1cf6447
    url = "%s/cards/%s/comments/%s" % (self.base_url, comment_obj.card.id, comment_obj.id)
    response = self.__put(url, comment_obj.json())
    if status_to_bool(response.status_code):
      return CardComment(response.json(), card=comment_obj.card, guru=self)

  def delete_card_comment(self, card, comment_id):
    """
    Deletes a comment from a card. You need the exact comment ID
    to do this. The other way to do this is by getting the list of
    comments on a card and then those objects will have a delete()
    method:

      ```
      g = guru.Guru()
      comments = g.get_card_comments("card-id...")
      comments[0].delete()
      ```
    
    Args:
      card (str): The ID of the card that contains the comment.
      comment_id (str): The ID of the comment to delete.
    
    Returns:
      bool: True if it was successful and False otherwise.
    """
    card_obj = self.get_card(card)
    if not card_obj:
      self.__log(make_red("could not find card:", card))
      return False

    url = "%s/cards/%s/comments/%s" % (self.base_url, card_obj.id, comment_id)
    response = self.__delete(url)
    return status_to_bool(response.status_code)

  def get_board(self, id):
    """
    Loads a board.

    Args:
      id (str): The board's full ID or slug.
    
    Returns:
      Board: An object representing the board.
    """
    url = "%s/boards/%s" % (self.base_url, id)
    response = self.__get(url)
    return Board(response.json())
  
  def get_home_board(self, collection):
    """
    Loads a collection's "home board". The home board is the object
    that lists all of the boards and board groups in the collection
    and shows you the order they're in.

    Args:
      collection (str): The name or ID of the collection whose home
        board you're loading.
    
    Returns:
      HomeBoard: An object representing the home board.
    """
    collection_obj = self.get_collection(collection)
    if not collection_obj:
      self.__log(make_red("could not find collection:", collection))
      return

    url = "%s/boards/home?collection=%s" % (self.base_url, collection_obj.id)
    response = self.__get(url)
    return HomeBoard(response.json())

  def make_collection(self, name, desc="", color=GREEN, is_sync=False, group="All Members", public_cards=True):
    """
    Creates a new collection.

    Args:
      name (str): The name of the new collection.
      desc (str, optional): The description of the new collection.
      color (str, optional): The color of the new collection. The guru module has
        constants for all of the different colors:  MAROON, RED, ORANGE, AMBER,
        SAPPHIRE, CORNFLOWER, TEAL, GREEN, MAGENTA, DODGER_BLUE, SALMON, GREEN_APPLE.
        Defaults to GREEN. We like green.
      is_sync (str, optional): True if you want this collection behave as a synced
        collection and False otherwise. Defaults to False. For more information on
        synced collection, go here: https://developer.getguru.com/docs/guru-sync-manual-api
      group (str, optional): The name or ID of the group to have collection owner
        access to this collection. Defaults to All Members.
      public_cards (bool, optional): True if you want to allow cards in this collection
        to be made public and False if you don't. Defaults to True.
    
    Returns:
      Collection: an object representing the new collection.
    """
    self.__log("make collection", make_blue(name), "with ", make_blue(group), "as Collection Owner")

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
      self.__log(make_red("could not find group:", group))
      return
    data["initialAdminGroupId"] = group_obj.id

    url = "%s/collections" % self.base_url
    response = self.__post(url, data)
    return Collection(response.json())

  def add_group_to_collection(self, group, collection, role):
    """
    Adds a group to a collection and gives it the specified role.
    If the group is already on the collection it'll update its role
    to be what you specify here.

    Args:
      group (str): A group name or ID.
      collection (str): A collection name or ID.
      role (str): Either guru.READ_ONLY, guru.AUTHOR, or guru.COLLECTION_OWNER.
    
    Returns:
      bool: True if it was successful and False otherwise.
    """
    self.__log("add group", make_blue(group), "to collection", make_blue(collection), "as", make_blue(role))
    group_obj = self.get_group(group, cache=True)
    collection_obj = self.get_collection(collection, cache=True)

    if not group_obj or not collection_obj:
      if not group_obj:
        self.__log(make_red("could not find group:", group))
      if not collection_obj:
        self.__log(make_red("could not find collection:", collection))
      return False

    data = {
      "groupId": group_obj.id,
      "role": role
    }
    url = "%s/collections/%s/groups" % (self.base_url, collection_obj.id)
    response = self.__post(url, data)

    # a 400 response might mean the group is already assigned to the collection
    # and we need to do this as a put call instead of a post.
    if response.status_code == 400:
      url = "%s/collections/%s/groups/%s" % (self.base_url, collection_obj.id, group_obj.id)
      response = self.__put(url, data)

    return status_to_bool(response.status_code)

  def remove_group_from_collection(self, group, collection):
    """
    Removes a group's access to a collection.

    Args:
      group (str): The name or ID of the group to remove.
      collection (str): The name or ID of the collection.
    
    Returns:
      bool: True if it was successful and False otherwise.
    """
    self.__log("remove group", make_blue(group), "from collection", make_blue(collection))
    group_obj = self.get_group(group, cache=True)
    collection_obj = self.get_collection(collection, cache=True)

    if not group_obj or not collection_obj:
      if not group_obj:
        self.__log(make_red("could not find group:", group))
      if not collection_obj:
        self.__log(make_red("could not find collection:", collection))
      return False

    url = "%s/collections/%s/groups/%s" % (self.base_url, collection_obj.id, group_obj.id)
    response = self.__delete(url)
    return status_to_bool(response.status_code)

  def delete_collection(self, collection):
    """
    Deletes a collection. You can't undo this using the API or SDK
    so be sure you want to delete it.

    Args:
      collection (str): The name or ID of the collection to delete.
    
    Returns:
      bool: True if it was successful and False otherwise.
    """
    collection_obj = self.get_collection(collection, cache=True)
    if not collection_obj:
      self.__log(make_red("could not find collection:", collection))
      return False
    
    url = "%s/collections/%s" % (self.base_url, collection_obj.id)
    response = self.__delete(url)
    return status_to_bool(response.status_code)

  def upload_content(self, collection, filename, zip_path, is_sync=False):
    collection_obj = self.get_collection(collection)
    if not collection_obj:
      self.__log(make_red("could not find collection:", collection))
      return

    with open(zip_path, "rb") as file_in:
      file_key = "file" if is_sync else "contentFile"
      files = {
        file_key: (filename, file_in, "application/zip")
      }

      # there's a slightly different url for syncs vs. imports.
      route = "contentsyncupload" if is_sync else "contentupload"
      url = "https://api.getguru.com/app/%s?collectionId=%s" % (route, collection_obj.id)
      response = self.__post(url, files=files)

      if not status_to_bool(response.status_code):
        raise BaseException("%s returned a %s response: %s" % (
          route, response.status_code, response.text
        ))
      else:
        return response.json()
