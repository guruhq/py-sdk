
import guru

def page_to_cards(url, sync, parent_node):
  # this loads a page and breaks its sections into cards.
  doc = guru.load_html(url)
  elements = doc.select(".md-page > *")

  content = ""
  title = ""
  external_url = ""
  for element in elements:
    if element.name == "h1" or element.name == "h2" or element.name == "h3":
      # the right column has a heading that says "on this page" and we want to skip that.
      if element.text.strip().lower() == "on this page":
        continue
      
      # if we have content and a title when we see a heading that means it's not the
      # first heading so we should make a card for the previous section we saw.
      if content and title:
        sync.node(content=content, title=title, url=external_url).add_to(parent_node)
        
      content = ""
      title = element.text
      external_url = url + "#" + element.attrs.get("id")
    else:
      content += str(element)
  
  if content and title:
    sync.node(content=content, title=title, url=external_url).add_to(parent_node)

def get_gitlab_boards():
  # this reads the gitlab handbook page and figures out what container nodes
  # exist then calls page_to_cards to generate the cards for each page.
  doc = guru.load_html("https://about.gitlab.com/handbook/")

  page_links = doc.select("li a")

  g = guru.Guru()
  sync = g.sync("gitlab_handbook")

  for page_link in page_links:
    url = page_link.attrs.get("href") or ""
    if "changelog" in url.lower():
      continue
    
    # for each <li> in the list, find the parent LIs which'll tell us
    # what board group/board each set of cards will go in.
    lis = page_link.find_parents("li")
    links = [li.select("a")[0] for li in lis]
    links.reverse()

    parent_node = None
    for i in range(0, len(links)):
      # make sure we have a node for each part of the hierarchy.
      # for nodes 1..n establish the parent-child relationship.
      parent_node = sync.node(url=links[i].attrs["href"], title=links[i].text)
      if i > 0:
        sync.node(url=links[i - 1].attrs["href"]).add_child(parent_node)
    
    page_to_cards(url, sync, parent_node)
  
  sync.zip()
  sync.print_tree()
  sync.view_in_browser()
  # sync.upload(name="Gitlab Handbook Import v2", color="#ffffff")


if __name__ == "__main__":
  get_gitlab_boards()
