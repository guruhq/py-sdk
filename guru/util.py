
import re
import os
import sys
import yaml
import shutil
import requests

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

def load_html(url, cache=False, make_links_absolute=True, headers=None):
  """Fetches HTML from the given URL and returns it as a BeautifulSoup document object."""
  if url.startswith("http"):
    html = http_get(url, cache, headers)
  else:
    html = read_file(url)
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

  return doc

def http_get(url, cache=False, headers=None):
  """Makes an HTTP GET request and returns the body content."""
  if not headers:
    headers = {}

  non_alphanumeric = re.compile("[^a-zA-Z0-9]")
  cached_file = "./cache/%s.html" % non_alphanumeric.sub("", url)
  if cache:
    cached_content = read_file(cached_file)
    if cached_content:
      return cached_content
  
  response = requests.get(url, headers=headers)

  # todo: figure out a better way to handle this.
  #       this code was originally needed for gitlab's sync but causes issues in other ones.
  # html = response.content.decode("utf-8").encode("ascii", "ignore")
  html = response.content.decode("utf-8")
  write_file(cached_file, html)
  
  return html

def http_post(url, data=None, cache=False, headers=None):
  """Makes an HTTP POST request and returns the body content."""
  if not headers:
    headers = {}

  non_alphanumeric = re.compile("[^a-zA-Z0-9]")
  cached_file = "./cache/%s.html" % non_alphanumeric.sub("", url)
  if cache:
    cached_content = read_file(cached_file)
    if cached_content:
      return cached_content

  response = requests.post(url, json=data, headers=headers)
  html = response.content.decode("utf-8")
  write_file(cached_file, html)

  return html

def download_file(url, filename, headers=None):
  """Downloads an image and saves it as the full filename you provide."""
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
    shutil.copyfile(src, dest)
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
    if hasattr(obj, "name") and obj.name.strip().lower() == name_or_id.lower():
      return obj
    if hasattr(obj, "title") and obj.title.strip().lower() == name_or_id.lower():
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
