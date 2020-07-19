
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

# 250 MB
# todo: figure out how to enforce this automatically.
MAX_FILE_SIZE = 250000000

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
  html = str(response.content)
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
