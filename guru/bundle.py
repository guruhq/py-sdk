
import re
import os
import csv
import sys
import time
import hashlib
import zipfile
import requests
import webbrowser

from bs4 import BeautifulSoup

if sys.version_info.major >= 3:
  from urllib.parse import urljoin
else:
  from urlparse import urljoin

from guru.util import clear_dir, write_file, copy_file, download_file, to_yaml, http_post, http_get, load_html

# node types
NONE = "NONE"
FOLDER = "FOLDER"
CARD = "CARD"

MAX_FOLDER_DEPTH = 3

def slugify(text):
  return re.sub(r"[^a-zA-Z0-9_\-]", "", text.replace(" ", "_"))

def _url_to_id(url, include_extension=True):
  id = hashlib.md5(url.encode("utf-8")).hexdigest()

  # take everything after the last . before the ?
  if include_extension:
    url = url.split("?")[0]
    extension = url.split(".")[-1]
    if len(extension) < 5:
      return "%s.%s" % (id, extension)
  return id

def _id_to_filename(id):
  return id.replace("/", "_")

def _is_local(url_or_path):
  if url_or_path.startswith("http") or url_or_path.startswith("mailto:"):
    return False
  elif url_or_path.startswith("//"):
    return False
  elif not url_or_path.startswith("file:") and re.match(r'[a-zA-Z]{1,}\:\/\/.*', url_or_path):
    return False
  else:
    return True

def _parse_style(text):
  result = {}
  pairs = text.split(";")

  for pair in pairs:
    # split a "width: 400px" kind of string into the key and value.
    index = pair.find(":")
    key = pair[0:index].strip()
    value = pair[index + 1:].strip()
    result[key] = value
  
  return result

def _format_style(values):
  return ";".join(["%s:%s" % (key, values[key]) for key in values.keys()])

def clean_up_html(html):
  doc = BeautifulSoup(html, "html.parser")

  # when we see 'colspan' in a table, insert extra cells so the original TD plus
  # the extra TDs take up the expected number of columns. for colspan="3" we insert
  # two TDs after the original one so together they span three columns.
  # rowspan is harder because we'd have to insert TDs into the next rows.
  for td in doc.select("[colspan]"):
    for i in range(1, int(td.attrs.get("colspan", 1))):
      new_td = doc.new_tag("td")
      td.insert_after(new_td)
    del td.attrs["colspan"]

  # only keep the attributes we need otherwise they just take up space.
  attributes_to_keep = [
    "style",
    "start",   # for numbered lists
    "href",    # for links...
    "target",
    "rel",
    "title",
    "src",     # for images...
    "alt",
    "height",
    "width",
    "class",   # for guru elements...
    "data-ghq-card-content-type",
    "data-ghq-card-content-markdown-content"
  ]
  for el in doc.select("*"):
    for attr in list(el.attrs.keys()):
      if attr not in attributes_to_keep:
        del el.attrs[attr]

    # keep any class name that starts with 'ghq-'
    old_class_list = el.attrs.get("class") or []
    new_class_list = list(filter(lambda c: c.startswith("ghq-"), old_class_list))

    if new_class_list:
      el.attrs["class"] = new_class_list
    elif el.has_attr("class"):
      # we only remove the 'class' attribute if it was there in the first place.
      del el.attrs["class"]

  # clean up lists inside table cells.
  for li in doc.select("td li"):
    # todo: only add the br tag if the list has a previous sibling.
    # todo: make this work for numbered lists.
    br = doc.new_tag("br")
    li.insert(0, "- ")
    li.insert(0, br)
    li.unwrap()
  
  for ul in doc.select("td ul, td ol"):
    ul.unwrap()

  # table cells don't really handle multiple blocks, or one block with
  # text before or after it. so, we try to convert all blocks to inlines.
  # <p> becomes <span>, <h1> (or any heading) becomes <strong>, <pre>
  # becomes <code>. once those conversions are made we also insert a <br>
  # tag between every pair of inlines to make the line breaks look like
  # they would when the elements were block elements.
  for td in doc.select("td"):

    # we use this to look up the new tag name. if a match isn't found here
    # we'll assume it's a heading and convert it to a <strong> tag.
    # note: these spans will likely get unwrapped later because we unwrap
    #       unstyled span tags later on.
    block_to_inline = {
      "p": "span",
      "pre": "code"
    }
    had_block_elements = False
    for block in td.select("p, pre, h1, h2, h3, h4, h5, h6"):
      block.name = block_to_inline.get(block.name, "strong")
      had_block_elements = True

    # if any conversions happened, insert <br> tags between each pair of inlines.
    if had_block_elements:
      for inline in td.select("span ~ span, span ~ strong, span ~ code, strong ~ span, strong ~ strong, strong ~ code, code ~ span, code ~ strong, code ~ code"):
        inline.insert_before(doc.new_tag("br"))

  # we don't use these tags for anything but they might contain content
  # so we call unwrap() rather than calling decompose().
  for el in doc.select("html, body, header, nav, article"):
    el.unwrap()

  # we don't use these tags and we don't want their content either, like the JS code
  # inside a script tag, so we call decompose() to remove them completely.
  for el in doc.select("colgroup, table caption, script, style, meta, title, head"):
    el.decompose()

  # when a block item, like a table or code block, is inside a list we need to get it out.
  # but we want to keep it's relative position (e.g. rather than moving it to be after the
  # entire list).
  for block in doc.select("ol table, ul table, ol iframe, ul iframe, ol pre, ul pre"):

    # check the blocks's ancestors for certain elements, like <li> tags, and keep a list
    # of all the tags we need to close to create a break for where the block goes.
    parents_to_close = []
    next_ol_start = 1
    node = block

    while node:
      if node.name in ["ol", "ul", "li"]:
        # if this item is in a numbered list, we want to find out what number this item had
        # and compute the number the list should continue at. the number the continuation
        # starts at is based on this item's index and the number this list started at.
        if node.name == "li" and node.parent.name == "ol":
          ol = node.parent

          # we take the ol's non-text chilren and find the index of this <li> in that list.
          list_items = list(filter(lambda x: not isinstance(x, str), list(ol.children)))
          li_index = list_items.index(node)
          ol_start = int(ol.attrs.get("start", "1"))
          next_ol_start = ol_start + li_index + 1

        parents_to_close.append(node.name)
      node = node.parent

    # we insert text strings before/after the block indicating what tags we need to close/re-open.
    # once the doc is converted to an html string, we'll replace these markers with < and > to
    # create the actual html tags. this ends up being easier than doing the manipulations using
    # beautifulsoup to move nodes around.
    for tag in parents_to_close:
      block.insert_before("[[GURU[[/%s]]GURU]]" % tag)
      if tag == "ol":
        next_ol_start
        block.insert_after('[[GURU[[%s start="%s"]]GURU]]' % (tag, next_ol_start))
      else:
        block.insert_after("[[GURU[[%s]]GURU]]" % tag)

  # look for things like ul > ul and unwrap the child list.
  # we expect nested lists to be wrapped in an <li> and if they're not,
  # it introduces an extra blank list item when it's viewed in guru.
  for child_list in doc.select("ul > ul, ul > ol, ol > ol, ol > ul"):
    child_list.unwrap()

  # remove unnecessary things from style attributes (e.g. width/height on table cells).
  style_attrs_to_keep = [
    "background",
    "background-color",
    "color",
    "font-style",
    "font-weight",
    "text-decoration"
  ]

  for el in doc.select("[style]"):
    # style attributes are ok if the element is inside a guru markdown block.
    # the styles you'll usually see are the ones in the encoded markdown attribute but
    # the ones on the nested HTML might be used somewhere (maybe public cards?).
    if el.find_parent("div", attrs={"class": "ghq-card-content__markdown"}):
      continue

    values = _parse_style(el.attrs["style"])
    for attr in list(values.keys()):
      if attr not in style_attrs_to_keep:
        del values[attr]
    el.attrs["style"] = _format_style(values)

    # if removing some properties left the style attribute empty, remove it altogether.
    if not el.attrs["style"].strip():
      del el.attrs["style"]

  # remove spans that have no style attributes.
  for el in doc.select("span"):
    if not el.attrs or not el.attrs.get("style"):
      el.unwrap()
  
  # remove empty blocks. for a block to be empty it has to meet all of these criteria:
  #
  #  - contain no visible text.
  #  - contain either no tags, or contains only br, div, or span tags.
  #
  # the second rule is important otherwise we'll remove paragraphs that contain only an image, iframe, etc.
  elements_to_remove_if_empty = ["p", "li", "h1, h2, h3, h4, h5, h6"]
  for selector in elements_to_remove_if_empty:
    for el in doc.select(selector):
      text = el.text.strip()
      if not text:
        all_tag_count = len(el.select("*"))
        unimportant_tag_count = len(el.select("br, div, span"))
        if all_tag_count == unimportant_tag_count:
          el.decompose()

  # remove empty ol and ul tags.
  for ol in doc.select("ol, ul"):
    if len(ol.select("li")) == 0:
      ol.decompose()

  return (
    str(doc)
      .replace("\\n", "\n")
      .replace("\\'", "'")
      # when we break a list around a code block, if there's no other content in the list item,
      # either before or after, the substitutions we do create an extra, empty list item.
      # doing these two replacements will avoid that.
      .replace("<li>[[GURU[[/li]]GURU]]", "")
      .replace("[[GURU[[li]]GURU]]</li>", "")
      .replace("[[GURU[[", "<")
      .replace("]]GURU]]", ">")
  )

