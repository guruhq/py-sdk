
import re
import os
import sys
import json
import time
import yaml
import shutil
import requests
import pytz
import dateutil.parser

from datetime import datetime
from bs4 import BeautifulSoup

if sys.version_info.major >= 3:
  from urllib.parse import urljoin
else:
  from urlparse import urljoin

# the limit is now 5 GB
# todo: figure out how to enforce this automatically, currently its up to your download_func to check this.
# todo: check this before downloading the whole file.
# todo: apply this to local files too (i.e. before copying them into resources/ we check their size).
MAX_FILE_SIZE = 5000000000

TRACKING_HEADERS = {
    "X-Guru-Application": "sdk",
    "X-Amzn-Trace-Id": "GApp=sdk"
}


def load_html(url, cache=False, make_links_absolute=True, headers=None):
  """Fetches HTML from the given URL and returns it as a BeautifulSoup document object."""
  if url.startswith("http"):
    html, status_code = http_get(url, cache, headers)
    if status_code >= 400:
      return "", status_code
  else:
    html = read_file(url)
    status_code = 200

  doc = BeautifulSoup(html, "html.parser")

  # since we know the url this is all coming from we can make link urls
  # absolute so we don't have to worry about that later on.
  if make_links_absolute:
    for link in doc.select("a"):
      href = link.attrs.get("href")
      if href:
        link.attrs["href"] = urljoin(url, href)
    for image in doc.select("img"):
      src = image.attrs.get("src")
      if src:
        image.attrs["src"] = urljoin(url, src)

  return doc, status_code


def http_get(url, cache=False, headers=None):
  """Makes an HTTP GET request and returns the body content."""
  if not headers:
    headers = {}

  # if you're making a request to a getguru.com url, include our tracking headers.
  if "getguru.com" in url:
    for header in TRACKING_HEADERS:
      headers[header] = TRACKING_HEADERS[header]

  non_alphanumeric = re.compile("[^a-zA-Z0-9]")
  cached_file = "./cache/%s.html" % non_alphanumeric.sub("", url)
  if cache:
    cached_content = read_file(cached_file)
    if cached_content:
      return cached_content, 200

  response = requests.get(url, headers=headers)

  # todo: figure out a better way to handle this.
  #       this code was originally needed for gitlab's sync but causes issues in other ones.
  # html = response.content.decode("utf-8").encode("ascii", "ignore")
  html = response.content.decode("utf-8")
  write_file(cached_file, html)

  return html, response.status_code


def http_post(url, data=None, cache=False, headers=None):
  """Makes an HTTP POST request and returns the body content."""
  if not headers:
    headers = {}

  # if you're making a request to a getguru.com url, include our tracking headers.
  if "getguru.com" in url:
    for header in TRACKING_HEADERS:
      headers[header] = TRACKING_HEADERS[header]

  non_alphanumeric = re.compile("[^a-zA-Z0-9]")
  cached_file = "./cache/%s.html" % non_alphanumeric.sub("", url)
  if cache:
    cached_content = read_file(cached_file)
    if cached_content:
      return cached_content, 200

  response = requests.post(url, json=data, headers=headers)
  html = response.content.decode("utf-8")
  write_file(cached_file, html)

  return html, response.status_code


def download_file(url, filename, headers=None, cache=False):
  """Downloads an image and saves it as the full filename you provide."""
  if cache and os.path.isfile(filename):
    return 200, os.path.getsize(filename)

  # if you're making a request to a getguru.com url, include our tracking headers.
  if "getguru.com" in url:
    for header in TRACKING_HEADERS:
      headers[header] = TRACKING_HEADERS[header]

  response = requests.get(url, headers=headers, allow_redirects=True)
  file_size = 0
  if response.status_code == 200:
    make_dir(filename)
    with open(filename, "wb") as file_out:
      if len(response.content):
        file_size = len(response.content)
        file_out.write(response.content)
      else:
        file_size = len(response.raw)
        response.raw.decode_content = True
        shutil.copyfileobj(response.raw, file_out)

  return response.status_code, file_size


def make_dir(filename):
  """Given a path or full filename, this creates the directory if it doesn't exist."""
  if not os.path.exists(os.path.dirname(filename)):
    os.makedirs(os.path.dirname(filename))


def clear_dir(dir):
  """Deletes all files and folders inside the given directory."""
  if not os.path.exists(dir):
    return
  for file in os.listdir(dir):
    file_path = os.path.join(dir, file)
    try:
      if os.path.isfile(file_path):
        os.unlink(file_path)
      elif os.path.isdir(file_path):
        shutil.rmtree(file_path)
    except:
      pass


