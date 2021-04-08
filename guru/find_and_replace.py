import re
import webbrowser
from guru.util import write_file, load_html
from guru.data_objects import Card

from bs4 import BeautifulSoup

def replace_text_in_text(text, term, replacement, case_sensitive=False):
  # replacement = "[start]Customer[end]".capitalize()
  original_text = text
  lowercased_term = term.lower()
  lowercased_replacement = replacement.lower().replace("[guru_sdk_highlight_start]", "[GURU_SDK_HIGHLIGHT_START]").replace("[guru_sdk_highlight_end]", "[GURU_SDK_HIGHLIGHT_END]")
  uppercased_term = term.upper()
  uppercased_replacement = replacement.upper()
  capitalized_term = term.capitalize()
  if "[GURU_SDK_HIGHLIGHT_START]" in replacement and "[GURU_SDK_HIGHLIGHT_END]" in replacement:
    replacement = replacement.replace("[GURU_SDK_HIGHLIGHT_END]", "")
    replacement = replacement.replace("[GURU_SDK_HIGHLIGHT_START]", "")
    capitalized_replacement = "[GURU_SDK_HIGHLIGHT_START]" + replacement.capitalize() + "[GURU_SDK_HIGHLIGHT_END]"
  elif "[GURU_SDK_HIGHLIGHT_END]" in replacement:
    replacement = replacement.replace("[GURU_SDK_HIGHLIGHT_END]", "")
    capitalized_replacement = "[GURU_SDK_HIGHLIGHT_END]" + replacement.capitalize()
  elif "[GURU_SDK_HIGHLIGHT_START]" in replacement:
    replacement = replacement.replace("[GURU_SDK_HIGHLIGHT_START]", "")
    capitalized_replacement = "[GURU_SDK_HIGHLIGHT_START]" + replacement.capitalize()
  else:
    capitalized_replacement = replacement.capitalize()
  if case_sensitive:
    text = text.replace(term, replacement)
    print(case_sensitive, term, replacement)
  else:
    text = text.replace(lowercased_term, lowercased_replacement).replace(uppercased_term, uppercased_replacement).replace(capitalized_term, capitalized_replacement)
  
  return text

def replace_text_in_html(html, term, replacement, case_sensitive=False):
  doc = html if isinstance(html, BeautifulSoup) else BeautifulSoup(html, "html.parser")
  pattern = re.compile(r'%s' % term, re.IGNORECASE)
  text_nodes = doc.find_all(text=pattern)
  for text_node in text_nodes:
    text_node.replace_with(replace_text_in_text(
      text_node, term, replacement, case_sensitive
    ))
  return str(doc)

def replace_text_in_card(card, term, replacement, replace_title=True, highlight=False, case_sensitive=False):
  if isinstance(card, Card):
    if replace_title:
      card.title = replace_text_in_text(card.title, term, replacement)
    if highlight:
      card.content = replace_text_in_html(card.content, term, "[GURU_SDK_HIGHLIGHT_START]%s[GURU_SDK_HIGHLIGHT_END]" % replacement)
      # do string replacements on the [start] and [end] tokens.
      card.content = replace_text_in_html(card.content, "[GURU_SDK_HIGHLIGHT_START]", '<span class="sdk-highlight">', case_sensitive=True)
      card.content = replace_text_in_html(card.content, "[GURU_SDK_HIGHLIGHT_END]", "</span>", case_sensitive=True)
    else:
      card.content = replace_text_in_html(card.content, term, replacement)
    return card.content
  else:
    if highlight:
      card = replace_text_in_html(card, term, "[GURU_SDK_HIGHLIGHT_START]%s[GURU_SDK_HIGHLIGHT_END]" % replacement)
      # do string replacements on the [start] and [end] tokens.
      card = replace_text_in_text(str(card), "[GURU_SDK_HIGHLIGHT_START]", '<span class="sdk-highlight">', case_sensitive=True)
      card = replace_text_in_text(str(card), "[GURU_SDK_HIGHLIGHT_END]", "</span>", case_sensitive=True)
    else:
      card = replace_text_in_html(card, term, replacement)
    return card
class PreviewData:
  def __init__(self, card, orig_content, new_content):
    self.card_id = card.id
    self.title = card.title
    self.orig_content = orig_content
    self.new_content = new_content

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
        color: rgba(0, 0, 0, 0.6)
      }

      .sdk-highlight {
        background-color: #4a7; 
        color: #fff;
      }
      </style>
      """

      

      write_file(orig_filepath, content_data.orig_content)
      write_file(new_filepath, content_data.new_content)
      
      # orig_content_html = load_html(orig_filepath, make_links_absolute=False)
      # orig_content_html = replace_text_in_card(orig_content_html, self.term, self.term, replace_title=False, highlight=True)
      # write_file(orig_filepath, highlight_css + str(orig_content_html))
      
      new_content_html = load_html(new_filepath, make_links_absolute=False)
      new_content_html = replace_text_in_card(new_content_html, self.replacement, self.replacement, replace_title=False, highlight=True)
      write_file(new_filepath, highlight_css + str(new_content_html))
      
      self.html_pieces.append(
        '<a href="%s" data-original-url="%s" target="iframe">%s</a>' % (new_filepath, orig_filepath, content_data.title)
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