def traverse_tree(bundle, func, node=None, parent=None, depth=0, post=False, **kwargs):
  """Traverses the tree and applies the function `func` to each node."""
  if node:
      if node.removed:
          return
      func(node, parent, depth, **kwargs)
      for id in node.children[:]:
          child = bundle.node(id)
          if child:
              traverse_tree(bundle, func, child, node, depth + 1, post, **kwargs)
      if post:
          func(node, parent, depth, post=True, **kwargs)
  else:
      # Traverse the subtree for every node that doesn't have a parent.
      for node in bundle.nodes:
          if not node.parents and not node.removed:
              traverse_tree(bundle, func, node, post=post, **kwargs)

def make_spreadsheet(node, parent, depth, rows):
  """internal"""
  # if the 'rows' list is empty, add the headings to it.
  if not rows:
    rows.append([
      "Index",
      "ID",
      "External URL",
      "Type",
      "Title",
      "# of Children",
      "HTML Length",
      "# of HTML Tags",
      "# of Essential HTML Tags",
      "Word Count",
      "H1s",
      "H2s",
      "H3s",
      "All Headings",
      "Iframes",
      "All Links",
      "Guru Card Links",
      "Guru File Links",
      "Table Cells",
      "All Images",
      "Attached Images"
    ])

  indent = "    " * min(3, depth)
  values = [
    len(rows),
    node.id,
    node.url or "",
    node.type,
    '"' + indent + node.title + '"'
  ]

  # number of children:
  if node.type == CARD:
    values.append("")
    values.append("")
  elif node.type == FOLDER:
    all_children = node.get_children_recursively()
    folders = list(filter(lambda n: n.type == FOLDER, all_children))
    values.append(len(all_children))
    values.append(len(folders))
  else:
    values.append(len(node.get_children_recursively()))
    values.append("")

  # for nodes with content we put additional values in the sheet,
  # like word count, # of headings, # of links, etc.
  if node.type == CARD:
    doc = BeautifulSoup(node.content, "html.parser")
    # these are the tag types that are absolutely essential, otherwise
    # we're changing what the content looks like. some other tags, like
    # divs, might be required to format the content correctly, but there's
    # also a chance that some divs aren't needed.
    essential_tags = "p, a, img, iframe, table, tr, th, td, h1, h2, h3, h4, h5, h6, ul, ol, li, em, strong, pre, code"
    values += [
      len(node.content),                         # html length
      len(doc.select("*")),                      # number of tags
      len(doc.select(essential_tags)),           # number of essential tags (p, img, table, etc.)
      len(re.split(r"\s+", doc.text)),            # word count
      len(doc.select("h1")),                     # number of H1s
      len(doc.select("h2")),                     # number of H2s
      len(doc.select("h3")),                     # number of H3s
      len(doc.select("h1, h2, h3, h4, h5, h6")), # number of headings
      len(doc.select("iframe")),                 # number of iframes
      len(doc.select("a[href]")),                # all links
      len(doc.select('a[href^="cards/"]')),      # guru card links,
      len(doc.select('a[href^="resources/"]')),  # guru file links,
      len(doc.select("td")),                     # table cells
      len(doc.select("img")),                    # images
      len(doc.select('img[src^="resources/"]')), # attached images
    ]

  rows.append(values)