def write_file(filename, content):
  """Writes a text file."""
  make_dir(filename)
  with open(filename, "w") as file_out:
    file_out.write(content)


def read_file(filename):
  """Reads a text file."""
  try:
    with open(filename, "r") as file_in:
      return file_in.read()
  except:
    pass


def copy_file(src, dest):
  """Copies a file."""
  # the src value could have querystring params because it comes from
  # an image's src attribute, so we want to remove those.
  src = src.split("?")[0]

  try:
    make_dir(dest)
    try:
      shutil.copyfile(src, dest)
    except FileNotFoundError:
      raise FileNotFoundError("File not found", src)
    return True
  except:
    return False


def to_yaml(data):
  return yaml.dump(data, allow_unicode=True).replace("!!python/unicode ", "").replace("!!python/str ", "")


def find_by_name_or_id(lst, name_or_id):
  if not lst:
    return

  # it says "name or id" but we really need to check the 'title' and 'slug' properties too.
  name_or_id = (name_or_id or "").strip()
  for obj in lst:
    # some objects call it 'name', some call it 'title'.
    # for cards it's preferredPhrase but we also give them a title property.
    # for tags it's called 'value'.
    if hasattr(obj, "name") and obj.name.strip().lower() == name_or_id.lower():
      return obj
    if hasattr(obj, "title") and obj.title.strip().lower() == name_or_id.lower():
      return obj
    if hasattr(obj, "value") and obj.value.strip().lower() == name_or_id.lower():
      return obj
    if obj.id.lower() == name_or_id.lower():
      return obj
    if hasattr(obj, "slug") and obj.slug and obj.slug.startswith(name_or_id + "/"):
      return obj


def find_by_email(lst, email):
  def func(obj):
    return (obj.email or "").strip().lower() == (email or "").strip().lower()
  filtered = [x for x in lst if func(x)]
  if filtered:
    return filtered[0]


def find_by_id(lst, id):
  def func(obj):
    return (obj.id or "").strip().lower() == (id or "").strip().lower()
  filtered = [x for x in lst if func(x)]
  if filtered:
    return filtered[0]


def format_timestamp(timestamp):
  """
  Return a timestamp formatted like: 2021-03-15T00:00:00-04:00

  The input can vary. It might be a shorter value, like just "2021-03-15",
  or it could be more complete.
  """
  return "%s-00:00" % dateutil.parser.parse(timestamp).isoformat()


def compare_datetime_string(date_to_compare, comparison, date_to_compare_against="", tz_aware=False):
  """
  Compares 2 datetime strings

  Args:
    date_to_compare (str): date string to compare
    comparison (str): comparison operator (i.e. lt, lt_or_eq, eq, ne, gt, or gt_or_eq)
    date_to_compare_against (str or datetime obj): date to compare against
    tz_aware (bool, optional): is `date_to_compare` time-zone aware

  Default:
    Compares date provided to the current datetime

  Returns:
    bool: True or False, depending on comparison evaluation
  """
  date_to_compare = dateutil.parser.parse(date_to_compare)
  if date_to_compare_against:
    date_to_compare_against = dateutil.parser.parse(date_to_compare_against)
  elif tz_aware and not date_to_compare_against:
    date_to_compare_against = datetime.now(pytz.utc)
  else:
    date_to_compare_against = datetime.now()

  if comparison == "gt":
    return date_to_compare > date_to_compare_against
  elif comparison == "gt_or_eq":
    return date_to_compare >= date_to_compare_against
  elif comparison == "lt":
    return date_to_compare < date_to_compare_against
  elif comparison == "lt_or_eq":
    return date_to_compare <= date_to_compare_against
  elif comparison == "eq":
    return date_to_compare == date_to_compare_against
  elif comparison == "ne":
    return date_to_compare != date_to_compare_against
  else:
    raise ValueError(
        "Please provide a valid comparison option (lt, gt, lt_or_eq, gt_or_eq, eq, ne")


def load_json(filename):
  """returns JSON object from file."""
  try:
    with open(filename, "r") as file_in:
      return json.loads(file_in.read())
  except:
    return {}


def save_json(filename, data):
  """writes data to a file, as JSON."""
  with open(filename, "w") as file_out:
    file_out.write(json.dumps(data, indent=2))


def clean_slug(string):
  return re.sub(r"/.*", "", string)
