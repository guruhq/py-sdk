
import guru

def get_article_content(url):
  doc = guru.load_html(url)
  return str(doc.select(".help-articles")[0])

def do_mid_level(sync, url, parent_node):
  doc = guru.load_html(url)
  category_links = doc.select(".help-products > a")

  for link in category_links:
    category_url = link.attrs.get("href")
    category_title = link.select(".ux-pivot-title")[0].text

    category_node = sync.node(url=category_url, title=category_title)
    parent_node.add_child(category_node)

    article_links = link.find_next_sibling("div").select("a")

    for article_link in article_links:
      article_url = article_link.attrs.get("href")
      article_title = article_link.text
      article_content = get_article_content(article_url)
      article_node = sync.node(url=article_url, title=article_title, content=article_content)
      category_node.add_child(article_node)

def do_top_level():
  g = guru.Guru()
  sync = g.sync("godaddy")

  doc = guru.load_html("https://www.godaddy.com/help")
  links = doc.select("#more-help-product-all a")[0:3]

  for link in links:
    url = link.attrs.get("href")
    node = sync.node(url=url, title=link.text)
    do_mid_level(sync, url, node)
  
  sync.zip()
  sync.print_tree()
  sync.view_in_browser()

if __name__ == "__main__":
  do_top_level()