def make_html_tree(node, parent, depth, html_pieces):
  """internal: This builds the folder/card tree in the HTML preview page."""
  if node.removed:
    return

  if node.type == CARD:
    url = node.bundle.CARD_HTML_PATH % (node.bundle.id, node.id)
    html_pieces.append(
      '<a href="%s" data-depth="%s" data-original-url="%s" target="iframe">%s (%s)</a>' % (url, depth, node.url, node.title, node.type)
    )
  else:
    html_pieces.append(
      '<div data-depth="%s">%s (%s)</div>' % (depth, node.title, node.type)
    )

def print_node(node, parent, depth):
  """internal"""
  """Prints the node information."""
  indent = "  " * depth
  parent_str = f", parent={parent.id}" if parent else ""
  if node.url:
      print(f"{indent}- {node.title or node.id} ({node.type}, url={node.url})")
  else:
      print(f"{indent}- {node.title or node.id} ({node.type})")

def print_type(node, parent, depth):
  print("%s- %s" % ("  " * min(3, depth), node.type))

def mark_node_and_descendants_removed(node):
    node.removed = True
    # Remove node from parents' children lists
    for parent in node.parents:
        if node.id in parent.children:
            parent.children.remove(node.id)
    # Remove node from children's parents lists and recursively remove children
    for child_id in node.children:
        child_node = node.bundle.node(child_id)
        if node in child_node.parents:
            child_node.parents.remove(node)
        # Recursively remove descendants
        mark_node_and_descendants_removed(child_node)

def assign_types(node, parent, depth, post=False):
  """
  internal:
  When you're done adding content to a bundle we call this for every
  node to figure out which nodes become folders and cards.
  """

  max_folder_depth = MAX_FOLDER_DEPTH
  if not post:
    if node.type is None:
      if node.children:
        if depth < max_folder_depth:
            node.type = FOLDER
        else:
            # Mark node and descendants as removed, note: add 1 to depth in log file b/c zero based.
            mark_node_and_descendants_removed(node)
            node.bundle.log(
                message="Folder discarded due to exceeding maximum folder depth",
                node_id=node.id,
                depth=depth + 1
            )
      elif node.content:
        node.type = CARD
      else:
          node.type = CARD
  else:
      pass  # No post-traversal adjustments needed

def insert_nodes(node, parent, depth):
  """internal:
  If a node that ends up being Folder and also has
  content of its own, we need to insert additional nodes so its
  content has a place to go.

  additional check to ensure we don't exceed max folder depth of 3.
  Folders exceeding depth of 3 will be logged and discarded. This is to prevent
  the import from failing by providing a proper import file.
  """
  if node.removed:
      return
  if node.content and node.type == FOLDER:
    # Add a CARD as the first child
    content_id = f"{node.id}_content"
    content_node = node.bundle.node(
        id=content_id,
        url=node.url,
        title=node.title,
        content=node.content,
        alt_urls=node.alt_urls,
        type=CARD
    )
    node.add_child(content_node, first=True)
    node.url = ""

