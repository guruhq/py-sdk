
import os
import re
import sys
import time
import base64
import requests
import mimetypes

from requests.auth import HTTPBasicAuth

if sys.version_info.major >= 3:
  from urllib.parse import quote
else:
  from urlparse import quote

from guru.bundle import Bundle
from guru.data_objects import Board, BoardGroup, BoardPermission, Card, CardComment, Collection, CollectionAccess, Draft, Group, HomeBoard, Tag, User, Question
from guru.util import download_file, find_by_name_or_id, find_by_email, find_by_id, format_timestamp, TRACKING_HEADERS

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

def base64_encode(string):
  return base64.b64encode(
    string.encode("ascii")
  ).decode("ascii")

def is_board_slug(value):
  return re.match("^[a-zA-Z0-9]{5,8}$", value)

def is_uuid(value):
  return re.match("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", value, flags=re.IGNORECASE)

def is_color(color):
  if re.match("^#[0-9a-fA-F]{6}$", color):
    return True
  return False

def is_email(email):
  return "@" in email and len(email) > 3


class DummyResponse:
  def __init__(self, status_code=200):
    self.headers = {}
    self.status_code = status_code
  
  def json(self):
    return []


class Guru:
  """
  The Guru object is the main wrapper around all API functionality.
  You can create one like this, passing it your username and API token:

  ```
  import guru
  g = guru.Guru("user@example.com", "abcd1234-abcd-abcd-abcd-abcdabcdabcd")
  ```

  You can also store these values in the `GURU_USER` and `GURU_TOKEN` environment
  variables. If you're using environment variables you don't need to pass any parameters
  to the `Guru()` constructor.
  """

  def __init__(self, username="", api_token="", silent=False, dry_run=False, qa=False):
    self.username = username or os.environ.get("PYGURU_USER", "") or os.environ.get("GURU_USER", "")
    self.api_token = api_token or os.environ.get("PYGURU_TOKEN", "") or os.environ.get("GURU_TOKEN", "")
    self.base_url = "https://qaapi.getguru.com/api/v1" if qa else "https://api.getguru.com/api/v1"
    self.hostname = "qaapi.getguru.com" if qa else "api.getguru.com"
    self.dry_run = dry_run
    self.__cache = {}
    self.__upload_key = None

    if self.dry_run:
      self.debug = True
    elif silent:
      self.debug = False
    else:
      self.debug = True
  
  def __is_id(self, value):
    """internal"""
    if re.match("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", str(value)):
      return True
    else:
      return False

  def __print(self, *args):
    """internal"""
    print(" ".join([str(a) for a in args]))

  def __get_auth(self):
    """internal"""
    return HTTPBasicAuth(self.username, self.api_token)

  def __get_basic_auth_value(self):
    auth_string = "%s:%s" % (self.username, self.api_token)
    return "Basic %s" % base64_encode(auth_string)

  def __log(self, *args):
    """internal"""
    if self.debug:
      if self.dry_run:
        self.__print(make_bold("[Dry Run]"), *args)
      else:
        self.__print(make_bold(make_green("[Live]")), *args)

  def __log_response(self, response):
    """internal"""
    if status_to_bool(response.status_code):
      self.__log(make_gray("  response status:", response.status_code))
    else:
      self.__log(make_gray("  response status:", response.status_code, "body:", response.content))

  def __clear_cache(self, url):
    """internal"""
    if self.__cache.get(url):
      del self.__cache[url]

  def __get(self, url, cache=False):
    """internal"""
    if cache:
      # if we don't have a response for this call in our cache,
      # make the call and store the response.
      if not self.__cache.get(url):
        self.__log(make_gray("  making a get call:", url))
        self.__cache[url] = requests.get(url, auth=self.__get_auth(), headers=TRACKING_HEADERS)
      else:
        self.__log(make_gray("  using cached get call:", url))
      return self.__cache[url]
    else:
      self.__log(make_gray("  making a get call:", url))
      response = requests.get(url, auth=self.__get_auth(), headers=TRACKING_HEADERS)
      self.__cache[url] = response
      self.__log_response(response)
      return response
  
  def __put(self, url, data=None):
    """internal"""
    if self.dry_run:
      self.__log(make_gray("  would make a put call:", url, data))
      return DummyResponse()

    self.__log(make_gray("  making a put call:", url, data))
    response = requests.put(url, json=data, auth=self.__get_auth(), headers=TRACKING_HEADERS)
    self.__log_response(response)
    return response

  def __patch(self, url, data=None):
    """internal"""
    if self.dry_run:
      self.__log(make_gray("  would make a patch call:", url, data))
      return DummyResponse()

    self.__log(make_gray("  making a patch call:", url, data))
    response = requests.patch(url, json=data, auth=self.__get_auth(), headers=TRACKING_HEADERS)
    self.__log_response(response)
    return response

  def __post(self, url, data=None, files=None):
    """internal"""
    if self.dry_run:
      self.__log(make_gray("  would make a post call:", url, data))
      return DummyResponse()
      
    self.__log(make_gray("  making a post call:", url, data))
    if files:
      response = requests.post(url, files=files, auth=self.__get_auth(), headers=TRACKING_HEADERS)
      self.__log_response(response)
      return response
    else:
      response = requests.post(url, json=data, auth=self.__get_auth(), headers=TRACKING_HEADERS)
      self.__log_response(response)
      return response
  
  def __get_and_get_all(self, url, cache=False, max_pages=500):
    """internal"""
    if cache and self.__cache.get(url):
      self.__log(make_gray("  using cached get call:", url))
      return self.__cache[url]
    
    results = []
    auth = self.__get_auth()
    page = 0

    while url:
      page += 1
      self.__log("loading page:", page)
      response = self.__get(url)
      if status_to_bool(response.status_code):
        if response.status_code != 204:
          results += response.json()
      else:
        raise BaseException("error response", response)
      url = get_link_header(response)

      if page >= max_pages:
        break
    
    self.__cache[url] = results
    return results

  def __post_and_get_all(self, url, data):
    """internal"""
    results = []
    auth = self.__get_auth()
    page = 0

    while url:
      page += 1
      self.__log("loading page:", page)
      response = self.__post(url, data)
      if response.status_code != 204:
        results += response.json()
      url = get_link_header(response)
    
    return results

  def __delete(self, url, data=None):
    """internal"""
    if self.dry_run:
      self.__log(make_gray("  would make a delete call:", url, data))
      return DummyResponse(204)

    self.__log(make_gray("  making a delete call:", url, data))
    response = requests.delete(url, json=data, auth=self.__get_auth())
    self.__log_response(response)
    return response

  def get_collection(self, collection, cache=False):
    """
    Loads a collection.

    ```
    collection = g.get_collection("Engineering")
    print(collection.name)
    print(collection.description)
    ```

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
      return Collection(response.json(), guru=self)
    else:
      # we compare the name and ID because you can pass either.
      # and if the names aren't unique, you'll need to pass an ID.
      return find_by_name_or_id(self.get_collections(cache), collection)

  def get_collections(self, cache=False):
    """
    Loads a list of all collections you have access to.

    ```
    for collection in g.get_collections():
      print(collection.name)
    ```

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
    return [Collection(c, guru=self) for c in response.json()]

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

    if not color:
      color = GREEN
    if not is_color(color):
      raise ValueError("invalid color value '%s'" % color)
    color = color.strip()

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
    return Collection(response.json(), guru=self)

  def get_groups_on_collection(self, collection):
    collection_obj = self.get_collection(collection, cache=True)
    if not collection_obj:
      self.__log(make_red("could not find collection:", collection))
      return

    url = "%s/collections/%s/groups" % (self.base_url, collection_obj.id)
    response = self.__get(url)
    if response.status_code == 204:
      return []
    return [CollectionAccess(ca) for ca in response.json()]

  def add_group_to_collection(self, group, collection, role):
    """
    Adds a group to a collection and gives it the specified role.
    If the group is already on the collection it'll update its role
    to be what you specify here.

    You can also do this through the Collection object:

    ```
    collection = g.get_collection("Engineering")
    collection.add_group("Customer Support", guru.READ_ONLY)
    ```

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
    """internal: used by the bundle object"""
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
      url = "https://%s/app/%s?collectionId=%s" % (self.hostname, route, collection_obj.id)
      response = self.__post(url, files=files)

      if not status_to_bool(response.status_code):
        raise BaseException("%s returned a %s response: %s" % (
          route, response.status_code, response.text
        ))
      else:
        return response.json()

  def get_group(self, group, cache=False):
    """
    Loads a group.

    ```
    group = g.get_group("Experts")
    print(group.id)
    ```

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
    return find_by_name_or_id(groups, group)

  def get_groups(self, cache=False):
    """
    Loads a list of all groups.

    ```
    for group in g.get_groups():
      print(group.id, group.name)
    ```

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
    return [Group(g, guru=self) for g in response.json()]
  
  def make_group(self, name):
    """
    Creates a new group. This *does* check if a group by this name already
    exists, but you should still be careful not to create duplicate groups.
    For example, you can still create near-duplicates where one group's name
    is the misspelling of another, or one is singular and the other is plural.

    ```
    g.make_group("Experts")
    g.add_user_to_group("user@example.com", "Experts")
    ```

    Args:
      name (str): The group's name.

    Returns:
      Group: An object representing the new group.
    """
    # check first if a group with this name already exists.
    # our backend does not check for this so if we don't, it's easy
    # to create duplicate groups.
    group_obj = self.get_group(name)
    if group_obj:
      self.__log(make_red("A group with the name \"%s\" already exists." % name))
      return None

    url = "%s/groups" % self.base_url
    data = {
      "id": "new-group",
      "name": name
    }
    response = self.__post(url, data)
    self.__clear_cache("%s/groups" % self.base_url)
    return Group(response.json(), guru=self)

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

  def get_group_members(self, group):
    """
    Gets a list of users in the group.

    ```
    for user in g.get_group_members("Experts"):
      print(user.email)
    ```

    Args:
      group (str or Group): The name of the group, or its ID, or a Group object.

    Returns:
      list of User: a list of users in the group.
    """
    group_obj = self.get_group(group)
    if not group_obj:
      self.__log(make_red("could not find group:", group))
      return False

    url = "%s/groups/%s/members" % (self.base_url, group_obj.id)
    response = self.__get(url)
    if response.status_code == 204:
      return []
    return [User(u) for u in response.json() or []]

  def get_members(self, search="", cache=False):
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
    url = "%s/members?search=%s" % (self.base_url, quote(search))
    users = self.__get_and_get_all(url, cache)
    users = [User(u) for u in users]
    return users

  def __invite_user(self, email, *groups, is_light_user=False):
    """
    Internal

    Args:
      email (str): The email address of the user to add to the team.
      *groups (str): Any number of groups to add the user to.
    
    Returns:
      response (str): parsed JSON response.
      status (int): response status code
    """
    groups = list(groups)

    if not is_email(email):
      raise ValueError("invalid email '%s'" % email)
    
    if groups:
      self.__log("invite user", make_blue(email), "and then add them to:", make_blue(groups))
    else:
      self.__log("invite user", make_blue(email))
    
    if is_light_user:
      data = { "emails": email, "teamMemberType": "LIGHT" }
    else:
      data = { "emails": email, "teamMemberType": "CORE" }
    url = "%s/members/invite" % self.base_url
    response = self.__post(url, data)

    # if there are remaining groups, call add_user_to_groups() for that.
    if groups:
      # todo: when we call this, it'll make a GET call to load this user to see if they're
      #       already in any of the groups we're trying to add them to -- in this case, since
      #       we _just_ invited them, we know they won't be. it'd be great to be able to skip
      #       that GET call in this situation.
      self.add_user_to_groups(email, *groups)
    
    # todo: return a dict that maps email -> bool indicating if the user was invited successfully.
    return response.json(), response.status_code
  
  def invite_user(self, email, *groups):
    """
    Adds a user to the team and adds them to the groups provided.
    The user may receive an email because of this -- this is configured
    in the webapp's Team Settings section.

    If the user is already on the team this still adds them to the
    groups.

    ```
    g.invite_user("user1@example.com")

    # invite a user and add them to some groups.
    g.invite_user("user2@example.com", "Experts", "Engineering")
    ```

    Args:
      email (str): The email address of the user to add to the team.
      *groups (str): Any number of groups to add the user to.
    
    Returns:
      response (str): parsed JSON response.
      status (int): response status code
    """

    response, status = self.__invite_user(email, *groups)

    return response, status

  def invite_light_user(self, email):
    """
    Adds a user to the team as a light user.
    Light users can't belong to groups, so they automatically go into the All Members group.
    The user may receive an email because of this -- this is configured
    in the webapp's Team Settings section.

    ```
    g.invite_light_user("user1@example.com")

    ```

    Args:
      email (str): The email address of the user to add to the team.
    
    Returns:
      response (str): parsed JSON response.
      status (int): response status code
    """

    response, status = self.__invite_user(email, is_light_user=True)
    # todo: return a dict that maps email -> bool indicating if the user was invited successfully.
    return response, status
  
  def invite_core_user(self, email, *groups):
    """
    Adds a user to the team as a core user and adds them to the groups provided.
    The user may receive an email because of this -- this is configured
    in the webapp's Team Settings section.

    If the user is already on the team this still adds them to the
    groups.

    ```
    g.invite_core_user("user1@example.com")

    # invite a user and add them to some groups.
    g.invite_core_user("user2@example.com", "Experts", "Engineering")
    ```

    Args:
      email (str): The email address of the user to add to the team.
      *groups (str): Any number of groups to add the user to.
    
    Returns:
      response (str): parsed JSON response.
      status (int): response status code
    """
    
    response, status = self.__invite_user(email, *groups)

    return response, status

  def upgrade_light_user(self, email):
    """
    Upgrades a light user to a core user.

    ```
    g.upgrade_light_user("user1@example.com")
    ```

    Args:
      email (str): The email address of the light user.
    Returns:
      response (str): parsed JSON response.
      status (int): response status code
    """

    # check if user is Light user first, then upgrade

    # load the user list so we can check if the user is a member and a light user.
    users = self.get_members(email, cache=False)
    user = find_by_email(users, email)

    if not user:
      self.__log(make_red("could not find user:", email))
      return

    if not user.is_light:
      self.__log(make_red("user is not a light user:", email))
      return
  
    data = {}
    url = "%s/members/%s/upgrade" % (self.base_url, email)
    response = self.__post(url, data)

    return status_to_bool(response.status_code)
  
  def downgrade_core_user(self, email):
    """
    Downgrades a core user to a light user.

    ```
    g.downgrade_core_user("user1@example.com")
    ```

    Args:
      email (str): The email address of the core user.
    Returns:
      response (str): parsed JSON response.
      status (int): response status code
    """

    # check if user is Core user first, then downgrade

    # load the user list so we can check if the user is a member and a core user.
    users = self.get_members(email, cache=False)
    user = find_by_email(users, email)

    if not user:
      self.__log(make_red("could not find user:", email))
      return

    if not user.is_core:
      self.__log(make_red("user is not a core user:", email))
      return
  
    data = {}
    url = "%s/members/%s/downgrade" % (self.base_url, email)
    response = self.__post(url, data)

    return status_to_bool(response.status_code)
  
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
    for email in emails:
      if not is_email(email):
        raise ValueError("invalid email '%s'" % email)
    
    group_obj = self.get_group(group)
    if not group_obj:
      self.__log(make_red("could not find group:", group))
      return

    results = {}

    # the largest possible batch size is 100.
    batch_size = 100

    while len(emails) > 0:
      failed_emails = []
      for index in range(0, len(emails), batch_size):
        batch = emails[index:index + batch_size]
        
        url = "%s/groups/%s/members" % (self.base_url, group_obj.id)
        response = self.__post(url, batch)

        # either they were all successful or all failed.
        if status_to_bool(response.status_code):
          for obj in response.json():
            email = obj.get("id")
            if email:
              results[email] = True
        else:
          failed_emails += batch
          for email in batch:
            results[email] = False
      
      # if we just tried with batch_size = 1 and some still didn't work, then we're done.
      # otherwise make the batch size smaller and try again.
      if batch_size == 1:
        break
      elif batch_size >= len(failed_emails):
        batch_size = max(int(len(failed_emails) / 5), 1)
      else:
        batch_size = max(int(batch_size / 2), 1)
      
      emails = failed_emails
    
    return results

  def add_user_to_groups(self, email, *groups):
    """
    Adds a user to one or more groups. If the user is already in some
    of the groups provided, that's ok. All groups must already exist, no
    new groups will be created here.

    The user must already be on the team. If you need to invite a user
    and also assign them to groups, you can call `invite_user` and pass
    that the list of groups to both invite them and add them to groups.

    ```
    g.add_user_to_groups("user@example.com", "Experts", "Engineering")
    ```

    Args:
      email (str): The user being added to groups.
      *groups (str): Any number of groups to add the user to. Can be
        group names, IDs, or group objects (like what you'd get from
        calling get_group()).

    Returns:
      dict of str: bool: The keys are the group names and the values
        indicate whether the addition was successful (True) or not (False).
    """
    if not is_email(email):
      raise ValueError("invalid email '%s'" % email)
      
    groups = list(groups)
    self.__log("add user", make_blue(email), "to groups", make_blue(groups))

    # load the user list so we can check if any of these assignments were already made.
    users = self.get_members(email, cache=False)
    user = find_by_email(users, email)

    if not user:
      self.__log(make_red("could not find user:", email))
      return

    if user.is_light:
      self.__log(make_red("user is a light user, and cannot belong to groups:", email))
      return

    # for each group, track whether the addition was successful or not.
    result = {}
    for group in groups:
      # we have the group name but we need its ID.
      group_obj = self.get_group(group, cache=True)
      if not group_obj:
        self.__log(make_red("could not find group:", group))
        result[group] = False
        continue
      
      # check if the user is already assigned to this group.
      if not find_by_id(user.groups, group_obj.id):
        url = "%s/groups/%s/members" % (self.base_url, group_obj.id)
        response = self.__post(url, [email])
        result[group_obj.name] = status_to_bool(response.status_code)
      else:
        self.__log(make_gray("  %s is already in the group %s" % (email, group_obj.name)))
        result[group_obj.name] = True
    
    return result
  
  def add_user_to_group(self, email, group):
    """
    Adds a user to a single group. This requires that the group exists and
    that the user is on the team. It's ok if the user hasn't logged in yet
    but they need to have been invited at least.

    If you're adding the user to many groups you can call `add_user_to_groups`.

    If you need to invite the user and assign them to groups you an call `invite_user`.

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
    if not is_email(email):
      raise ValueError("invalid email '%s'" % email)
    
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
    if not is_email(email):
      raise ValueError("invalid email '%s'" % email)
    
    self.__log("remove", make_blue(email), "from the team")
    data = {
      "collectionVerifiers": {}
    }
    url = "%s/members/%s/replaceverifier" % (self.base_url, email)
    response = self.__delete(url, data)
    return status_to_bool(response.status_code)

  def get_card(self, card, is_archived=False):
    """
    Loads a single card by its ID or slug. The slug comes from the card's URL, like this:

    ```
    # load this card: https://app.getguru.com/card/Tbbqo5pc/Getting-Started-with-the-Guru-SDK
    card = g.get_card("Tbbqo5pc")
    print(card.title)
    print(card.content)
    ```

    Args:
      card (str): The card's ID or slug.
      is_archived (bool, optional): If the card you're looking for is archived or might be
        archived, pass True for this value. Otherwise leave it False (which is the default value).
    
    Returns:
      Card: An object representing the card.
    """
    if isinstance(card, Card):
      return card

    url = "%s/cards/%s/extended" % (self.base_url, card)
    response = self.__get(url)
    if status_to_bool(response.status_code):
      # todo: figure out why this is inside a 'try'.
      try:
        return Card(response.json(), guru=self)
      except:
        return None
    elif is_archived and response.status_code == 404:
      # if it's a 404 it might be an archived card and we need to use
      # the regular endpoint, not the /extended one, to load it.
      url = "%s/cards/%s" % (self.base_url, card)
      response = self.__get(url)
      try:
        return Card(response.json(), guru=self)
      except:
        return None

  def get_cards(self, card_ids):
    url = "%s/cards/bulk" % self.base_url
    data = {
      "ids": card_ids
    }

    response = self.__post(url, data)

    # this returns a dict where each key is a card ID and the value
    # is the card object plus a 'status' field, so we convert the
    # nested card objects to instances of the Card class.
    if status_to_bool(response.status_code):
      return {id: Card(obj) for id, obj in response.json().items()}
    else:
      return {}

  def get_visible_cards(self):
    """
    Gets the count of all cards on the team where you have read access or higher.

    This is helpful when you want to run a script that checks all cards for a certain
    kind of image or link, this gives you an easy way to see how many of the team's
    cards you're able to see.

    Args:
      none

    Returns:
      int: The number of cards you can view.
    """
    url = "%s/search/visible" % self.base_url
    response = self.__get(url)
    return int(response.headers.get("x-guru-total-cards"))

  def get_card_version(self, card, version):
    """
    Loads a previous version of a card.

    Args:
      card (str or Card): The card's ID, slug, or the full Card object.
      version (int): The version number to retrieve.
    """
    card_obj = self.get_card(card)
    if not card_obj:
      self.__log(make_red("could not find card:", card))
      return

    url = "%s/cards/%s/versions/%s" % (
      self.base_url, card_obj.id, version
    )
    response = self.__get(url)
    if status_to_bool(response.status_code):
      return Card(response.json(), guru=self)

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

  def find_card(self, **kwargs):
    cards = self.find_cards(**kwargs)
    if self.dry_run:
      return Card({}, guru=self)
    if cards:
      return cards[0]

  def find_cards(
    self, title="", tag="", collection="", author="", verified=None, unverified=None,
    created_before=None, created_after=None, last_modified_before=None, last_modified_after=None,
    last_modified_by=None, archived=False
  ):
    """
    Gets a list of cards that match the criteria defined by the parameters.
    All parameters are optional. Calling find_cards() selects all cards you
    have read access to. Parameter may be combined to find cards that match
    all specified criteria (e.g. cards in a collection that also have the
    specified tag).

    ```
    # list all cards in the Engineering collection created after April 1.
    for card in g.find_cards(collection="Engineering", created_after="2020-04-01"):
      print(card.url)
    ```

    Args:
      title (str, optional): Optional parameter to select cards containing the
        specified text in their title. Not case sensitive.
      tag (str, optional): Optional parameter to select cards containing the
        specified tag. Can be the tag's name or ID.
      collection (str, optional): Optional parameter to select cards within the
        specified collection. Can be the collection's name or ID.
      author (str, optional): Optional parameter to select cards originally created
        by the specified user (email address).
      verified (bool, optional): Optional parameter to select only verified cards
        (verified=True) or unverified cards (verified=False).
      unverified (bool, optional): Also lets you select only verified or unverified
        cards, but gives you the option of saying verified=False or unverified=True.
      created_before (str, optional): Optional parameter to select cards created before
        a certain date and time.
      created_after (str, optional): Optional parameter to select cards created after a
        certain date and time.
      last_modified_before (str, optional): Optional parameter to select cards last
        modified before a certain date and time.
      last_modified_after (str, optional): Optional parameter to select cards last
        modified after a certain date and time.
      last_modified_by (str, optional): Optional parameter to select cards last
        modified by the specified user (email address).
      archived (bool, optional): Sets the query to search archived cards. 
        Can be mixed with title, tag, and/ or collection.
    
    Returns:
      list of Card: The cards that matched the parameters you provided.
    """
    if archived:
      data = {
        "queryType": "archived",
        "sorts": None,
        "query": None,
        "collectionIds": []
      }
    else:
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
      collection_obj = self.get_collection(collection, cache=True)
      if not collection_obj:
        raise BaseException("collection '%s' not found" % collection)

      data["collectionIds"] = [collection_obj.id]

    # if no tag value was passed in, get_tag() will return nothing.
    nested_expressions = []
    if tag:
      tag_obj = self.get_tag(tag)
      if not tag_obj:
        self.__log(make_red("could not find tag:", tag))
        return []

      nested_expressions.append({
        "type": "tag",
        "ids": [tag_obj.id],
        "op": "EXISTS"
      })

    if title:
      nested_expressions.append({
        "type": "title",
        "value": title,
        "op": "CONTAINS"
      })

    if author:
      nested_expressions.append({
        "type": "originalOwner",
        "email": author,
        "op": "EQ"
      })

    # if these are set to the same value that either means they're both
    # omitted (both = None) or they're contradictory - we interpret
    # verified=True and unverified=True to mean we select all cards.
    if verified == unverified:
      pass
    elif verified == True or unverified == False:
      nested_expressions.append({
        "type": "trust-state",
        "verificationState": "TRUSTED",
        "op": "EQ"
      })
    elif verified == False or unverified == True:
      nested_expressions.append({
        "type": "trust-state",
        "verificationState": "NEEDS_VERIFICATION",
        "op": "EQ"
      })

    # the card manager UI doesn't allow for this, but the API
    # lets you specify both 'created before' and 'created after'.
    if created_before:
      nested_expressions.append({
        "type": "absolute-date",
        "value": format_timestamp(created_before),
        "op": "LT",
        "field": "DATECREATED"
      })
    if created_after:
      nested_expressions.append({
        "type": "absolute-date",
        "value": format_timestamp(created_after),
        "op": "GTE",
        "field": "DATECREATED"
      })

    if last_modified_before:
      nested_expressions.append({
        "type": "absolute-date",
        "value": format_timestamp(last_modified_before),
        "op": "LT",
        "field": "LASTMODIFIED"
      })
    if last_modified_after:
      nested_expressions.append({
        "type": "absolute-date",
        "value": format_timestamp(last_modified_after),
        "op": "GTE",
        "field": "LASTMODIFIED"
      })

    if last_modified_by:
      nested_expressions.append({
        "type": "last-modified-by",
        "email": last_modified_by,
        "op": "EQ"
      })

    if nested_expressions:
      data["query"] = {
        "nestedExpressions": nested_expressions,
        "op": "AND",
        "type": "grouping"
      }

    url = "%s/search/cardmgr" % self.base_url
    cards = self.__post_and_get_all(url, data)
    return [Card(c, guru=self) for c in cards]

  def __get_upload_key(self):
    """internal"""
    # the key we get here is valid for 24 hours which means it could expire, but we'll assume
    # for now your script won't run for 24+ hours.
    if self.__upload_key:
      return self.__upload_key

    url = "%s/attachments/policy" % self.base_url
    self.__upload_key = self.__get(url).json()
    return self.__upload_key

  def upload_to_filestack(self, filename):
    # get an upload key, read the file, do the call to filestack, return fs_data.
    upload_key = self.__get_upload_key()

    # read the file and upload it to filestack.
    with open(filename, "rb") as file_in:
      file_mimetype, file_encoding = mimetypes.guess_type(filename)
      url = "https://www.filepicker.io/api/store/S3?key=%s&filename=%s&mimetype=%s&path=%s&signature=%s&policy=%s" % (
        upload_key.get("apiKey"),
        os.path.basename(filename),
        file_mimetype,
        upload_key.get("path"),
        upload_key.get("signature"),
        upload_key.get("policy")
      )
      files = {
        "fileUpload": (filename, file_in)
      }
      response = self.__post(url, files=files)
      if response.status_code != 200:
        self.__log(make_red("status %s uploading to filestack" % response.status_code))
        return

      # the response has a bunch of values we need, particularly the filestack url.
      # the full response looks like this:
      #   {
      #     "container": "fs.getguru.com",
      #     "url": "https://cdn.filepicker.io/api/file/YtOIxff7T8Cyu2OZaF7m",
      #     "filename": "screenshot.jpeg",
      #     "key": "d7277b61-3974-4228-bcd7-4e4e220e93cb/iasnMk0TROCyLZPX9QIk_4e2d7a8627e34e8c8406e6b38f481941.jpeg",
      #     "type": "image/jpeg",
      #     "size": 4083
      #   }
      fs_data = response.json()
      return fs_data
  
  def create_attachment(self, fs_data):
    # make the /attachments call and return the 'link' value we get back.

    # make the call to our backend so we know the attachment was uploaded
    # and what its filestack url is.
    url = "%s/attachments" % self.base_url
    data = {
      "filestackKey": fs_data.get("key"),
      "filestackUrl": fs_data.get("url"),
      "filestackClient": "",
      "filename": fs_data.get("filename"),
      "size": fs_data.get("size"),
      "mimeType": fs_data.get("type")
    }
    response = self.__post(url, data=data)

    # the response from our api gives us the content.api.getguru.com URL for the file.
    # the full response looks like this:
    #   {
    #     "mimeType" : "image/jpeg",
    #     "link" : "https://content.api.getguru.com/files/view/3886ec47-a99d-4431-848e-cff2d73a49f3",
    #     "filename" : "screenshot.jpeg",
    #     "filestackKey" : "d7277b61-3974-4228-bcd7-4e4e220e93cb/iasnMk0TROCyLZPX9QIk_4e2d7a8627e34e8c8406e6b38f481941.jpeg",
    #     "attachmentId" : "3886ec47-a99d-4431-848e-cff2d73a49f3",
    #     "filestackUrl" : "https://cdn.filepicker.io/api/file/YtOIxff7T8Cyu2OZaF7m",
    #     "filestackClient" : "",
    #     "size" : 4083
    #   }
    if status_to_bool(response.status_code):
      return response.json().get("link")

  def upload_file(self, filename):
    """
    Uploads a file, like an image or pdf, to Guru so you can reference it in cards.

    ```
    # load a card and add a pdf to it.
    card = g.get_card("Tbbqo5pc")
    url = g.upload_file("/Users/rob/Documents/getting-started.pdf")
    card.content += '<a href="%s">getting-started.pdf</a>' % url
    card.save()
    ```

    Args:
      filename (str): The file on your computer that you want to upload to Guru.

    Returns:
      str: The Guru URL for the attachment, something like: https://content.api.getguru.com/files/view/3886ec47-a99d-4431-848e-cff2d73a49f3
    """
    # there are three steps here:
    # 1. make sure we have an upload key for filestack, we get this from our API. ( handled in `upload_to_filestack()`)
    # 2. make the /S3 call to upload the file to filestack (FS gives us the attachment URL in their response). ( handled in `upload_to_filestack()`)
    # 3. make the /attachment call to tell guru about the newly created attachment. ( handled in `create_attachment()`)

    fs_data = self.upload_to_filestack(filename)
    return self.create_attachment(fs_data)

  def patch_card(self, card, keep_verification=True):
    """
    Patches a card, updating its content, title, and verification interval.

    Args:
      card (Card): The card object you're saving.
      keep_verification (bool, optional): True if you want to save the card without
        triggering Guru's default business logic of unverifying a card when the user
        editing the card is not its verifier. This defaults to true.

    Returns:
      Card: An updated card object.
    """

    # todo: maybe just use card.json() here because we will have more complete
    #       objects and passing in extra fields is not a problem.
    data = {
      "preferredPhrase": card.title,
      "content": card.content
    }
    # todo: add 'verifiers' to the fields we patch.
    if card.verification_interval:
      data["verificationInterval"] = card.verification_interval

    url = "%s/cards/%s?keepVerificationState=%s" % (
      self.base_url,
      card.id,
      "true" if keep_verification else "false"
    )
    response = self.__patch(url, data)
    return Card(response.json()), status_to_bool(response.status_code)

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

  def verify_card(self, card_obj):
    """
    Verifies a card.

    Args:
      card_obj (Card): The Card object for the card you're verifying.
    
    Returns:
      bool: True if it was successful and False otherwise.
    """
    url = "%s/cards/%s/verify" % (self.base_url, card_obj.id)
    response = self.__put(url)
    return status_to_bool(response.status_code)
  
  def unverify_card(self, card_obj):
    """
    Unverifies a card.

    Args:
      card_obj (Card): The Card object for the card you're unverifying.
    
    Returns:
      bool: True if it was successful and False otherwise.
    """
    url = "%s/cards/%s/unverify" % (self.base_url, card_obj.id)
    response = self.__post(url)
    return status_to_bool(response.status_code)

  def get_favorite_lists(self):
    url = "%s/favoritelists" % self.base_url
    return [Board(b) for b in self.__get(url).json()]

  def favorite_card(self, card):
    # find the favorites list to add it to.
    favorite_lists = self.get_favorite_lists()

    if not favorite_lists:
      self.__log(make_red("could not find any favorite lists"))
      return
    else:
      favorite_list = favorite_lists[0]
    
    card_obj = self.get_card(card)
    if not card_obj:
      self.__log(make_red("could not find card:", card))
      return False
    
    data = {
      "prevSiblingItem": "last",
      "actionType": "add",
      "boardEntries": [{
        "cardId": card_obj.id,
        "entryType": "card"
      }]
    }

    url = "%s/favoritelists/%s/entries" % (self.base_url, favorite_list.id)
    response = self.__put(url, data)
    return status_to_bool(response.status_code)
  
  def unfavorite_card(self, card):
    card_obj = self.get_card(card)
    if not card_obj:
      self.__log(make_red("could not find card:", card))
      return False
    
    url = "%s/cards/%s/favorite" % (self.base_url, card_obj.id)
    response = self.__delete(url)
    return status_to_bool(response.status_code)

  def restore_card(self, card):
    """
    Restores an archived card.

    ```
    import guru
    g = guru.Guru()

    # you can restore cards like this:
    g.restore_card("11111111-1111-1111-1111-111111111111")

    # or like this:
    g.get_card("11111111-1111-1111-1111-111111111111").restore()
    ```

    Args:
      card (str or Card): The ID or slug of the card to be restored or the Card object.

    Returns:
      bool: True if it was successful and False otherwise.
    """
    card_obj = self.get_card(card, is_archived=True)
    if not card_obj:
      self.__log(make_red("could not find card:", card))
      return False

    return self.restore_cards(card_obj.id)

  def restore_cards(self, *card_ids, timeout=0):
    """
    Restores many archived cards. This is done as a bulk operation
    so this may be faster than making 10 separate calls to restore
    10 cards.

    ```
    import guru
    g = guru.Guru()

    g.restore_cards(
      "11111111-1111-1111-1111-111111111111",
      "22222222-2222-2222-2222-222222222222"
    )
    ```

    The operation may be done synchronously or asynchronously. Meaning, if you
    pass in a single card ID, Guru will restore that one card before returning
    a response. If you pass in 100 cards, Guru will immediately respond to say
    "we've queued this up" and will work on it asynchronously.

    You may want to wait for the operation to complete. For example, if you're
    restoring a bunch of cards then adding them to a board, you need to wait for
    the 'restore' operation to finish. To make this happen you can use the
    `timeout` parameter, which is the number of seconds to wait for the operation
    to complete. The SDK will automatically check the bulk operation's status
    and return once it is successful (or once the timeout has been reached).

    Args:
      *card_ids (str): Any number of card IDs. These are the IDs of the archived
        cards that will be restored.
      timeout (int, optional): The maximum number of seconds to wait for the bulk
        operation to complete. By default, there is no timeout and we won't wait
        for asynchronous bulk operations at all.

    Returns:
      bool: True if it was successful and False otherwise.
    """
    data = {
      "action": {
        "type": "restore-archived-card"
      },
      "items": {
        "type": "id",
        "cardIds": card_ids
      }
    }

    url = "%s/cards/bulkop" % self.base_url
    response = self.__post(url, data)

    # if there's a timeout and the operation is being done async, we wait.
    if timeout and response.status_code == 202:
      # poll and wait for the bulk operation to finish.
      bulk_op_id = response.json().get("id")
      url = "%s/cards/bulkop/%s" % (self.base_url, bulk_op_id)
      return self.__wait_for_bulkop(url, timeout)
    else:
      # todo: make this return a more detailed status since the operation can
      #       succeed for some cards and fail for others.
      return status_to_bool(response.status_code)

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

  def get_drafts(self, card=None):
    if card:
      card_obj = self.get_card(card)
      if not card_obj:
        self.__log(make_red("could not find card:", card))
        return
      
      url = "%s/drafts/%s" % (self.base_url, card_obj.id)
    else:
      url = "%s/drafts" % (self.base_url)
    
    drafts = self.__get_and_get_all(url)
    drafts = [Draft(d, guru=self) for d in drafts]
    return drafts

  def create_draft(self, title, content, json_content=""):
    data = {
      "content": content,
      # todo: most users won't have json content -- is that ok?
      "jsonContent": json_content,
      "title": title,
      "saveType": "USER"
    }
    url = "%s/drafts" % self.base_url
    response = self.__post(url, data)
    if status_to_bool(response.status_code):
      return Draft(response.json())

  def delete_draft(self, draft):
    url = "%s/drafts/%s" % (self.base_url, draft.id)
    response = self.__delete(url)
    return status_to_bool(response.status_code)

  def add_comment_to_card(self, card, comment):
    """
    Adds a comment to a card. You can also add comments through the Card object, like thisL

    ```
    # load a card using it's slug and add a comment.
    card = g.get_card("TyRM678c")
    card.add_comment("Is this still a good doc to include in our onboarding materials?")
    ```

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

  def get_card_comments(self, card, status=None):
    """
    Gets all comments on a card.

    Args:
      card (str): The name or ID of the card.
      status (str): Either OPEN or RESOLVED, for the respective comment spaces of the card.
    
    Returns:
      list of CardComment: The card's comments.
    """
    card_obj = self.get_card(card)
    if not card_obj:
      self.__log(make_red("could not find card:", card))
      return
    if status:
      url = "%s/cards/%s/comments?status=%s" % (self.base_url, card_obj.id, status)
    else:
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

  def resolve_card_comment(self, comment_obj):
    """
    Resolves a card comment.

    Args:
      comment_obj (CardComment): The CardComment object to be resolved.
    
    Returns:
      bool: True if it was successful and False otherwise.
    """
    # https://api.getguru.com/api/v1/cards/a0201644-5dcf-4a90-868c-fb5e4981aa17/comments/2ecb2e09-e78a-4de8-90ac-f075e1cf6447/resolve
    url = "%s/cards/%s/comments/%s/resolve" % (self.base_url, comment_obj.card.id, comment_obj.id)
    response = self.__put(url)
    return status_to_bool(response.status_code)

  def reopen_card_comment(self, comment_obj):
    """
    Reopens a card comment, putting it back in the Open comment box.

    Args:
      comment_obj (CardComment): The CardComment object to be resolved.
    
    Returns:
      bool: True if it was successful and False otherwise.
    """
    # https://api.getguru.com/api/v1/cards/a0201644-5dcf-4a90-868c-fb5e4981aa17/comments/2ecb2e09-e78a-4de8-90ac-f075e1cf6447/resolve
    url = "%s/cards/%s/comments/%s/unresolve" % (self.base_url, comment_obj.card.id, comment_obj.id)
    response = self.__put(url)
    return status_to_bool(response.status_code)

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

  def get_tag(self, tag, cache=False):
    """
    Gets a tag.

    Args:
      tag (str): The tag's ID or text value (without the leading "#").
    
    Returns:
      Tag: An object reprensenting the tag.
    """
    if not tag:
      return

    if isinstance(tag, Tag):
      return tag

    tags = self.get_tags(cache=cache)
    for t in tags:
      if t.value.lower() == tag.lower() or t.id.lower() == tag.lower():
        return t

  def get_team_id(self, cache=True):
    url = "%s/whoami" % self.base_url
    response = self.__get(url, cache=cache)
    return response.json().get("team", {}).get("id")

  def get_tags(self, cache=False):
    # https://api.getguru.com/api/v1/teams/014dc5f6-9488-43fe-a892-206d276a7a9c/tagcategories/
    url = "%s/teams/%s/tagcategories" % (self.base_url, self.get_team_id())

    # this returns a list of objects where each object represents a tag category
    # and looks like this:
    #   {
    #     "tags": [ tags... ],
    #     "id": "abcd1234",
    #     "name": "category"
    #   }
    response = self.__get(url, cache=cache)

    tags = []
    for tag_category in response.json():
      tags += [Tag(t) for t in tag_category.get("tags", [])]
    return tags

  def get_tag_category(self, category="Tags"):
    url = "%s/teams/%s/tagcategories" % (self.base_url, self.get_team_id())
    response = self.__get(url, cache=True)
    for tag_category in response.json():
      if tag_category["name"].lower() == category.lower():
        return tag_category.get("id")

  def make_tag(self, tag):
    data = {
      "categoryId": self.get_tag_category(),
      "value": tag
    }
    url = "%s/teams/%s/tagcategories/tags" % (self.base_url, self.get_team_id())
    response = self.__post(url, data)
    return Tag(response.json())

  def delete_tag(self, tag):
    """
    Deletes a tag.

    Args:
      tags (str or Tag): Either a tag's name, ID, or the Tag object.
    """
    tag_object = self.get_tag(tag)
    if not tag_object:
      self.__log(make_red("could not find tag:", tag))
      return False
    
    url = "%s/teams/%s/bulkop" % (self.base_url, self.get_team_id())
    data = {
      "action": {
        "type": "delete-tag",
        "tagId": tag_object.id
      }
    }
    response = self.__post(url, data)
    return status_to_bool(response.status_code)

  def merge_tags(self, *tags):
    """
    Merge two or more tags. This is the same action you can
    do through Tag Manager.

    Args:
      Any number of arguments where each is either a tag's value, ID, or a Tag object.
    
    Returns:
      bool: True if it was successful and False otherwise.
    """
    tag_objects = []
    for tag in tags:
      tag_object = self.get_tag(tag)
      if tag_object:
        tag_objects.append(tag_object)
      else:
        self.__log(make_red("could not find tag:", tag))
        return False
    
    url = "%s/teams/%s/bulkop" % (self.base_url, self.get_team_id())
    data = {
      "action": {
        "type": "merge-tag",
        "mergeSpec": {
          "parentId": tag_objects[0].id,
          "childIds": [t.id for t in tag_objects[1:]]
        }
      }
    }
    response = self.__post(url, data)
    return status_to_bool(response.status_code)

  def add_tag_to_card(self, tag, card, create=False):
    """
    Adds a tag to a card using the PUT call to do just this, rather than
    using the PUT call to update an entire card.

    Args:
      tag (str or Tag): A Tag's value, ID, or the Tag object.
      card (str or Card): A card's slug, ID, or the Card object.

    Returns:
      Tag: The Tag object in case this was a newly created tag and you need
        to use that object. Will return None if it was unsuccessful.
    """
    tag_object = self.get_tag(tag)
    if not tag_object and create:
      tag_object = self.make_tag(tag)

    if not tag_object:
      self.__log(make_red("could not find tag:", tag))
      return

    card_object = self.get_card(card)
    if not card_object:
      self.__log(make_red("could not find card:", card))
      return

    url = "%s/cards/%s/tags/%s" % (self.base_url, card_object.id, tag_object.id)
    response = self.__put(url)
    if status_to_bool(response.status_code):
      return tag_object

  def get_board(self, board, collection=None, cache=True):
    """
    Loads a board.

    Args:
      id (str): The board's full ID or slug.
    
    Returns:
      Board: An object representing the board.
    """
    if isinstance(board, Board) or isinstance(board, HomeBoard):
      return board

    # if the value looks like a slug or uuid, try treating it like one and make the API call to
    # load this board directly. if this fails, we fall back to loading a list of all boards and
    # scanning it to match by title.
    if is_board_slug(board) or is_uuid(board):
      url = "%s/boards/%s" % (self.base_url, board)
      response = self.__get(url)
      if status_to_bool(response.status_code):
        return Board(response.json(), guru=self)

    # todo: use the 'collection' parameter as a way to also filter, in case the same board appears
    #       in more than one collection (board titles still aren't unique within a collection though).

    # this returns a list of 'lite' objects that don't have the lists of items on the board.
    # once we find the matching board, then we can make the get call to get the complete object.
    board_obj = find_by_name_or_id(self.get_boards(collection, cache), board)
    
    if not board_obj:
      self.__log(make_red("could not find board:", board))
      return

    url = "%s/boards/%s" % (self.base_url, board_obj.id)
    response = self.__get(url)
    return Board(response.json(), guru=self)
  
  def get_boards(self, collection=None, cache=False):
    """
    Gets a list of boards you can see. You can optionally filter by collection.

    Args:
      collection (str or Collection, optional): The name or ID of a collection or a Collection object
        to filter by. If this is not provided, you'll get back a list of all boards in all collections
        you can see.

    Returns:
      list of Board: Either all boards you have access to or all boards within the specified collection.
    """
    # filtering by collection is optional.
    if collection:
      collection_obj = self.get_collection(collection)
      if not collection_obj:
        self.__log(make_red("could not find collection:", collection))
        return
      url = "%s/boards?collection=%s" % (self.base_url, collection_obj.id)
    else:
      url = "%s/boards" % self.base_url
    
    response = self.__get(url, cache)
    return [Board(b, guru=self) for b in response.json()]

  def get_board_group(self, board_group, collection):
    """
    Loads a board group.

    Args:
      board_group(str): The name of the board group.
      collection(str or Collection): The name of the collection or the Collection object
        for the collection that contains the board group you're looking for.

    Returns:
      BoardGroup: an object representing the board group.
    """
    if isinstance(board_group, BoardGroup):
      return board_group

    home_board_obj = self.get_home_board(collection)
    
    for item in home_board_obj.items:
      if isinstance(item, BoardGroup) and item.title.lower() == board_group.lower():
        return item

  def make_board_group(self, collection, title, desc=""):
    """
    Creates a new board group. It'll be added as the last item in the collection.

    Args:
      collection (str or Collection): A collection ID or a Collection object
        the board group will be added to.
      title (str): The title for the new board group.
      desc (str, optional): The description of the new board group.
    
    Returns:
      bool: True if it was successful and False otherwise.
    """
    # https://api.getguru.com/api/v1/boards/home/entries?collection=fac2ed4d-a2c0-4d47-b409-5a988fe8dcf7
    collection_obj = self.get_collection(collection)
    if not collection_obj:
      self.__log(make_red("could not find collection:", collection))
      return
    
    data = {
      "actionType": "add",
      "boardEntries": [{
        "entryType": "section",
        "title": title,
        "description": desc
      }],
      # "nextSiblingItem": "b93799c8-6fb7-467d-a8ea-9a6e62ff8e93"
    }
    url = "%s/boards/home/entries?collection=%s" % (self.base_url, collection_obj.id)

    # this doesn't need to have a timeout or wait for a response because it's just
    # creating one board so that should always be done synchronously.
    response = self.__put(url, data)
    if status_to_bool(response.status_code):
      return self.get_board_group(title, collection)

  def add_board_to_board_group(self, board, board_group, collection=""):
    """
    Adds an existing board to a board group. You can also load the Board and
    BoardGroup objects and add boards like this:

    ```
    board_group = g.get_board_group("Onboarding", "Engineering")
    board_group.add_board("Week 1")
    ```

    Args:
      board (str or Board): The name, ID, or slug of the Board or a Board object.
      board_group (str or BoardGrop): The name of the Board Group or a BoardGroup object.
      collection (str or Collection): The name or ID of the Collection the board and board group
        are located in, or the Collection object.

    Returns:
      bool: True if it was successful and False otherwise.
    """
    board_obj = self.get_board(board, collection)
    if not board_obj:
      self.__log(make_red("could not find board:", board))
      return
    
    board_group_obj = self.get_board_group(board_group, collection)
    if not board_group_obj:
      self.__log(make_red("could not find board group:", board_group))
      return
    
    # bug: board_obj doesn't have an item_id, we only get that when we load the home board.
    data = {
      "sectionId": board_group_obj.item_id,
      "actionType": "move",
      "boardEntries": [
        {
          "id": board_obj.item_id,
          "entryType": "board"
        }
      ],
      # this makes us insert it as the first item in the board group.
      # if we omit this, we get a 500 error.
      "prevSiblingItem": board_group_obj.item_id
    }
    url = "%s/boards/home/entries?collection=%s" % (self.base_url, board_obj.collection.id)
    response = self.__put(url, data)
    return status_to_bool(response.status_code)

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
    return HomeBoard(response.json(), guru=self)

  def set_item_order(self, collection, board, *items):
    """
    Rearranges a board or board group's items based on the values provided.
    This doesn't add or remove any items, it just rearranges the items that
    are already there.

    It also doesn't rearrange items inside sections on a board. If a board
    has two sections each with 3 cards, this just rearranges the two sections.
    There will be a separate way (or an update to this method) to let it
    rearrange content inside sections.

    This method is often not called directly. Instead you'd make the call to
    load a board then call its set_item_order method, like this:

    ```
    board = g.get_board("My Board")
    board.set_item_order("Card 1", "Card 2", "Card 3")
    ```

    Args:
      collection (str or Collection): A collection to filter by if you're
        specifying a board title.
      board (str or Board or BoardGroup): Either a string that'll match a
        board's name or the Board or BoardGroup object whose items you're
        rearranging.
      *items (str): The names of the objects in the order you want them to appear.
    
    Returns:
      None
    """
    if isinstance(board, BoardGroup):
      board_obj = board
    else:
      board_obj = self.get_board(board, collection)
      if not board_obj:
        return
    
    def get_key(b):
      for i in range(len(items)):
        if b.title.lower().strip() == items[i].lower().strip():
          return i
      # if we couldn't find it, move it to the back.
      return len(items)

    board_obj.items.sort(key=get_key)
    
    # if it's a board group, we need to save the entire home board.
    if isinstance(board_obj, BoardGroup):
      self.save_board(board_obj.home_board)
    else:
      self.save_board(board_obj)

  def make_board(self, title, collection, description=""):
    """
    Creates a new board in the specified collection.

    Args:
      title (str): The title of the board you're creating. Board titles are not
        unique so we do not check if a board with the same title already exists.
      collection (str or Collection): The name or ID of the collection you're adding
        the board to, or a Collection object.
      description (str, optional): The description of the board you're creating.

    Returns:
      bool: True if it was successful and false otherwise.
    """
    collection_obj = self.get_collection(collection)
    if not collection_obj:
      self.__log(make_red("could not find collection:", collection))

    url = "%s/boards/home/entries?collection=%s" % (self.base_url, collection_obj.id)
    data = {
      "actionType": "add",
      "boardEntries": [{
        "entryType": "board",
        "title": title,
        "description": description
      }]
    }

    # this doesn't need to have a timeout or wait for a response because it's just
    # creating one board so that should always be done synchronously.
    response = self.__put(url, data)
    return status_to_bool(response.status_code)

  def save_board(self, board_obj):
    url = "%s/boards/%s" % (self.base_url, board_obj.id)
    response = self.__put(url, data=board_obj.json(include_item_id=False))

    if status_to_bool(response.status_code):
      # todo: update the board obj so the caller doesn't have to store this return value.
      return board_obj

  def add_card_to_board(self, card, board, section=None, collection=None, create_section_if_needed=False):
    """
    Adds a card to a board. You can optionally provide the name of a section
    to add the card to. The card will be added to the end -- either to the
    end of the board if no section is specified or to the end of the specified
    section.

    The board can be defined using its ID or slug, which uniquely identify it.
    You can also use its title. If there are multiple boards with the same title
    you can also provide a collection name, then it'll find the board with a
    matching name in that collection.

    Board names still don't have to be unique inside a collection. If you run
    into this problem, you'll have to use the board's ID or slug.

    You can also do this using the Board or Card objects:

    ```
    # load a card using its slug and add it to a board:
    card = g.get_card("TyRM678c")
    card.add_to_board("Onboarding")

    # or you load the board and add cards like this:
    board = g.get_board("Onboarding", collection="Engineering")
    board.add_card("TyRM678c")
    ```

    Args:
      card (str or Card): The card to be added to the board. Can either be the
        card's title, ID, slug, or the Card object.
      board (str or Board): The board you're adding the card to. Can either be
        the board's title, ID, slug, or the Board object.
      section (str, optional): The name of the section to add the card to.
      collection (str or Collection, optional): The collection in which the board
        resides. This is optional but might be necessary if you're identifying the
        board by title and the same title is used by boards in different collections.
    
    Returns:
      None
    """
    # get the card object.
    card_obj = self.get_card(card)
    if not card_obj:
      self.__log(make_red("could not find card:", card))
      return
    
    # get the board object.
    board_obj = self.get_board(board, collection)
    if not board_obj:
      self.__log(make_red("could not find board:", board))
      return
    
    if section:
      # find the section (if applicable).
      section_obj = find_by_name_or_id(board_obj.items, section)
      if not section_obj:
        if create_section_if_needed:
          board_obj.add_section(section)
          # load the objects again so we get the updated board and section.
          board_obj = self.get_board(board_obj.id, cache=False)
          section_obj = find_by_name_or_id(board_obj.items, section)
        else:
          self.__log(make_red("could not find section:", section))
          return
      
      # add the card to the section.
      section_obj.items.append(card_obj)
    else:
      # add the card to the board.
      board_obj.items.append(card_obj)
    
    self.save_board(board_obj)

  def add_section_to_board(self, board, section, collection=None):
    """
    Adds a section to a board.

    You can also do this through the Board object:

    ```
    # load a board using its slug and add some new sections.
    board = g.get_board("Onboarding", collection="Engineering")
    board.add_section("Week 1")
    board.add_section("Week 2")
    board.add_section("Week 3")
    ```

    Args:
      board (str or Board): The board you're adding the section to. Can either
        be the board's title, ID, slug, or the Board object.
      section (str, optional): The name of the section you're adding.
      collection (str or Collection, optional): The collection in which the board
        resides. This is optional but might be necessary if you're identifying the
        board by title and the same title is used by boards in different collections.
    
    Returns:
      bool: True if it was successful and False otherwise.
    """
    # get the board object.
    board_obj = self.get_board(board, collection)
    if not board_obj:
      return

    url = "%s/boards/%s/entries" % (
      self.base_url,
      board_obj.id
    )
    data = {
      "actionType": "add",
      "boardEntries": [{
        "entryType": "section",
        "title": section
      }]
    }
    response = self.__put(url, data)
    return status_to_bool(response.status_code)

  def remove_card_from_board(self, card, board, collection=None):
    """
    Removes a card from a board.

    Args:
      card (str or Card): The card to be removed from the board. Can either be
        the card's title, ID, slug, or the Card object.
      board (str or Board): The board you're removing the card from. Can either
        be the board's title, ID, slug, or the Board object.
      collection (str or Collection, optional): The collection in which the board
        resides. This is optional but might be necessary if you're identifying the
        board by title and the same title is used by boards in different collections.

    Returns:
      bool: True if it was successful and False otherwise.
    """
    board_obj = self.get_board(board, collection)
    if not board_obj:
      return
    
    card_obj = board_obj.get_card(card)
    if not card_obj:
      self.__log(make_red("could not find card:", card))
      return
    
    url = "%s/boards/%s/entries" % (self.base_url, board_obj.id)
    data = {
      "actionType": "remove",
      "collectionId": board_obj.collection.id,
      "id": board_obj.id,
      "boardEntries": [{
        "entryType": "card",
        "id": card_obj.item_id
      }]
    }
    response = self.__put(url, data)
    return status_to_bool(response.status_code)

  def bundle(self, id="default", clear=True, folder="/tmp/", verbose=False, skip_empty_sections=False):
    """
    Creates a Bundle object that can be used to bulk import content.
    """
    return Bundle(guru=self, id=id, clear=clear, folder=folder, verbose=verbose, skip_empty_sections=skip_empty_sections)
  
  def sync(self, id="default", clear=True, folder="/tmp/", verbose=False, skip_empty_sections=False):
    """
    internal: sync() is an alias for bundle().
    """
    return Bundle(guru=self, id=id, clear=clear, folder=folder, verbose=verbose, skip_empty_sections=skip_empty_sections)

  def get_events(self, start="", end="", max_pages=10):
    """
    Load a list of events from the /analytics API. Check [this doc](https://developer.getguru.com/docs/list-analytics-data)
    for more information about this endpoint.

    The start and end parameters are timestamps that can either be full
    timestamps like `"2021-02-01T15:01:30.000+04:00"` or just dates like
    `"2021-02-01"`.
    """
    team_id = self.get_team_id()
    if not team_id:
      self.__log(make_red("couldn't find your Team ID, are you authenticated?"))
      return

    url = "%s/teams/%s/analytics?fromDate=%s&toDate=%s" % (
      self.base_url,
      team_id,
      start,
      end
    )
    return self.__get_and_get_all(url, max_pages=max_pages)

  def get_shared_groups(self, board):
    board_obj = self.get_board(board)
    if not board_obj:
      self.__log(make_red("could not find board:", board))
      return
    
    url = "%s/boards/%s/permissions" % (self.base_url, board_obj.id)
    response = self.__get(url)
    return [BoardPermission(b) for b in response.json()]
  
  def add_shared_group(self, board, group):
    """
    Shares a board with a group using the Board Permissions settings.
    This is how you share specific boards with groups that don't have full
    read access to the collection.

    You can also do this through the board object:

    ```
    # load a board using its slug and share it with a group:
    board = g.get_board("KTRX8zMT")
    board.add_group("Sales")
    ```

    Args:
      board (str or Board): The board's ID or slug or a Board object.
      group (str or Group): The group's name or ID or a Group object.

    Returns:
      bool: True if it was successful and False otherwise.
    """
    group_obj = self.get_group(group)
    if not group_obj:
      self.__log(make_red("could not find group:", group))
      return
    
    board_obj = self.get_board(board)
    if not board_obj:
      self.__log(make_red("could not find board:", board))
      return
    
    data = [{
      "type": "group",
      "role": "MEMBER",
      "group": {
        "id": group_obj.id
      }
    }]
    
    url = "%s/boards/%s/permissions" % (self.base_url, board_obj.id)
    response = self.__post(url, data)
    return status_to_bool(response.status_code)
  
  def remove_shared_group(self, board, group):
    group_obj = self.get_group(group)
    if not group_obj:
      self.__log(make_red("could not find group:", group))
      return
    
    board_obj = self.get_board(board)
    if not board_obj:
      self.__log(make_red("could not find board:", board))
      return
    
    # find the id of the permission assignment.
    perm_obj = None
    for perm in self.get_shared_groups(board_obj):
      if perm.group.id == group_obj.id:
        perm_obj = perm
        break
    
    if not perm_obj:
      self.__log(make_red("could not find assigned permission for group %s, maybe it's not assigned to this board" % group))
      return

    url = "%s/boards/%s/permissions/%s" % (self.base_url, board_obj.id, perm_obj.id)
    response = self.__delete(url)
    return status_to_bool(response.status_code)

  def move_board_to_collection(self, board, collection, timeout=0):
    """
    Moves a board from one collection to another.

    Args:
      board (str or Board): The board to be moved. Can either be the board's title,
        ID, slug, or the Board object.
      collection (str or Collection): The collection you're moving the board to. Can
        either be the collection's title, ID, or the Collection object.
      timeout (int, optional): The API call to move a board just queues up the operation.
        This parameter is used if you want to wait until Guru is done moving the board to
        its new collection. This helpful if you want to do multiple operations, like move
        a board to a new collection then add it to a board group there. By default this is
        0 so it doesn't wait. If you set a timeout of 10, we'll wait up to 10 seconds to
        see if the move completes.

    Returns:
      bool: True if it was successful and False otherwise. False could mean that there was
        an error or that you were waiting for the operation to finish and it timed out.
    """
    board_obj = self.get_board(board, collection=collection)
    if not board_obj:
      self.__log(make_red("could not find board:", board))
      return

    collection_obj = self.get_collection(collection)
    if not collection_obj:
      self.__log(make_red("could not find collection:", collection))
      return

    # if the board is already in that collection, do nothing.
    if board_obj.collection and board_obj.collection.id == collection_obj.id:
      self.__log(make_red("board", board_obj.title, "is already in collection", collection_obj.name))
      return

    # make the bulk op call to move the board to the other collection.
    data = {
      "action": {
        "type": "move-board",
        "collectionId": collection_obj.id
      },
      "items": {
        "type": "id",
        "itemIds": [board_obj.id]
      }
    }

    url = "%s/boards/bulkop" % self.base_url
    response = self.__post(url, data)

    # if there's a timeout and the operation is being done async, we wait.
    if timeout and response.status_code == 202:
      # poll and wait for the bulk operation to finish.
      bulk_op_id = response.json().get("id")
      url = "%s/boards/bulkop/%s" % (self.base_url, bulk_op_id)
      return self.__wait_for_bulkop(url, timeout)
    else:
      return status_to_bool(response.status_code)

  def __wait_for_bulkop(self, url, timeout):
    elapsed = 0
    while True:
      time.sleep(2)
      response = self.__get(url)
      if response.status_code == 200:
        return True

      elapsed += 2
      if elapsed >= timeout:
        break

    return False

  def get_questions(self, type="INBOX", cache=False):
    url = "%s/tasks/questions?filter=%s" % (self.base_url, type)
    questions = self.__get_and_get_all(url, cache)
    questions = [Question(q, guru=self) for q in questions]
    return questions

  def get_questions_inbox(self, cache=False):
    """
    Gets the questions in your inbox.

    Returns:
      list of Question: A list of Question objects for each question in your inbox.
    """
    return self.get_questions("INBOX", cache)

  def get_questions_sent(self, cache=False):
    """
    Gets the questions you have sent.

    Returns:
      list of Question: A list of Question objects for each question you've sent.
    """
    return self.get_questions("SENT", cache)

  def delete_question(self, question):
    """
    Deletes a question. Can be applied to a question you've sent or received.

    Args:
      question (str or Question): Either question's ID as a string or a Question object.

    Returns:
      bool: True if it was successful and False otherwise.
    """
    if isinstance(question, Question):
      url = "%s/tasks/questions/%s" % (self.base_url, question.id)
    else:
      url = "%s/tasks/questions/%s" % (self.base_url, question)
    response = self.__delete(url)
    return status_to_bool(response.status_code)

  def download_card_as_pdf(self, card, filename):
    card_obj = self.get_card(card)
    if not card_obj:
      self.__log(make_red("could not find card:", card))
      return

    url = "https://api.getguru.com/api/v1/cards/%s/pdf" % card_obj.id
    headers = {
      "Authorization": self.__get_basic_auth_value()
    }

    status, file_size = download_file(url, filename, headers=headers)
    return status_to_bool(status)
