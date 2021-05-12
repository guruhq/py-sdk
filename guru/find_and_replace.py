import re
import webbrowser
from guru.util import write_file, load_html
from guru.data_objects import Card

from urllib.parse import quote, unquote
from bs4 import BeautifulSoup

def get_term_count(text, term):
  """
  Returns count of all occurrences of term in the text

  Args:
    text (str): text to search
    term (str): term to find
  
  Returns: count (number) of all occurrences of term in the text

  """
  doc = BeautifulSoup(text, "html.parser")
  lowered_doc = doc.text.lower()
  return lowered_doc.count(term.lower())

def replace_text_in_text(text, term, replacement, term_case_sensitive=False, replacement_case_sensitive=False):
  """
  Replaces term in text (string). Accounts for lowercase, uppercase, capitalized, and title-cased

  Arguments:
    text (str): text that contains the term we want to replace,
    term (str): term we want to replace,
    replacement (str): replacement term,
    term_case_sensitive (bool): boolean for searching for the specific term or case-insensitive (defaults to false ),
    replacement_case_sensitive (bool): boolean for replacement term case-sensitivity (defaults to false)

  Returns: text (str) with replacement
  """
  # replacement = "[start]Customer[end]".capitalize()
  lowercased_term = term.lower()
  lowercased_replacement = replacement.lower().replace("[guru_sdk_highlight_start]", "[GURU_SDK_HIGHLIGHT_START]")
  lowercased_replacement = lowercased_replacement.replace("[guru_sdk_highlight_end]", "[GURU_SDK_HIGHLIGHT_END]")
  uppercased_term = term.upper()
  uppercased_replacement = replacement.upper()
  capitalized_term = term.capitalize()
  titlecased_term = term.title()
  if "[GURU_SDK_HIGHLIGHT_START]" in replacement and "[GURU_SDK_HIGHLIGHT_END]" in replacement:
    replacement = replacement.replace("[GURU_SDK_HIGHLIGHT_END]", "")
    replacement = replacement.replace("[GURU_SDK_HIGHLIGHT_START]", "")
    capitalized_replacement = "[GURU_SDK_HIGHLIGHT_START]" + replacement.capitalize() + "[GURU_SDK_HIGHLIGHT_END]"
    titlecased_replacement = "[GURU_SDK_HIGHLIGHT_START]" + replacement.title() + "[GURU_SDK_HIGHLIGHT_END]"
  elif "[GURU_SDK_HIGHLIGHT_END]" in replacement:
    replacement = replacement.replace("[GURU_SDK_HIGHLIGHT_END]", "")
    capitalized_replacement = "[GURU_SDK_HIGHLIGHT_END]" + replacement.capitalize()
    titlecased_replacement = "[GURU_SDK_HIGHLIGHT_END]" + replacement.title()
  elif "[GURU_SDK_HIGHLIGHT_START]" in replacement:
    replacement = replacement.replace("[GURU_SDK_HIGHLIGHT_START]", "")
    capitalized_replacement = "[GURU_SDK_HIGHLIGHT_START]" + replacement.capitalize()
    titlecased_replacement = "[GURU_SDK_HIGHLIGHT_START]" + replacement.title()
  else:
    capitalized_replacement = replacement.capitalize()
    titlecased_replacement = replacement.title()
  
  if term_case_sensitive:
    text = text.replace(term, replacement)
  elif not term_case_sensitive and replacement_case_sensitive:
    text = text.replace(lowercased_term, replacement)
    text = text.replace(uppercased_term, replacement)
    text = text.replace(capitalized_term, replacement)
    if not capitalized_term == titlecased_term:
      text = text.replace(titlecased_term, replacement)
  else:
    text = text.replace(lowercased_term, lowercased_replacement)
    text = text.replace(uppercased_term, uppercased_replacement)
    text = text.replace(capitalized_term, capitalized_replacement)
    if not capitalized_term == titlecased_term:
      text = text.replace(titlecased_term, titlecased_replacement)

  return text

