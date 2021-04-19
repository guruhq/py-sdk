import re
import webbrowser
from guru.util import write_file, load_html
from guru.data_objects import Card


from bs4 import BeautifulSoup

# for markdown_div in card.doc.select("[data-ghq-card-content-markdown-content]"):
#       md = unquote(markdown_div.attrs.get("data-ghq-card-content-markdown-content"))
#       html = markdown.markdown(md)
#       doc = BeautifulSoup(html, "html.parser")

def get_term_count(text, term):
  doc = BeautifulSoup(text, "html.parser")
  lowered_doc = doc.text.lower()
  return lowered_doc.count(term.lower())

def replace_text_in_text(text, term, replacement, term_case_sensitive=False, replacement_case_sensitive=False):
  # replacement = "[start]Customer[end]".capitalize()
  lowercased_term = term.lower()
  lowercased_replacement = replacement.lower().replace("[guru_sdk_highlight_start]", "[GURU_SDK_HIGHLIGHT_START]").replace("[guru_sdk_highlight_end]", "[GURU_SDK_HIGHLIGHT_END]")
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
    if not capitalized_term == titlecased_term:
      text = text.replace(lowercased_term, replacement).replace(uppercased_term, replacement).replace(titlecased_term, replacement).replace(capitalized_term, replacement)
    else:
      text = text.replace(lowercased_term, replacement).replace(uppercased_term, replacement).replace(capitalized_term, replacement)
  else:
    if not capitalized_term == titlecased_term:
      text = text.replace(lowercased_term, lowercased_replacement).replace(uppercased_term, uppercased_replacement).replace(titlecased_term, titlecased_replacement).replace(capitalized_term, capitalized_replacement)
    else:
      text = text.replace(lowercased_term, lowercased_replacement).replace(uppercased_term, uppercased_replacement).replace(capitalized_term, capitalized_replacement)
  
  return text

def replace_text_in_html(html, term, replacement, term_case_sensitive=False, replacement_case_sensitive=False):
  doc = html if isinstance(html, BeautifulSoup) else BeautifulSoup(html, "html.parser")
  pattern = re.compile(r'%s' % term, re.IGNORECASE)
  text_nodes = doc.find_all(text=pattern) if not term_case_sensitive else doc.find_all(text=term)
  for text_node in text_nodes:
    text_node.replace_with(replace_text_in_text(
      text_node, term, replacement, replacement_case_sensitive=replacement_case_sensitive
    ))
  return str(doc)

def add_highlight(card, term, replacement, highlight="replacement", case_sensitive=False):
  highlight_class = None
  if highlight == "original":
    highlight_class = "sdk-orig-highlight"
  if highlight == "replacement":
    highlight_class = "sdk-replacement-highlight"

  card_content = card.content if isinstance(card, Card) else card

  content = replace_text_in_html(card_content, term, "[GURU_SDK_HIGHLIGHT_START]%s[GURU_SDK_HIGHLIGHT_END]" % replacement, term_case_sensitive=case_sensitive)
  
  # do string replacements on the [start] and [end] tokens.
  content = replace_text_in_text(str(content), "[GURU_SDK_HIGHLIGHT_START]", '<span class="%s">' % highlight_class, replacement_case_sensitive=True)
  content = replace_text_in_text(str(content), "[GURU_SDK_HIGHLIGHT_END]", "</span>", replacement_case_sensitive=True)
  return content

def replace_text_in_card(card, term, replacement, replace_title=True, replacement_highlight=False, orig_highlight=False, case_sensitive=False):
  if isinstance(card, Card):
    if replace_title:
      card.title = replace_text_in_text(card.title, term, replacement, term_case_sensitive=case_sensitive)
    if replacement_highlight:
      card.content = add_highlight(card, term, replacement, case_sensitive=case_sensitive)
    elif orig_highlight:
      card.content = add_highlight(card, term, replacement, highlight="original", case_sensitive=case_sensitive)
    else:
      card.content = replace_text_in_html(card.content, term, replacement, term_case_sensitive=case_sensitive)
    return card.content
  else:
    if replacement_highlight:
      card = add_highlight(card, term, replacement, case_sensitive=case_sensitive)
    elif orig_highlight:
      card = add_highlight(card, term, replacement, highlight="original", case_sensitive=case_sensitive)
    else:
      card = replace_text_in_html(card, term, replacement, term_case_sensitive=case_sensitive)
    return card
class PreviewData:
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
class Preview:
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

      * {
        color: rgba(0, 0, 0, 0.3)
      }
      .sdk-replacement-highlight {
        background-color: #4a7; 
        color: #fff;
        filter: drop-shadow(6px 6px 4px #4444dd);
      }
      .sdk-orig-highlight {
        background-color: #E81456; 
        color: #fff;
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

      self.html_pieces.append(
        '<a href="%s" data-original-url="%s" target="iframe">%s (%s/%s)</a>' % (new_filepath, orig_filepath, content_data.title, replacement_count, term_count)
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