class BundleNode:
  def __init__(self, id, bundle, url="", title="", desc="", content="", tags=None, alt_urls=None, index=None, node_type=None):
    self.id = id
    self.bundle = bundle
    self.url = ""
    self.desc = desc
    self.title = title or id
    self.content = content
    self.children = []
    self.parents = []
    self.type = node_type
    self.tags = tags
    self.alt_urls = alt_urls
    self.removed = False
    if index is None:
      self.index = 9999
    else:
      self.index = index

  def add_to(self, node):
    """Adds this object as a child of the given node."""
    node.add_child(self)
    return self
  
  def remove(self):
    self.bundle.remove_node(self)

  def detach(self):
    """Removes a node from all of its parents."""
    # for node in self.bundle.nodes:
    #   if self.id in node.children:
    #     node.children.remove(self.id)
    for node in self.parents:
      node.children.remove(self.id)
    self.parents = []
    return self

  def move_to(self, parent):
    """Removes the node from all of its parents and assign it a new parent."""
    self.detach()
    parent.add_child(self)
    return self

  def ancestors(self):
    result = self.parents[:]
    index = 0
    while index < len(result):
      result += result[index].parents
      index += 1
    return result

  def add_child(self, child, first=False, after=None):
    """
    Adds the given node as a child of this one.
    
    By default children are added to the end of the parent's list
    of children but passing first=True makes the new child go first.
    """
    
    # check if 'child' is already an ancestor of 'self'.
    for ancestor in self.ancestors():
        if ancestor.id == child.id:
            raise RuntimeError(f"adding '{child.title or child.id}' as a child of '{self.title or self.id}' would create a cycle")

    if child.id in self.children:
        return

    child.parents.append(self)
    if first:
        self.children.insert(0, child.id)
    elif after:
        index = self.children.index(after.id)
        self.children.insert(index + 1, child.id)
    else:
        self.children.append(child.id)

    return self
  
  def get_children_recursively(self):
    all_children = []
    for id in self.children:
      child = self.bundle.node(id)
      if not child.removed:
        all_children.append(child)
      all_children += child.get_children_recursively()
    return all_children

  def __make_items_list(self):
    """internal: This is used internally when we're building the .yaml files."""
    #recursively process child FOLDER and CARDs

    # do not process any nodes that deleted AND 
    # use case of Folder w/no children being first and skip_empty_folders is true, this will remove it.
    # otherwise, it would not get caught in the FOLDER processing below b/c that deals with folders that might be
    # empty within other Folders.
    if self.removed:
        return []  # Do not include removed nodes
    elif not self.children and self.type == FOLDER and self.bundle.skip_empty_folders:
      self.bundle.log(message="skipping empty folder", title=self.title, id=self.id)
      self.removed = True

    items = []
    for id in self.children:
      node = self.bundle.node(id)
      if node.removed:
        continue
      if node.type == CARD:
          items.append({
            "ID": node.id,
            "Type": "card"
          })
      elif node.type == FOLDER:
          folder_items = node.__make_items_list()
          # we can choose to skip empty folders. if there's a sync that's likely to create
          # empty cards, then that might make us more likely to end up with empty folders.
          if node.bundle.skip_empty_folders and not folder_items:
            node.bundle.log(message="skipping empty folder", title=self.title, id=self.id)
            node.removed = True
          else:
            folder_data = {
              "ID": node.id,
              "Type": "folder",
              "Title": node.title,
              "Items": folder_items
            }
            items.append(folder_data)
    return items

  def split_all(self, selector, nest=False):
    doc = BeautifulSoup(self.content, "html.parser")

    for element in doc.select(selector):
      element.insert_before("[GURU_SDK_BREAKPOINT]")

    html = str(doc)
    parts = html.split("[GURU_SDK_BREAKPOINT]")

    self.content = parts[0]

    # we go backwards so the parts end up in the correct order.
    for index in range(len(parts) - 1, 0, -1):
      new_content = parts[index]
      if not new_content.strip():
        continue

      new_doc = BeautifulSoup(new_content, "html.parser")
      new_title = self.title

      # if we split on h2s, find the first h2 in the doc and use that as the title.
      for element in new_doc.select(selector):
        new_title = element.text.strip()
        element.decompose()
        break

      # if this split would end up having no content, skip it.
      if not str(new_doc):
        continue

      new_node = self.bundle.node(
        id="%s_part%s" % (self.id, index),
        url=self.url,
        title=new_title or self.title,
        content=str(new_doc)
      )

      # add the new node after this existing node so it's on all the same folders.
      if nest:
        self.add_child(new_node, first=True)
      else:
        for parent_node in self.parents:
          parent_node.add_child(new_node, after=self)

  def split(self, *args):
    """
    The arguments are pairs of strings where the first string is a
    CSS selector indicating where to make a split and the second string
    is the title that should be applied to the new card.

    If you're not sure what the title should be you can pass empty strings
    and we'll name the new cards the same as the card you're splitting.
    """
    doc = BeautifulSoup(self.content, "html.parser")

    selectors = [args[i] for i in range(0, len(args), 2)]
    titles = [args[i] for i in range(1, len(args), 2)]

    for selector in selectors:
      elements = doc.select(selector)
      if elements:
        element = elements[0]
        element.insert_before("[GURU_SDK_BREAKPOINT]")

    # we split the html in two parts, the first part is the new content for this node
    # and the second part becomes the content of a new node.
    html = str(doc)
    parts = html.split("[GURU_SDK_BREAKPOINT]")

    # todo: we might need to run each half of the HTML through beautifulsoup, otherwise guru
    #       might be unhappy about the lack of closing tags.

    self.content = parts[0]

    # we go backwards so the parts end up in the correct order.
    for index in range(len(selectors) - 1, -1, -1):
      # part[0] is the new content for the 'root' card.
      # part[1] is the content for the first new card, whose title is title[0].
      new_content = parts[index + 1]
      new_title = titles[index]

      # if this piece has a title, we need to check for a heading tag where
      # the title came from. we don't want the first thing inside the card's
      # content to be an <h1> with the title, that'd be redundant.
      if new_title:
        # todo: how do we check if the heading is near the top of the card?
        #       it may not literally be the first child. if this heading is
        #       way towards the bottom and coincidentally has the same text
        #       content as the title, we want to leave it alone then.
        new_doc = BeautifulSoup(new_content, "html.parser")
        for heading in new_doc.select("h1, h2, h3, h4, h5, h6"):
          if heading.text.strip().lower() == new_title.strip().lower():
            heading.decompose()
            new_content = str(new_doc)

          # we only care about the first heading so we always break after the first iteration.
          break

      new_node = self.bundle.node(
        id="%s_part%s" % (self.id, index + 1),
        url=self.url,
        title=new_title or self.title,
        content=new_content
      )

      # add the new node after this existing node so it's on all the same folders.
      for parent_node in self.parents:
        parent_node.add_child(new_node, after=self)

  def html_cleanup(self, download_func=None, compare_links=None):
    """
    internal:
    This adjusts image and link URLs to either be absolute or refer to
    something in this import -- for cards this means we look for href
    values that should become card-to-card links and for images we look
    for references to files in the resources folder.

    This will eventually have the ability to download images.
    """
    # we only need to clean up the html for cards that have content.
    if not self.content or self.type != CARD or self.removed:
      return

    doc = BeautifulSoup(self.content, "html.parser")
    url_map = {}

    # this function can work on image and link URLs.
    def check_element(element, attr):
      url = element.attrs.get(attr, "")

      if url.startswith("data:") or url.startswith("mailto:"):
        return

      # remember this value so we can later check if it changed.
      initial_value = element.attrs[attr]

      # if we've already seen this URL, update this element in the same way.
      # this way if they have two links to the same file we only download it once.
      if initial_value in url_map:
        element.attrs[attr] = url_map[initial_value]
        return

      absolute_url = urljoin(self.url, url)
      resource_id = _url_to_id(absolute_url)

      # download_func is responsible for deciding if we need to download the file
      # and for doing the download too (since you probably need auth headers for
      # the download to work).
      if download_func:

        # if we've already downloaded this file, update the src/href.
        if resource_id in self.bundle.resources:
          element.attrs[attr] = self.bundle.resources[resource_id]
        else:
          filename = self.bundle.RESOURCE_PATH % (self.bundle.id, resource_id)
          self.bundle.log(message="checking if we should download attachment", url=absolute_url, file=filename)

          # you can either return True or return a tuple, with the http status code as the first item.
          # if the file didn't download, you would get a return of False or None.
          # if the file was downloaded we need to update the src/href.
          download_result = download_func(absolute_url, filename, self.bundle, self)

          is_successful = False
          if type(download_result) == type(True):
            is_successful = download_result
          elif download_result and isinstance(download_result[0], int):
            if int(download_result[0] / 100) == 2:
              is_successful = True

          if is_successful:
            self.bundle.log(message="download successful", url=absolute_url, file=filename)
            self.bundle.resources[resource_id] = "resources/%s" % resource_id
            element.attrs[attr] = "resources/%s" % resource_id
          else:
            # returning False means it didn't download so we make the url absolute.
            self.bundle.log(message="did not download", url=absolute_url, file=filename)
            element.attrs[attr] = absolute_url
      else:
        # if we're not downloading files we still need to do some cleanup.
        #  - move referenced attachments into the resources/ folder.
        #  - make urls absolute.

        # if it's a local html file and the src is relative,
        # add the attachment as a resource and update the url.
        if _is_local(self.url) and _is_local(url):
          # if self.url is:       /Users/rmiller/export/something.html
          # and url is:           images/bullet.gif
          # then absolute_url is: /Users/rmiller/export/images/bullet.gif
          # and filename is:      /tmp/{job_id}/resources/{hash}.gif
          filename = self.bundle.RESOURCE_PATH % (self.bundle.id, resource_id)
          if copy_file(absolute_url, filename):
            self.bundle.resources[resource_id] = "resources/%s" % resource_id
            element.attrs[attr] = "resources/%s" % resource_id
          else:
            # the element could be a link or an image.
            # if it's a link we unwrap its text, if it's an image we just remove it.
            self.bundle.log(message="resource doesn't exist", file=filename)
            if attr == "href":
              element.unwrap()
            else:
              element.decompose()
        elif _is_local(url):
          # this means self.url is _not_ local but the url is, so make it absolute.
          element.attrs[attr] = absolute_url
        # add protocols to image urls that are lacking them.
        # i'm pretty sure this is required but i forget why.
        elif url.startswith("//"):
          element.attrs[attr] = "https:" + url
  
      # we want to return True if the value changed.
      if element.attrs and element.attrs[attr] != initial_value:
        url_map[initial_value] = element.attrs[attr]
    
    # images and iframes can both have src attributes that might reference files we need
    # to download or we may need to adjust ther urls (e.g. make them absolute).
    for el in doc.select("[src]"):
      check_element(el, "src")
    
    # look for links to files that need to be downloaded.
    # also convert doc-to-doc links to be card-to-card.
    for link in doc.select("a[href]"):
      href = link.attrs.get("href", "")
      if not href:
        continue

      check_as_attachment = True
      absolute_url = urljoin(self.url, href)

      for other_node in self.bundle.nodes:
        if other_node.removed:
          continue
        if (compare_links and compare_links(other_node, absolute_url)) or \
            other_node.url == absolute_url or \
            (other_node.alt_urls and absolute_url in other_node.alt_urls):
          if other_node.type == FOLDER:
            link.attrs["href"] = "folders/%s" % other_node.id
          elif other_node.type == CARD:
            link.attrs["href"] = "cards/%s" % other_node.id
          check_as_attachment = False
          break

      # find links to local files and add these files as resources.
      if check_as_attachment:
        check_element(link, "href")
      
    self.content = str(doc)

  def write_files(self):
    """
    internal:
    Writes the files needed for this object. For cards that's a .yaml
    and .html file. For Folders it's just a .yaml file.
    """
    if self.removed:
      return
    if self.type == CARD:
        write_file(self.bundle.CARD_YAML_PATH % (self.bundle.id, _id_to_filename(self.id)), self.make_yaml())
        write_file(self.bundle.CARD_HTML_PATH % (self.bundle.id, _id_to_filename(self.id)), self.content.strip() or "")
    elif self.type == FOLDER:
        write_file(self.bundle.FOLDER_YAML_PATH % (self.bundle.id, _id_to_filename(self.id)), self.make_yaml())

  def make_yaml(self):
    """internal: Generates the yaml content for this node."""
    """Generates the YAML content for this node."""
    if self.removed:
        return ""
    if self.type == CARD:
        data = {
            "Title": self.title.replace("<", "<\u200E"),
            "ExternalId": self.id
        }
        if self.url:
            data["ExternalUrl"] = self.url
        if self.tags:
            data["Tags"] = self.tags
        return to_yaml(data)
    elif self.type == FOLDER:
        data = {
            "Title": self.title,
            "ExternalId": self.id,
            "Items": self.__make_items_list()
        }
        if self.url:
            data["ExternalUrl"] = self.url
        if self.desc:
            data["Description"] = self.desc

        return to_yaml(data)