def replace_in_markdown_block(doc, term, replacement, replacement_case_sensitive=False):
  """
  Replace text in markdown blocks (markdown content in data-ghq-card-content-markdown-content attribute)

  Args:
    doc (BeautifulSoup): html document object
    term (str): term to replace
    replacement (str): replacement term
    replacement_case_sensitive (bool): boolean for replacement term case-sensitivity (defaults to false)
  """
  for markdown_div in doc.select("[data-ghq-card-content-markdown-content]"):
    md = unquote(markdown_div.attrs.get("data-ghq-card-content-markdown-content"))
    new_md = replace_text_in_text(md, term, replacement, replacement_case_sensitive=replacement_case_sensitive)
    markdown_div.attrs["data-ghq-card-content-markdown-content"] = quote(new_md)

def replace_text_in_html(html, term, replacement, term_case_sensitive=False, replacement_case_sensitive=False, replace_html_attributes=False):
  """
  Replaces term in html (string). Accounts for lowercase, uppercase, capitalized, and title-cased

  Arguments:
    html (BeautifulSoup or str): card's html (converted to BeautifulSoup object if not already)
    term (str): term we want to replace,
    replacement (str): replacement term,
    term_case_sensitive (bool): boolean for searching for the specific term or case-insensitive (defaults to false ),
    replacement_case_sensitive (bool): boolean for replacement term case-sensitivity (defaults to false)
    replace_html_attributes (bool): determines whether to replace term in html attributes

  Returns: html (str) with replacement
  """
  doc = html if isinstance(html, BeautifulSoup) else BeautifulSoup(html, "html.parser")
  pattern = re.compile(r'%s' % re.escape(term), re.IGNORECASE)
  text_nodes = doc.find_all(text=term) if term_case_sensitive else doc.find_all(text=pattern)
  if replace_html_attributes:
    return replace_text_in_text(str(doc), term, replacement, replacement_case_sensitive=replacement_case_sensitive)
  else:
    for text_node in text_nodes:
      text_node.replace_with(replace_text_in_text(
        text_node, term, replacement, replacement_case_sensitive=replacement_case_sensitive
      ))
    replace_in_markdown_block(doc, term, replacement)
    return str(doc)

def add_highlight(card, term, highlight="replacement", case_sensitive=False):
  """
  Wraps term with a span element, with a highlight class

  example:
  ```
  add_highlight(card, "Trust score", case_sensitive=case_sensitive)
  ```

  Arguments:
    card (BeautifulSoup or str): card's html (converted to BeautifulSoup object if not already)
    term (str): term we want to replace
    highlight (str, either `original` or `replacement`): determines which highlight class the term will get (defaults to replacement)
    case_sensitive (bool): boolean, denoting whether the search term is case-insensitive or specific (defaults to false )

  Returns: html (str) with highlighted terms
  """
  
  highlight_class = None
  if highlight == "original":
    highlight_class = "sdk-orig-highlight"
  if highlight == "replacement":
    highlight_class = "sdk-replacement-highlight"

  card_content = card.content if isinstance(card, Card) else card

  content = replace_text_in_html(card_content, term, "[GURU_SDK_HIGHLIGHT_START]%s[GURU_SDK_HIGHLIGHT_END]" % term, term_case_sensitive=case_sensitive)
  
  # do string replacements on the [start] and [end] tokens.
  content = replace_text_in_text(str(content), "[GURU_SDK_HIGHLIGHT_START]", '<span class="%s">' % highlight_class, replacement_case_sensitive=True)
  content = replace_text_in_text(str(content), "[GURU_SDK_HIGHLIGHT_END]", "</span>", replacement_case_sensitive=True)
  return content

def replace_text_in_card(card, term, replacement, replace_title=True, replacement_highlight=False, orig_highlight=False, case_sensitive=False, replacement_case_sensitive=False, replace_html_attributes=False):
  """
  Replaces term in card content. Accounts for lowercase, uppercase, capitalized, and title-cased.
  Optional replacement of term in card title.
  Could also choose to add a highlight class to a term ( replacement term and/or original term ).

  Arguments:
    card (Card instance or str): Card instance or text string (i.e., card.content)
    term (str): term we want to replace,
    replacement (str): replacement term,
    replace_title (bool): boolean for replacing term in card title ( defaults to false )
    replacement_highlight (bool): determines whether to apply a highlight class to the replacement term (defaults to false)
    orig_highlight (bool): determines whether to apply a highlight class to the original term (defaults to false)
    case_sensitive (bool): boolean, denoting whether the search term is case-insensitive or specific (defaults to false )
    replace_html_attributes (bool): determines whether to replace term in html attributes

  Returns: html (str) with replacement
  """
  if isinstance(card, Card):
    content = card.content
    if replace_title:
      card.title = replace_text_in_text(card.title, term, replacement, term_case_sensitive=case_sensitive, replacement_case_sensitive=replacement_case_sensitive)
  else:
    content = card
  if replacement_highlight:
    content = add_highlight(content, replacement, case_sensitive=case_sensitive)
  elif orig_highlight:
    content = add_highlight(content, term, highlight="original", case_sensitive=case_sensitive)
  else:
    content = replace_text_in_html(content, term, replacement, term_case_sensitive=case_sensitive, replacement_case_sensitive=replacement_case_sensitive, replace_html_attributes=replace_html_attributes)
  if isinstance(card, Card):
    card.content = content
  return content
class PreviewData:
  """
  Class that holds a card's preview data.

  Args:
    card (Card instance): instance of `Card`
    term (str): term to replace
    replacement (str): replacement term
    orig_content (str): original card content
    new_content (str): new content, with replaced term
    
  Properties:
    replacement_term_count: returns a count of all occurrences of the replacement term in the card's text
    original_term_count: returns a count of all occurrences of the original term in the card's text

  """
  def __init__(self, card, term, replacement, orig_content, new_content):
    self.card_id = card.id
    self.title = card.title
    self.term = term
    self.replacement = replacement
    self.orig_content = orig_content
    self.new_content = new_content
    
  @property
  def replacement_term_count(self):
    return get_term_count(self.new_content, self.replacement)

  @property
  def original_term_count(self):
    return get_term_count(self.orig_content, self.term)

  @property
  def replacement_term_count_in_html(self):
    return self.new_content.lower().count(self.replacement)

  @property
  def original_term_count_in_html(self):
    return self.orig_content.lower().count(self.term)
class Preview:
  """
  Class that builds html tree and shows the find and replace preview in the browser.

  Args:
    content_list (list of Preview): List of preview data objects (Preview)
    term (str): term to replace
    replacement (str): replacement term
    folder (str): destination folder for preview files
    task_name (str): name to be included in preview file path ( i.e., /tmp/find_and_replace/new_content/new_1111.html )
    
  Methods:
    make_html_tree: builds the original content/new content link in the HTML preview page
    view_in_browser: generates preview HTML page and shows in browser

  """
  def __init__(self, content_list, term, replacement, folder="/tmp/", task_name=None):
    self.content_list = content_list
    self.term = term
    self.replacement = replacement
    self.task_name = task_name if task_name else "find_and_replace"
    self.orig_content_path = folder + "%s/old_content/orig_%s.html"
    self.new_content_path = folder + "%s/new_content/new_%s.html"
    self.card_preview_path = folder + "%s/index.html"
    self.html_pieces = []

  def make_html_tree(self):
    """This builds the original content/new content link in the HTML preview page."""
    for content_data in self.content_list:
      orig_filepath = self.orig_content_path % (self.task_name, content_data.card_id)
      new_filepath = self.new_content_path % (self.task_name, content_data.card_id)

      highlight_css = """
      <style>

      *,
      img,
      iframe {
        color: rgba(0, 0, 0, 0.3) !important;
      }
      .sdk-replacement-highlight {
        background-color: #4a7 !important; 
        color: #fff !important;
        filter: drop-shadow(6px 6px 4px #4444dd);
      }
      .sdk-orig-highlight {
        background-color: #E81456 !important; 
        color: #fff !important;
        filter: drop-shadow(6px 6px 4px #4444dd);
      }
      </style>
      """

      

      write_file(orig_filepath, content_data.orig_content)
      write_file(new_filepath, content_data.new_content)
      
      orig_content_html, orig_status = load_html(orig_filepath, make_links_absolute=False)

      orig_content_html = replace_text_in_card(orig_content_html, self.term, self.term, replace_title=False, orig_highlight=True)
      write_file(orig_filepath, highlight_css + str(orig_content_html))
      
      new_content_html, new_status = load_html(new_filepath, make_links_absolute=False)
      new_content_html = replace_text_in_card(new_content_html, self.replacement, self.replacement, replace_title=False, replacement_highlight=True)
      write_file(new_filepath, highlight_css + str(new_content_html))
      term_count = content_data.original_term_count
      replacement_count = content_data.replacement_term_count
      term_count_in_html = content_data.original_term_count_in_html
      replacement_count_in_html = content_data.replacement_term_count_in_html

      self.html_pieces.append(
        '<a href="%s" data-original-url="%s" target="iframe">%s (%s/%s)*(%s/%s)</a>' % (new_filepath, orig_filepath, content_data.title, replacement_count, term_count, replacement_count_in_html, term_count_in_html)
      )

  def view_in_browser(self, open_browser=True):
      """
      This generates an HTML page that shows the .html files in an iframe
      so you can visualize the content structure and preview the HTML.
      """

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
        

      </style>
    </head>
    <body>
      <div id="tree">%s</div>
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

      </script>
    </body>
  </html>
  """ % ("").join(self.html_pieces)

      write_file(self.card_preview_path % self.task_name, html)
      if open_browser:
        webbrowser.open_new_tab("file://" + self.card_preview_path % self.task_name)

class FindAndReplace:
  """
  Performs a find and replace over a given set of cards (all cards you can access, by default), and shows a preview of 
  the changes in the browser.

  ```
  import guru
  g = guru.Guru()

  term_to_replace = "Test"
  replace_with_term = "Quiz"
  task_name = "test_preview"

  find_and_replace = guru.FindAndReplace(g, term_to_replace, replace_with_term, replace_title=True, task_name=task_name)
  find_and_replace.run()
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
  Args:
    guru (Guru instance): instance of Guru module
    term (str): term to replace
    replacement (str): replacement term
    term_case_sensitive (bool): boolean for searching for the specific term or case-insensitive (defaults to false ),
    replacement_case_sensitive (bool): boolean for replacement term case-sensitivity (defaults to false)
    replace_title (bool): boolean for replacing term in card title ( defaults to false )
    replace_html_attributes (bool): determines whether to replace term in html attributes or not
    collection (str): Either a collection name or ID. If it's a name, it'll
        return the first matching collection and the comparison is not case
        sensitive.
    folder (str): destination folder for preview files
    task_name (str): name to be included in preview file path ( i.e., /tmp/find_and_replace/new_content/new_1111.html )
    
  Methods:
    run: Run a find and replace, with the parameters provided, and previews in the browser. 
    By default, this does a dry run, and doesn't post the changes to the card, 
    but setting `dry_run=False` will make a patch request, with the card changes.

  """
  def __init__(
    self, 
    guru, 
    term, 
    replacement, 
    term_case_sensitive=False, 
    replacement_case_sensitive=False, 
    replace_title=False, 
    replace_html_attributes=False, 
    collection=None, 
    folder="/tmp/", 
    task_name=None
  ):
    self.guru = guru
    self.term = term
    self.replacement = replacement
    self.term_case_sensitive = term_case_sensitive
    self.replacement_case_sensitive = replacement_case_sensitive
    self.replace_title = replace_title
    self.replace_attributes = replace_html_attributes
    self.collection = collection
    self.folder = folder
    self.task_name = task_name if task_name else "find_and_replace"
    self.cards = []

  def run(self, dry_run=True):
    """
    Performs a find and replace on the given cards, 
    and previews in the browser. Defaults to a dry run, 
    but setting `dry_run=False` will make a patch request, with the card changes.
    
    """
    for card in self.guru.find_cards(collection=self.collection):
      if card.has_text(self.term, case_sensitive=self.term_case_sensitive):
        
        original_content = card.content
        
        card.content = replace_text_in_card(
          card, 
          self.term, 
          self.replacement, 
          replace_title=self.replace_title, 
          replace_html_attributes=self.replace_attributes, 
          case_sensitive=self.term_case_sensitive,
          replacement_case_sensitive=self.replacement_case_sensitive
        )
        new_content =  card.content
        if not dry_run:
          card.patch()

        self.cards.append(PreviewData(
          card=card,
          term=self.term,
          replacement=self.replacement,
          orig_content=original_content,
          new_content=new_content
          
        ))

    browser_preview = Preview(
      content_list=self.cards, 
      term=self.term,
      replacement=self.replacement,
      folder=self.folder,
      task_name=self.task_name,
    )
    
    browser_preview.make_html_tree()

    browser_preview.view_in_browser()