class Bundle:
  """
  The `Bundle` object has methods you can use to build a bundle to import
  or sync into Guru. The main `Guru` object is used to create a bundle:

  ```
  import guru
  g = guru.Guru()
  bundle = g.bundle()
  ```

  Then you can use the `bundle` instance to add nodes and upload the content
  to Guru:

  ```
  bundle.node(title="New Card", content="this card was imported")
  bundle.zip()
  bundle.upload(collection="Import Test")
  ```

  That'll create a bundle with one card and upload it to the collection
  called "Import Test" -- if that collection doesn't exist, it'll be created.
  """
  def __init__(self, guru, id="", clear=False, folder="/tmp/", verbose=False, skip_empty_folders=False):
    self.guru = guru
    self.id = slugify(id) if id else str(int(time.time()))
    self.nodes = []
    self.resources = {}
    self.verbose = verbose
    self.skip_empty_folders = skip_empty_folders
    self.events = []
    self.start_time = time.time()
    self.CONTENT_PATH = folder + "%s"
    self.ZIP_PATH = folder + "collection_%s.zip"
    self.CARD_PREVIEW_PATH = folder + "%s/index.html"
    self.CSV_PATH = folder + "%s/log.csv"
    self.CARD_YAML_PATH = folder + "%s/cards/%s.yaml"
    self.CARD_HTML_PATH = folder + "%s/cards/%s.html"
    self.FOLDER_YAML_PATH = folder + "%s/folders/%s.yaml"
    self.COLLECTION_YAML_PATH = folder + "%s/collection.yaml"
    self.RESOURCE_PATH = folder + "%s/resources/%s"

    if clear:
        clear_dir(self.CONTENT_PATH % self.id)
  
  def log(self, **kwargs):
    kwargs["time"] = time.time() - self.start_time
    self.events.append(kwargs)
    if self.verbose:
      print(kwargs)

  def __write_csv(self):
    """internal"""
    labels = []
    for event in self.events:
      for key in event:
        if key not in labels:
          labels.append(key)

    with open(self.CSV_PATH % self.id, "w") as file_out:
      csv_out = csv.writer(file_out)
      csv_out.writerow(labels)
      for event in self.events:
        row = []
        for key in labels:
          if key in event:
            row.append(event[key])
          else:
            row.append("")
        csv_out.writerow(row)

  def has_node(self, id):
    for n in self.nodes:
      if n.id == id:
        return True
    return False
  
  def remove_node(self, node):
    node.detach()
    if node in self.nodes:
      self.nodes.remove(node)

  def url_to_id(self, url):
    return _url_to_id(url, False)

  def node(self, id="", url="", title="", content="", desc="", tags=None, alt_urls=None, index=None, node_type=None, clean_html=True):
    """
    This method makes a node or updates one. Nodes may have content but some
    may just have titles -- nodes with just titles can be used to group the
    nodes that do contain content.

    Nodes need either an ID or a URL. If you're loading data from your database
    or from an API, you might easily have IDs for each node. If you're scraping
    pages from a website you may not have IDs but you can use the URL -- we'll
    hash the URL and use that as the ID.

    Based on how you load and process data you may identify a node before you
    have all of its info. Say you load a page and it has links to its children,
    you'll know the URL and title of the children before you know what their
    content is. You can call bundle.node() to create them and establish the
    parent/child relationship, then call bundle.node() again later to set the
    child node's content.
    """
    id = str(id)
    if url and not id:
      id = _url_to_id(url, False)
    elif id:
      # some characters aren't allowed in IDs, like `/`
      id = id.replace("/", "_")
    
    node = None
    for n in self.nodes:
      if n.id == id:
        node = n
        break
    
    if title:
      title = str(title).strip()
      if len(title) > 200:
        title = f"{title[0:197]}..."

    if not node:
      node = BundleNode(id, bundle=self, title=title, desc=desc, content=content, tags=tags, alt_urls=alt_urls, index=index, node_type=node_type)
      self.nodes.append(node)
    
    if url:
      node.url = url
    if title:
      node.title = title
    if content:
      if clean_html:
        node.content = clean_up_html(content)
      else:
        node.content = content
    if node_type:
      node.type = node_type
    if tags:
      node.tags = tags
    if alt_urls:
      node.alt_urls = alt_urls
    if index is not None:
      node.index = index
    
    return node
  
  def print_tree(self, print_func=None):
    """Prints the bundle's hierarchy."""
    if print_func:
        traverse_tree(self, print_func)
    else:
        traverse_tree(self, print_node)

  def __wait_and_retry(self, status_code, wait):
    """internal"""
    if status_code == 429:
      # todo: use the response headers to check if they tell us how long to wait.
      self.log(message="got a 429 response", status_code=status_code, wait=wait)
      time.sleep(wait)
      return True

  def load_html(self, url, cache=False, make_links_absolute=True, headers=None, wait=5, timeout=0):
    """
    Makes an HTTP get call to load a URL, parse its content as HTML, and return a Beautiful
    Soup document object representing it.

    You can do this yourself using the `requests` and `bs4` modules directly but if you do it
    through the bundle object then it automatically logs this call and its response to its .csv
    log file. It's also easily cacheable so if your scripts can run faster by storing the HTTP
    responses to disk so subsequent runs can use the cached data.
    """
    # todo: figure out if we should log the headers. these could be helpful to have later
    #       but they could also contain an API key or other sensitive data.
    self.log(message="calling load_html", url=url, cache=cache, make_links_absolute=make_links_absolute)
    while True:
      doc, status_code = load_html(url, cache, make_links_absolute, headers)
      self.log(message="load_html response", url=url, status_code=status_code)

      if self.__wait_and_retry(status_code, wait):
        # todo: check if we've timed out.
        continue
      else:
        return doc

  def http_get(self, url, cache=False, headers=None, wait=5, timeout=0):
    """
    Makes an HTTP get call to load the specified URL and returns its response content as a string.

    You can do this yourself using the `requests` module directly but if you do it
    through the bundle object then it automatically logs this call and its response to its .csv
    log file. It's also easily cacheable so if your scripts can run faster by storing the HTTP
    responses to disk so subsequent runs can use the cached data.
    """
    self.log(message="calling http_get", url=url, cache=cache, timeout=timeout)

    while True:
      content, status_code = http_get(url, cache, headers)
      self.log(message="http_get response", url=url, status_code=status_code)

      if self.__wait_and_retry(status_code, wait):
        # todo: check if we've timed out.
        continue
      else:
        return content

  def http_post(self, url, data=None, cache=False, headers=None, wait=5, timeout=0):
    """
    Makes an HTTP post call to the specified URL and returns the response content as a string.

    You can do this yourself using the `requests` module directly but if you do it
    through the bundle object then it automatically logs this call and its response to its .csv
    log file. It's also easily cacheable so if your scripts can run faster by storing the HTTP
    responses to disk so subsequent runs can use the cached data.
    """
    self.log(message="calling http_post", url=url, cache=cache, timeout=timeout)
    while True:
      content, status_code = http_post(url, data, cache, headers)
      self.log(message="http_post response", url=url, status_code=status_code)

      if self.__wait_and_retry(status_code, wait):
        # todo: check if we've timed out.
        continue
      else:
        return content

  def download_file(self, url, filename, headers=None, cache=False, wait=5, timeout=0):
    """
    Makes an HTTP get call to load a remote file and save it to a local file.

    You can do this yourself using the `requests` module directly but if you do it
    through the bundle object then it automatically logs this call and its response to its .csv
    log file.
    """
    # todo: make this have a 'cache' parameter.
    self.log(message="calling download_file", url=url, filename=filename)

    while True:
      status_code, file_size = download_file(url, filename, headers, cache=cache)
      self.log(message="download_file response", url=url, filename=filename, status_code=status_code, file_size=file_size)

      if self.__wait_and_retry(status_code, wait):
        # todo: check if we've timed out.
        continue
      else:
        return status_code, file_size

  """
  def download_resource(self, url, headers=None):
    resource_id = _url_to_id(url)
    filename = self.RESOURCE_PATH % (self.id, resource_id)
    download_file(url, filename, headers=headers)
    self.resources[resource_id] = filename
    return "resources/%s" % resource_id

  def get_resource_path(self, url):
    id = _url_to_id(url)
    return self.RESOURCE_PATH % (self.id, id)
  
  def add_resource(self, filename):
    filename = filename.split("?")[0]
    resource_id = _url_to_id(filename)
    resource_filename = self.RESOURCE_PATH % (self.id, resource_id)
    self.resources[resource_id] = filename
    return "resources/%s" % resource_id
  """

  def __make_collection_yaml(self):
    """internal"""
    items = []
    tags = []
    for node in self.nodes:
      if node.removed:
          continue
      if node.type == FOLDER and not node.parents:
          items.append({
            "ID": node.id,
            "Type": "folder",
            "Title": node.title
          })
      elif node.type == CARD:
        if node.tags:
          for tag in node.tags:
            if tag not in tags:
              tags.append(tag)
    
    data = {
      "Version": 2,
      "Title": "Collection Title",
      "Items": items,
      "Tags": tags
    }

    return to_yaml(data)

  def zip(self, download_func=None, compare_links=None, clean_html=True):
    """
    This wraps up the sync process. Calling this lets us know you're
    done adding content so we can do these things:

    1. Assign guru types (folder, card) to each node.
    2. Create extra nodes as needed (e.g. to have the content that's associated with a folder node)
    3. Clean up link/image URLs and download resources.
    4. Write the .html and .yaml files.
    5. Make a .zip archive with all the content.
    """

    # todo: sort all nodes children by their 'index'.
    self.nodes.sort(key=lambda node: node.index)
    for node in self.nodes:
      node.children.sort(key=lambda id: self.node(id).index)

    # these are done as tree traversals so we have the parent/child
    # relationship and node depth as parameters.
    traverse_tree(self, assign_types)
    traverse_tree(self, insert_nodes)

    # remove nodes that are cards and have no content.
    self.nodes = [node for node in self.nodes if not node.removed]

    # 'clean html' is a little bit of a misnomer here. when you create a node,
    # we check the html and remove unnecessary tags and attributes. the operation
    # we're doing here is really resolving image and file links.
    # these are done for all nodes, the tree structure doesn't matter.
    if clean_html:
      count = 0
      for node in self.nodes:
        count += 1
        self.log(message=f"post-processing node {count} / {len(self.nodes)}", node=node.id)
        node.html_cleanup(
          download_func=download_func,
          compare_links=compare_links
        )

    for node in self.nodes:
      node.write_files()
    
    # write the collection.yaml file.
    write_file(self.COLLECTION_YAML_PATH % self.id, self.__make_collection_yaml())

    # make sure local files are all inside the /tmp/x/resources folder.
    for res_id, res_path in self.resources.items():
      if not res_path.startswith(self.CONTENT_PATH % self.id):
          self.log(message="add local file to resources", file=res_path, resource=res_id)
          copy_file(res_path, self.RESOURCE_PATH % (self.id, res_id))

    # build the zip file.
    zip_path = self.ZIP_PATH % self.id
    zip_file = zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, allowZip64=True)
    content_path = self.CONTENT_PATH % self.id
    for root, dirs, files in os.walk(content_path):
      for file in files:
        if not file.startswith("."):
          src_path = os.path.join(root, file)
          dest_path = os.path.relpath(src_path, content_path)
          self.log(message="add file to zip", file=file, zip_path=dest_path)
          zip_file.write(src_path, dest_path)

    zip_file.close()
    self.__write_csv()

  def upload(self, is_sync=False, name="", color="", desc="", collection_id=""):
    """
    Uploads the zip file you generated to Guru.

    This can either be done as a sync or import. Syncs update the content
    of an entire collection. Imports add content to a collection.

    The `name` parameter is the name of the collection to add this to. If
    there's not a collection matching that name it'll create one and you can
    provide the color and description to use for this new collection. You
    can also pass a collection_id instead of a name if you happen to know it.
    """
    if name and not collection_id:
      # get the team's list of collections and find the one matching this name.
      collection = self.guru.get_collection(name)
      collection_id = collection.id if collection else ""
      
      # if no match is found, make the collection.
      if not collection_id:
        collection_id = self.guru.make_collection(name, desc, color, is_sync).id
      else:
        # todo: make the PUT call to make sure the name, color, and desc are set correctly.
        pass
    
    if not collection_id:
      raise BaseException("collection_id is required")
    
    return self.guru.upload_content(
      collection=collection_id,
      filename="collection_%s.zip" % self.id,
      zip_path=self.ZIP_PATH % self.id,
      is_sync=is_sync
    )
  
  def build_spreadsheet(self):
    """internal"""
    rows = []
    traverse_tree(self, make_spreadsheet, rows=rows)

    # after the traversal, rows is a list of lists. we have to convert:
    # - the values to strings.
    # - the values to tab-delimited rows.
    # - the rows to be newline-delimited.
    return "\n".join([
      "\t".join([
        str(value).replace("`", "").replace("${", "\\${") for value in row
      ]) for row in rows
    ])

  def view_in_browser(self, open_browser=True):
    """
    This generates an HTML page that shows the .html files in an iframe
    so you can visualize the content structure and preview the HTML.
    """
    html_pieces = []
    traverse_tree(self, make_html_tree, html_pieces=html_pieces)

    spreadsheet = self.build_spreadsheet()
    html = """<!doctype html>
<html>
  <head>
    <style>

      body {
        display: flex;
        flex-direction: row;
        margin: 0;
        position: fixed;
        left: 0;
        right: 0;
        top: 0;
        bottom: 0;
        font-family: arial, sans-serif;
        font-size: 12px;
        background: #f7f8fa;
      }

      #tree {
        padding: 10px;
        height: calc(100%% - 70px);
        overflow: auto;
        box-sizing: border-box;
        max-width: 400px;
      }
      #tree > * {
        display: block;
        padding: 2px;
      }

      /* this covers depth=3 or higher. */
      [data-depth] { margin-left: 45px; }

      [data-depth="0"] { margin-left: 0px; }
      [data-depth="1"] { margin-left: 15px; }
      [data-depth="2"] { margin-left: 30px; }

      iframe {
        flex-grow: 1;
        max-width: 734px;
        margin: 20px;
        box-shadow: rgba(0, 0, 0, 0.15) 0 3px 10px;
        padding: 20px 60px;
        border: 1px solid #ccc;
        border-radius: 5px;
        background: #fff;
      }

      a, a:visited {
        display: block;
        color: #44f;
        text-decoration: none;
      }
      a:hover {
        background: #eef;
      }
      a.selected {
        background: #44f;
        color: #fff;
      }

      #copy-spreadsheet {
        border: 0;
        outline: 0;
        background: #44f;
        color: #fff;
        font-weight: bold;
        padding: 8px 12px;
        position: fixed;
        left: 20px;
        bottom: 20px;
        cursor: pointer;
      }

    </style>
  </head>
  <body>
    <div id="tree">%s</div>
    <button id="copy-spreadsheet">Copy Spreadsheet</button>
    <iframe name="iframe" src=""></iframe>
    <iframe id="source" style="display: none" src=""></iframe>
    <script>

      var sourceIframe = document.getElementById("source");
      var links = document.querySelectorAll("#tree a");
      var currentIndex = -1;

      links.forEach(function(link, index) {
        link.onclick = function() {
          links[currentIndex].classList.remove("selected");
          currentIndex = index;
          link.classList.add("selected");

          var originalUrl = link.getAttribute("data-original-url");
          if (originalUrl) {
            sourceIframe.src = originalUrl.startsWith("/") ? "file://" + originalUrl : originalUrl;
            sourceIframe.style.display = "block";
          } else {
            sourceIframe.style.display = "none";
          }
        }
      });
      function next() {
        if (links[currentIndex]) {
          links[currentIndex].classList.remove("selected");
        }
        currentIndex = (currentIndex + 1) %% links.length;
        links[currentIndex].classList.add("selected");
        links[currentIndex].click();
      }
      function prev() {
        if (links[currentIndex]) {
          links[currentIndex].classList.remove("selected");
        }
        currentIndex = (currentIndex - 1 + links.length) %% links.length;
        links[currentIndex].classList.add("selected");
        links[currentIndex].click();
      }

      document.onkeydown = function(event) {
        if (event.keyCode == 38) {
          prev();
          event.preventDefault();
        } else if (event.keyCode == 40) {
          next();
          event.preventDefault();
        }
      };
      next();

      var spreadsheet = `%s`;
      var copyButton = document.getElementById("copy-spreadsheet");
      var copyTimeout;
      copyButton.onclick = function() {
        var textarea = document.createElement("textarea");
        textarea.value = spreadsheet;

        // avoid scrolling to bottom.
        textarea.style.top = "0";
        textarea.style.left = "0";
        textarea.style.position = "fixed";

        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();

        var successful = false;
        try {
            successful = document.execCommand("copy");
        } catch (err) {
        }

        document.body.removeChild(textarea);

        copyButton.innerHTML = "Spreadsheet Copied!";
        if (copyTimeout) {
          clearTimeout(copyTimeout);
        }
        copyTimeout = setTimeout(function() {
          copyButton.innerHTML = "Copy Spreadsheet";
        }, 1500);
      };

      if (!spreadsheet) {
        copyButton.style.display = "none";
      }

    </script>
  </body>
</html>
""" % ("".join(html_pieces), spreadsheet)

    write_file(self.CARD_PREVIEW_PATH % self.id, html)
    if open_browser:
      webbrowser.open_new_tab("file://" + self.CARD_PREVIEW_PATH % self.id)
