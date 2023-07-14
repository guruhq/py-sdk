
import json
import yaml
import unittest
import responses

from unittest.mock import Mock

import guru

def use_guru(username="user@example.com", api_token="abcdabcd-abcd-abcd-abcd-abcdabcdabcd", silent=True, dry_run=False):
  def wrapper(func):
    def call_func(self):
      g = guru.Guru(username, api_token, silent=silent, dry_run=dry_run)
      func(self, g)
    return call_func
  return wrapper

def read_yaml(filename):
  with open(filename) as file_in:
    return yaml.load(file_in, Loader=yaml.FullLoader)

def read_html(filename):
  with open(filename) as file_in:
    return file_in.read()

class TestBundle(unittest.TestCase):
  @use_guru()
  def test_sync_with_two_nodes(self, g):
    sync = g.bundle("test_sync_with_two_nodes")

    # make two nodes, one with content, and add that one to the other.
    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1")
    node2 = sync.node(id="2", url="https://www.example.com/2", title="node 2", content="card content")
    node2.add_to(node1)
    sync.zip()

    self.assertEqual(read_yaml("/tmp/test_sync_with_two_nodes/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": [{
        "ID": "1",
        "Title": "node 1",
        "Type": "folder"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_two_nodes/folders/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Items": [{
        "ID": "2",
        "Type": "card"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_two_nodes/cards/2.yaml"), {
      "ExternalId": "2",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "node 2"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_two_nodes/cards/2.html"), "card content")

  @use_guru()
  def test_sync_where_the_child_has_no_content(self, g):
    sync = g.bundle("test_sync_where_the_child_has_no_content")

    # make two nodes, one with content, and add that one to the other.
    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1")
    node2 = sync.node(id="2", url="https://www.example.com/2", title="node 2")
    node2.add_to(node1)
    sync.zip(favor_sections=True)

    self.assertEqual(read_yaml("/tmp/test_sync_where_the_child_has_no_content/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": [{
        "ID": "1",
        "Title": "node 1",
        "Type": "folder"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_where_the_child_has_no_content/folders/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Items": [{
        "Title": "node 2",
        "Type": "section",
        "Items": []
      }]
    })
    # make sure cards/2.html and cards/2.yaml don't exist.
    with self.assertRaises(FileNotFoundError):
      read_html("/tmp/test_sync_where_the_child_has_no_content/cards/2.html")
    with self.assertRaises(FileNotFoundError):
      read_html("/tmp/test_sync_where_the_child_has_no_content/cards/2.yaml")

  @use_guru()
  def test_sync_with_html_in_card_title(self, g):
    sync = g.bundle("test_sync_with_html_in_card_title")

    # make one node with <a> in its title.
    node1 = sync.node(id="a", url="https://www.example.com/a", title="node <a>", content="card content")
    sync.zip()

    self.assertEqual(read_yaml("/tmp/test_sync_with_html_in_card_title/cards/a.yaml"), {
      "ExternalId": "a",
      "ExternalUrl": "https://www.example.com/a",
      "Title": "node <\u200Ea>"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_html_in_card_title/cards/a.html"), "card content")

  @use_guru()
  def test_sync_with_a_node_on_two_folders(self, g):
    sync = g.bundle("test_sync_with_a_node_on_two_folders")

    # make two nodes, one with content, and add that one to the other.
    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1")
    node2 = sync.node(id="2", url="https://www.example.com/2", title="node 2")
    node3 = sync.node(id="3", url="https://www.example.com/3", title="node 3", content="card content")
    node3.add_to(node1)
    node3.add_to(node2)
    sync.zip()

    self.assertEqual(read_yaml("/tmp/test_sync_with_a_node_on_two_folders/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": [{
        "ID": "1",
        "Title": "node 1",
        "Type": "folder"
      }, {
        "ID": "2",
        "Title": "node 2",
        "Type": "folder"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_a_node_on_two_folders/folders/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Items": [{
        "ID": "3",
        "Type": "card"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_a_node_on_two_folders/folders/2.yaml"), {
      "ExternalId": "2",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "node 2",
      "Items": [{
        "ID": "3",
        "Type": "card"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_a_node_on_two_folders/cards/3.yaml"), {
      "ExternalId": "3",
      "ExternalUrl": "https://www.example.com/3",
      "Title": "node 3"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_a_node_on_two_folders/cards/3.html"), "card content")

  @use_guru()
  def test_sync_move_to(self, g):
    sync = g.bundle("test_sync_move_to")

    # make two nodes, one with content, and add that one to the other.
    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1")
    node2 = sync.node(id="2", url="https://www.example.com/2", title="node 2")
    node3 = sync.node(id="3", url="https://www.example.com/3", title="node 3", content="card content")
    node3.add_to(node1)
    node3.move_to(node2)
    sync.zip()

    self.assertEqual(read_yaml("/tmp/test_sync_move_to/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": [{
        "ID": "1",
        "Title": "node 1",
        "Type": "folder"
      }, {
        "ID": "2",
        "Title": "node 2",
        "Type": "folder"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_move_to/folders/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Items": []
    })
    self.assertEqual(read_yaml("/tmp/test_sync_move_to/folders/2.yaml"), {
      "ExternalId": "2",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "node 2",
      "Items": [{
        "ID": "3",
        "Type": "card"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_move_to/cards/3.yaml"), {
      "ExternalId": "3",
      "ExternalUrl": "https://www.example.com/3",
      "Title": "node 3"
    })
    self.assertEqual(read_html("/tmp/test_sync_move_to/cards/3.html"), "card content")

  @use_guru()
  def test_sync_with_three_nodes(self, g):
    sync = g.bundle("test_sync_with_three_nodes")

    # make three nodes in a vertical hierarchy (folder-group -> folder -> card)
    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1")
    node2 = sync.node(id="2", url="https://www.example.com/2", title="node 2")
    node3 = sync.node(id="3", url="https://www.example.com/3", title="node 3", content="card content")
    node3.add_to(node2)
    node2.add_to(node1)
    sync.zip()

    self.assertEqual(read_yaml("/tmp/test_sync_with_three_nodes/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": [{
        "ID": "1",
        "Title": "node 1",
        "Type": "section"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_three_nodes/folder-groups/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Folders": ["2"]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_three_nodes/folders/2.yaml"), {
      "ExternalId": "2",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "node 2",
      "Items": [{
        "ID": "3",
        "Type": "card"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_three_nodes/cards/3.yaml"), {
      "ExternalId": "3",
      "ExternalUrl": "https://www.example.com/3",
      "Title": "node 3"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_three_nodes/cards/3.html"), "card content")

  @use_guru()
  def test_sync_where_a_folder_group_contains_a_card(self, g):
    sync = g.bundle("test_sync_where_a_folder_group_contains_a_card")

    # make three nodes in a vertical hierarchy (folder-group -> folder -> card)
    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1")
    node2 = sync.node(id="2", url="https://www.example.com/2", title="node 2")
    node3 = sync.node(id="3", url="https://www.example.com/3", title="node 3", content="card3 content")
    node3.add_to(node2)
    node2.add_to(node1)

    # add a node with content to the folder group (node 1)
    node4 = sync.node(id="4", url="https://www.example.com/4", title="node 4", content="card4 content")
    node4.add_to(node1)
    sync.zip()

    self.assertEqual(read_yaml("/tmp/test_sync_where_a_folder_group_contains_a_card/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": [{
        "ID": "1",
        "Title": "node 1",
        "Type": "section"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_where_a_folder_group_contains_a_card/folder-groups/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Folders": ["1_content_folder", "2"]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_where_a_folder_group_contains_a_card/folders/2.yaml"), {
      "ExternalId": "2",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "node 2",
      "Items": [{
        "ID": "3",
        "Type": "card"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_where_a_folder_group_contains_a_card/cards/3.yaml"), {
      "ExternalId": "3",
      "ExternalUrl": "https://www.example.com/3",
      "Title": "node 3"
    })
    self.assertEqual(read_html("/tmp/test_sync_where_a_folder_group_contains_a_card/cards/3.html"), "card3 content")

    # this is a folder that's inserted because node4 can't be directly on node1 because node1 is a folder group.
    self.assertEqual(read_yaml("/tmp/test_sync_where_a_folder_group_contains_a_card/folders/1_content_folder.yaml"), {
      "ExternalId": "1_content_folder",
      "Title": "node 1 Content",
      "Items": [{
        "ID": "4",
        "Type": "card"
      }]
    })
    self.assertEqual(read_html("/tmp/test_sync_where_a_folder_group_contains_a_card/cards/4.html"), "card4 content")

  @use_guru()
  def test_sync_add_child_edge_cases(self, g):
    sync = g.sync("test_sync_with_three_nodes")

    # make three nodes in a vertical hierarchy (folder-group -> folder -> card)
    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1")
    node2 = sync.node(id="2", url="https://www.example.com/2", title="node 2")
    node3 = sync.node(id="3", url="https://www.example.com/3", title="node 3", content="card content")

    # add 3 to 2 twice and we'll check that it only does it once.
    node3.add_to(node2)
    node3.add_to(node2)
    node2.add_to(node1)

    self.assertEqual(sync.has_node("1"), True)
    self.assertEqual(sync.has_node("2"), True)
    self.assertEqual(sync.has_node("3"), True)
    self.assertEqual(sync.has_node("4"), False)

    # try adding 1 to 3 to create a cycle.
    with self.assertRaises(RuntimeError):
      node1.add_to(node3)

    sync.zip()

    self.assertEqual(read_yaml("/tmp/test_sync_with_three_nodes/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": [{
        "ID": "1",
        "Title": "node 1",
        "Type": "section"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_three_nodes/folder-groups/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Folders": ["2"]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_three_nodes/folders/2.yaml"), {
      "ExternalId": "2",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "node 2",
      "Items": [{
        "ID": "3",
        "Type": "card"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_three_nodes/cards/3.yaml"), {
      "ExternalId": "3",
      "ExternalUrl": "https://www.example.com/3",
      "Title": "node 3"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_three_nodes/cards/3.html"), "card content")

  @use_guru()
  def test_sync_with_three_nodes_favor_sections(self, g):
    sync = g.bundle("test_sync_with_three_nodes_favor_sections")

    # make three nodes in a vertical hierarchy (folder -> section -> card)
    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1")
    node2 = sync.node(id="2", url="https://www.example.com/2", title="node 2")
    node3 = sync.node(id="3", url="https://www.example.com/3", title="node 3", content="card content")
    node3.add_to(node2)
    node2.add_to(node1)
    sync.zip(favor_sections=True)

    self.assertEqual(read_yaml("/tmp/test_sync_with_three_nodes_favor_sections/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": [{
        "ID": "1",
        "Title": "node 1",
        "Type": "folder"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_three_nodes_favor_sections/folders/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Items": [{
        "Title": "node 2",
        "Type": "section",
        "Items": [{
          "ID": "3",
          "Type": "card"
        }]
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_three_nodes_favor_sections/cards/3.yaml"), {
      "ExternalId": "3",
      "ExternalUrl": "https://www.example.com/3",
      "Title": "node 3"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_three_nodes_favor_sections/cards/3.html"), "card content")

  @use_guru()
  def test_sync_with_three_nodes_that_all_have_content(self, g):
    sync = g.bundle("test_sync_with_three_nodes_that_all_have_content")

    # make three nodes in a vertical hierarchy and all have content.
    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1", content="card1 content")
    node2 = sync.node(id="2", url="https://www.example.com/2", title="node 2", content="card2 content")
    node3 = sync.node(id="3", url="https://www.example.com/3", title="node 3", content="card3 content")
    node3.add_to(node2)
    node2.add_to(node1)
    sync.zip()

    self.assertEqual(read_yaml("/tmp/test_sync_with_three_nodes_that_all_have_content/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": [{
        "ID": "1",
        "Title": "node 1",
        "Type": "section"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_three_nodes_that_all_have_content/folder-groups/1.yaml"), {
      "ExternalId": "1",
      "Title": "node 1",
      "Folders": ["2"]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_three_nodes_that_all_have_content/folders/2.yaml"), {
      "ExternalId": "2",
      "Title": "node 2",
      "Items": [{
        "ID": "2_content",
        "Type": "card"
      }, {
        "ID": "1_content",
        "Type": "card"
      }, {
        "ID": "3",
        "Type": "card"
      }]
    })

    # nodes 1 and 2 have '_content' nodes created to hold their content.
    self.assertEqual(read_yaml("/tmp/test_sync_with_three_nodes_that_all_have_content/cards/1_content.yaml"), {
      "ExternalId": "1_content",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_three_nodes_that_all_have_content/cards/1_content.html"), "card1 content")
    self.assertEqual(read_yaml("/tmp/test_sync_with_three_nodes_that_all_have_content/cards/2_content.yaml"), {
      "ExternalId": "2_content",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "node 2"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_three_nodes_that_all_have_content/cards/2_content.html"), "card2 content")

    # node 3 is just a normal card.
    self.assertEqual(read_yaml("/tmp/test_sync_with_three_nodes_that_all_have_content/cards/3.yaml"), {
      "ExternalId": "3",
      "ExternalUrl": "https://www.example.com/3",
      "Title": "node 3"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_three_nodes_that_all_have_content/cards/3.html"), "card3 content")

  @use_guru()
  def test_sync_with_five_nodes(self, g):
    sync = g.bundle("test_sync_with_five_nodes")

    # make five nodes in a vertical hierarchy.
    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1")
    node2 = sync.node(id="2", url="https://www.example.com/2", title="node 2")
    node3 = sync.node(id="3", url="https://www.example.com/3", title="node 3")
    node4 = sync.node(id="4", url="https://www.example.com/4", title="node 4")
    node5 = sync.node(id="5", url="https://www.example.com/5", title="node 5", content="card content")
    node5.add_to(node4)
    node4.add_to(node3)
    node3.add_to(node2)
    node2.add_to(node1)
    sync.zip()

    self.assertEqual(read_yaml("/tmp/test_sync_with_five_nodes/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": [{
        "ID": "1",
        "Title": "node 1",
        "Type": "section"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_five_nodes/folder-groups/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Folders": ["2"]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_five_nodes/folders/2.yaml"), {
      "ExternalId": "2",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "node 2",
      "Items": [{
        "Title": "node 3",
        "Type": "section",
        "Items": [{
          "ID": "5",
          "Type": "card"
        }]
      }]
    })

    # node 4 doesn't get included in the zip because its parent, node 3, is a section.
    # that means node 4 has to be a card but it has no content, so we don't make a blank card.
    with self.assertRaises(FileNotFoundError):
      read_html("/tmp/test_sync_with_five_nodes/cards/4.html")
    with self.assertRaises(FileNotFoundError):
      read_html("/tmp/test_sync_with_five_nodes/cards/4.yaml")

    self.assertEqual(read_yaml("/tmp/test_sync_with_five_nodes/cards/5.yaml"), {
      "ExternalId": "5",
      "ExternalUrl": "https://www.example.com/5",
      "Title": "node 5"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_five_nodes/cards/5.html"), "card content")

  @use_guru()
  def test_sync_with_five_nodes_and_favor_sections(self, g):
    sync = g.bundle("test_sync_with_five_nodes_and_favor_sections")

    # make five nodes in a vertical hierarchy.
    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1")
    node2 = sync.node(id="2", url="https://www.example.com/2", title="node 2")
    node3 = sync.node(id="3", url="https://www.example.com/3", title="node 3")
    node4 = sync.node(id="4", url="https://www.example.com/4", title="node 4")
    node5 = sync.node(id="5", url="https://www.example.com/5", title="node 5", content="card content")
    node5.add_to(node4)
    node4.add_to(node3)
    node3.add_to(node2)
    node2.add_to(node1)
    sync.zip(favor_sections=True)

    # this ends up the same as if we don't favor sections because the hierarchy is deep
    # enough that we need to use folder groups, folders, and sections.
    self.assertEqual(read_yaml("/tmp/test_sync_with_five_nodes_and_favor_sections/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": [{
        "ID": "1",
        "Title": "node 1",
        "Type": "section"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_five_nodes_and_favor_sections/folder-groups/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Folders": ["2"]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_five_nodes_and_favor_sections/folders/2.yaml"), {
      "ExternalId": "2",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "node 2",
      "Items": [{
        "Title": "node 3",
        "Type": "section",
        "Items": [{
          "ID": "5",
          "Type": "card"
        }]
      }]
    })

    # node 4 doesn't get included in the zip because its parent, node 3, is a section.
    # that means node 4 has to be a card but it has no content, so we don't make a blank card.
    with self.assertRaises(FileNotFoundError):
      read_html("/tmp/test_sync_with_five_nodes/cards/4.html")
    with self.assertRaises(FileNotFoundError):
      read_html("/tmp/test_sync_with_five_nodes/cards/4.yaml")

    self.assertEqual(read_yaml("/tmp/test_sync_with_five_nodes_and_favor_sections/cards/5.yaml"), {
      "ExternalId": "5",
      "ExternalUrl": "https://www.example.com/5",
      "Title": "node 5"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_five_nodes_and_favor_sections/cards/5.html"), "card content")

  @use_guru()
  def test_sync_with_container_that_has_content(self, g):
    sync = g.bundle("test_sync_with_container_that_has_content")

    # make parent and child nodes but both have content.
    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1", content="parent content")
    node2 = sync.node(id="2", url="https://www.example.com/2", title="node 2", content="child content")
    node2.add_to(node1)
    sync.zip()

    # make sure the '1_content' node was generated because the node that becomes a folder
    # also needs a new node to be generated to hold its content.
    self.assertEqual(read_yaml("/tmp/test_sync_with_container_that_has_content/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": [{
        "ID": "1",
        "Title": "node 1",
        "Type": "folder"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_container_that_has_content/folders/1.yaml"), {
      "ExternalId": "1",
      "Title": "node 1",
      "Items": [{
        "ID": "1_content",
        "Type": "card"
      }, {
        "ID": "2",
        "Type": "card"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_container_that_has_content/cards/1_content.yaml"), {
      "ExternalId": "1_content",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_container_that_has_content/cards/1_content.html"), "parent content")
    self.assertEqual(read_yaml("/tmp/test_sync_with_container_that_has_content/cards/2.yaml"), {
      "ExternalId": "2",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "node 2"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_container_that_has_content/cards/2.html"), "child content")

  @use_guru()
  def test_sync_with_image(self, g):
    sync = g.bundle("test_sync_with_image")

    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1", content="""<p>
  <img src="https://www.example.com/test.png" />
</p>""")
    sync.zip()

    self.assertEqual(read_yaml("/tmp/test_sync_with_image/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": []
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_image/cards/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_image/cards/1.html"), """<p>
<img src="https://www.example.com/test.png"/>
</p>""")

  @use_guru()
  def test_sync_with_image_we_download(self, g):
    sync = g.bundle("test_sync_with_image_we_download")

    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1", content="""<p>
  <img src="https://www.example.com/test.png" />
  <img src="https://www.example.com/test.png" />
</p>""")

    download_mock = Mock()
    download_mock.return_value = True
    sync.zip(download_func=download_mock)

    self.assertEqual(download_mock.call_args.args, (
      "https://www.example.com/test.png",
      "/tmp/test_sync_with_image_we_download/resources/a3957e37ef2bcbe40ae4cfa69d8a2e5e.png",
      sync,
      node1
    ))
    self.assertEqual(read_yaml("/tmp/test_sync_with_image_we_download/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": []
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_image_we_download/cards/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_image_we_download/cards/1.html"), """<p>
<img src="resources/a3957e37ef2bcbe40ae4cfa69d8a2e5e.png"/>
<img src="resources/a3957e37ef2bcbe40ae4cfa69d8a2e5e.png"/>
</p>""")

  @use_guru()
  def test_sync_with_image_we_dont_download(self, g):
    sync = g.bundle("test_sync_with_image_we_dont_download")

    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1", content="""<p>
  <img src="test.png" />
</p>""")

    download_mock = Mock()
    download_mock.return_value = False
    sync.zip(download_func=download_mock)

    self.assertEqual(download_mock.call_args.args, (
      "https://www.example.com/test.png",
      "/tmp/test_sync_with_image_we_dont_download/resources/a3957e37ef2bcbe40ae4cfa69d8a2e5e.png",
      sync,
      node1
    ))
    self.assertEqual(read_yaml("/tmp/test_sync_with_image_we_dont_download/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": []
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_image_we_dont_download/cards/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_image_we_dont_download/cards/1.html"), """<p>
<img src="https://www.example.com/test.png"/>
</p>""")

  @use_guru()
  def test_sync_with_attachment_we_download(self, g):
    sync = g.bundle("test_sync_with_attachment_we_download")

    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1", content="""<p>
  <a href="test.pdf">test.pdf</a>
</p>""")

    download_mock = Mock()
    download_mock.return_value = (200, 2355)
    sync.zip(download_func=download_mock)

    self.assertEqual(download_mock.call_args.args, (
      "https://www.example.com/test.pdf",
      "/tmp/test_sync_with_attachment_we_download/resources/f7046e184217c5391c01550389ee7406.pdf",
      sync,
      node1
    ))
    self.assertEqual(read_yaml("/tmp/test_sync_with_attachment_we_download/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": []
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_attachment_we_download/cards/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_attachment_we_download/cards/1.html"), """<p>
<a href="resources/f7046e184217c5391c01550389ee7406.pdf">test.pdf</a>
</p>""")

  @use_guru()
  def test_sync_with_card_to_card_link(self, g):
    sync = g.bundle("test_sync_with_card_to_card_link")

    # make two nodes that have links to each other.
    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1", content="""<p>
  <a href="https://www.example.com/2">link to 2</a>
</p>""")
    node2 = sync.node(id="2", url="https://www.example.com/2", title="node 2", content="""<p>
  <a href="https://www.example.com/1">link to 1</a>
</p>""")
    sync.zip()

    self.assertEqual(read_yaml("/tmp/test_sync_with_card_to_card_link/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": []
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_card_to_card_link/cards/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_card_to_card_link/cards/1.html"), """<p>
<a href="cards/2">link to 2</a>
</p>""")
    self.assertEqual(read_yaml("/tmp/test_sync_with_card_to_card_link/cards/2.yaml"), {
      "ExternalId": "2",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "node 2"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_card_to_card_link/cards/2.html"), """<p>
<a href="cards/1">link to 1</a>
</p>""")

  @use_guru()
  def test_sync_with_complex_html(self, g):
    sync = g.bundle("test_sync_with_complex_html")

    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1", content="""<p>
  This <span>span tag</span> should be unwrapped.
</p>
<p style="border-top: 1px solid #000">
  <span style="margin: 50px; color: #44f; background: yellow">Some of these styles should be kept.</span>
  <a href="mailto:user@example.com">user@example.com</a>
  <a name="test">no href</a>
</p>
<p><br></p>
<ul><ul><li>test</li><li><ol></ol></li></ul></ul>
<nav><img src="https://www.example.com/test"/></nav>
<table class="test ghq-table other-class">
  <caption>test</caption>
  <tr>
    <td data-something="5" class="this-gets-removed">
      <h2>heading</h2>
      <p>test</p>
      <ul>
        <li>One</li>
        <li>Two</li>
      </ul>
    </td>
  </td>
</table>""")
    sync.zip()

    self.assertEqual(read_yaml("/tmp/test_sync_with_complex_html/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": []
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_complex_html/cards/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_complex_html/cards/1.html"), """<p>
  This span tag should be unwrapped.
</p>
<p>
<span style="color:#44f;background:yellow">Some of these styles should be kept.</span>
<a href="mailto:user@example.com">user@example.com</a>
<a>no href</a>
</p>
<ul><li>test</li><li></li></ul>
<img src="https://www.example.com/test"/>
<table class="ghq-table">
<tr>
<td>
<strong>heading</strong>
<br/>test

<br/>- One
<br/>- Two

</td>
</tr></table>""")

  @use_guru()
  def test_sync_visualization(self, g):
    sync = g.bundle("test_sync_visualization")

    # make five nodes in a vertical hierarchy.
    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1")
    node2 = sync.node(id="2", url="https://www.example.com/2", title="node 2")
    node3 = sync.node(id="3", url="https://www.example.com/3", title="node 3")
    node4 = sync.node(id="4", url="https://www.example.com/4", title="node 4")
    node5 = sync.node(id="5", title="node 5", content="card content")
    node5.add_to(node4)
    node4.add_to(node3)
    node3.add_to(node2)
    node2.add_to(node1)
    sync.zip()
    sync.print_tree()
    sync.print_tree(just_types=True)
    sync.view_in_browser(open_browser=False)

  @use_guru()
  def test_sync_with_local_files(self, g):
    sync = g.bundle("test_sync_with_local_files")

    html_file = "./tests/test_sync_with_local_files_node1.html"
    node1 = sync.node(id="1", url=html_file, title="node 1", content=read_html(html_file))

    sync.zip()

    self.assertEqual(read_html("/tmp/test_sync_with_local_files/cards/1.html"), """<p>
<img src="resources/fc82d6ce26e49cd7415aec38ff402de7.png"/>
</p>""")

  @use_guru()
  def test_sync_with_tags_and_folder_descriptions(self, g):
    sync = g.bundle("test_sync_with_tags_and_folder_descriptions")

    # make two nodes, one with content, and add that one to the other.
    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1", desc="folder description")
    node2 = sync.node(id="2", url="https://www.example.com/2", title="node 2", content="card content", tags=["tag1"])
    node3 = sync.node(id="3", url="https://www.example.com/3", title="node 3", content="card content", tags=["tag1", "tag2"])
    node2.add_to(node1)
    node3.add_to(node1)
    sync.zip()

    self.assertEqual(read_yaml("/tmp/test_sync_with_tags_and_folder_descriptions/collection.yaml"), {
      "Title": "test",
      "Tags": ["tag1", "tag2"],
      "Items": [{
        "ID": "1",
        "Title": "node 1",
        "Type": "folder"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_tags_and_folder_descriptions/folders/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Description": "folder description",
      "Items": [{
        "ID": "2",
        "Type": "card"
      }, {
        "ID": "3",
        "Type": "card"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_tags_and_folder_descriptions/cards/2.yaml"), {
      "ExternalId": "2",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "node 2",
      "Tags": ["tag1"]
    })
    self.assertEqual(read_html("/tmp/test_sync_with_tags_and_folder_descriptions/cards/2.html"), "card content")
    self.assertEqual(read_yaml("/tmp/test_sync_with_tags_and_folder_descriptions/cards/3.yaml"), {
      "ExternalId": "3",
      "ExternalUrl": "https://www.example.com/3",
      "Title": "node 3",
      "Tags": ["tag1", "tag2"]
    })
    self.assertEqual(read_html("/tmp/test_sync_with_tags_and_folder_descriptions/cards/3.html"), "card content")

  @use_guru()
  @responses.activate
  def test_sync_upload(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/collections", json=[{
      "id": "1111",
      "name": "test"
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1234",
      "name": "All Members"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/collections", json={
      "id": "2222"
    })

    sync = g.bundle("test_sync_upload")

    # make two nodes, one with content, and add that one to the other.
    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1", content="card content")
    sync.zip()

    self.assertEqual(read_yaml("/tmp/test_sync_upload/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": []
    })
    self.assertEqual(read_yaml("/tmp/test_sync_upload/cards/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1"
    })
    self.assertEqual(read_html("/tmp/test_sync_upload/cards/1.html"), "card content")

    # if we don't provide a collection name or ID, this throws an exception.
    with self.assertRaises(BaseException):
      sync.upload()

    sync.upload(name="General")

  @use_guru()
  def test_sync_node_edge_cases(self, g):
    sync = g.bundle("test_sync_node_edge_cases")

    # make two nodes, one with content, and add that one to the other.
    title = "this title is longer than 200 characters so we can check that it gets truncated where we expect it to get truncated even though i'm not sure why we do this, maybe it's a guru limitation that card titles can't be longer than 200 characters."
    node1 = sync.node(url="https://www.example.com/1", title=title, content="card content")
    sync.zip()

    self.assertEqual(read_yaml("/tmp/test_sync_node_edge_cases/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": []
    })
    self.assertEqual(read_yaml("/tmp/test_sync_node_edge_cases/cards/badc8210487e432c77699ef0ef7bd5e2.yaml"), {
      "ExternalId": "badc8210487e432c77699ef0ef7bd5e2",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "this title is longer than 200 characters so we can check that it gets truncated where we expect it to get truncated even though i'm not sure why we do this, maybe it's a guru limitation that card t..."
    })
    self.assertEqual(read_html("/tmp/test_sync_node_edge_cases/cards/badc8210487e432c77699ef0ef7bd5e2.html"), "card content")

  @use_guru()
  def test_sync_with_verbose_true(self, g):
    sync = g.bundle("test_sync_with_verbose_true", verbose=True)

    # make two nodes, one with content, and add that one to the other.
    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1")
    node2 = sync.node(id="2", url="https://www.example.com/2", title="node 2", content="card content")
    node2.add_to(node1)
    sync.zip()

    self.assertEqual(read_yaml("/tmp/test_sync_with_verbose_true/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": [{
        "ID": "1",
        "Title": "node 1",
        "Type": "folder"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_verbose_true/folders/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Items": [{
        "ID": "2",
        "Type": "card"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_verbose_true/cards/2.yaml"), {
      "ExternalId": "2",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "node 2"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_verbose_true/cards/2.html"), "card content")

  @use_guru()
  def test_sync_without_sort_order(self, g):
    # this test has no sort order. the next test will use these
    # same nodes but give them a different order.
    sync = g.bundle("test_sync_without_sort_order")

    # make two folders and one has four nodes.
    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1")
    node2 = sync.node(id="2", url="https://www.example.com/2", title="node 2")
    node3 = sync.node(id="3", url="https://www.example.com/3", title="node 3", content="card content")
    node4 = sync.node(id="4", url="https://www.example.com/4", title="node 4", content="card content")
    node5 = sync.node(id="5", url="https://www.example.com/5", title="node 5", content="card content")
    node6 = sync.node(id="6", url="https://www.example.com/6", title="node 6", content="card content")
    node3.add_to(node2)
    node4.add_to(node2)
    node5.add_to(node2)
    node6.add_to(node2)
    sync.zip()

    self.assertEqual(read_yaml("/tmp/test_sync_without_sort_order/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": [{
        "ID": "1",
        "Title": "node 1",
        "Type": "folder"
      }, {
        "ID": "2",
        "Title": "node 2",
        "Type": "folder"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_without_sort_order/folders/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Items": []
    })
    self.assertEqual(read_yaml("/tmp/test_sync_without_sort_order/folders/2.yaml"), {
      "ExternalId": "2",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "node 2",
      "Items": [
        {"ID": "3", "Type": "card"},
        {"ID": "4", "Type": "card"},
        {"ID": "5", "Type": "card"},
        {"ID": "6", "Type": "card"},
      ]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_without_sort_order/cards/3.yaml"), {
      "ExternalId": "3",
      "ExternalUrl": "https://www.example.com/3",
      "Title": "node 3"
    })
    self.assertEqual(read_html("/tmp/test_sync_without_sort_order/cards/3.html"), "card content")
    self.assertEqual(read_yaml("/tmp/test_sync_without_sort_order/cards/4.yaml"), {
      "ExternalId": "4",
      "ExternalUrl": "https://www.example.com/4",
      "Title": "node 4"
    })
    self.assertEqual(read_html("/tmp/test_sync_without_sort_order/cards/4.html"), "card content")
    self.assertEqual(read_yaml("/tmp/test_sync_without_sort_order/cards/5.yaml"), {
      "ExternalId": "5",
      "ExternalUrl": "https://www.example.com/5",
      "Title": "node 5"
    })
    self.assertEqual(read_html("/tmp/test_sync_without_sort_order/cards/5.html"), "card content")
    self.assertEqual(read_yaml("/tmp/test_sync_without_sort_order/cards/6.yaml"), {
      "ExternalId": "6",
      "ExternalUrl": "https://www.example.com/6",
      "Title": "node 6"
    })
    self.assertEqual(read_html("/tmp/test_sync_without_sort_order/cards/6.html"), "card content")

  @use_guru()
  def test_sync_with_sort_order(self, g):
    sync = g.bundle("test_sync_with_sort_order")

    # make two folders and one has four nodes.
    # set the indexes so it goes: node 2, node 1.
    # then inside node2, set the order has: node 6, node 3, node 4, node 5
    # (if no index is provided, those come last and keep their relative order)
    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1", index=50)
    node2 = sync.node(id="2", url="https://www.example.com/2", title="node 2", index=1)
    node3 = sync.node(id="3", url="https://www.example.com/3", title="node 3", content="card content", index=2)
    node4 = sync.node(id="4", url="https://www.example.com/4", title="node 4", content="card content")
    node5 = sync.node(id="5", url="https://www.example.com/5", title="node 5", content="card content")
    node6 = sync.node(id="6", url="https://www.example.com/6", title="node 6", content="card content", index=1)
    node3.add_to(node2)
    node4.add_to(node2)
    node5.add_to(node2)
    node6.add_to(node2)
    sync.zip()

    self.assertEqual(read_yaml("/tmp/test_sync_with_sort_order/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": [{
        "ID": "2",
        "Title": "node 2",
        "Type": "folder"
      }, {
        "ID": "1",
        "Title": "node 1",
        "Type": "folder"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_sort_order/folders/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Items": []
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_sort_order/folders/2.yaml"), {
      "ExternalId": "2",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "node 2",
      "Items": [
        {"ID": "6", "Type": "card"},
        {"ID": "3", "Type": "card"},
        {"ID": "4", "Type": "card"},
        {"ID": "5", "Type": "card"},
      ]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_sort_order/cards/3.yaml"), {
      "ExternalId": "3",
      "ExternalUrl": "https://www.example.com/3",
      "Title": "node 3"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_sort_order/cards/3.html"), "card content")
    self.assertEqual(read_yaml("/tmp/test_sync_with_sort_order/cards/4.yaml"), {
      "ExternalId": "4",
      "ExternalUrl": "https://www.example.com/4",
      "Title": "node 4"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_sort_order/cards/4.html"), "card content")
    self.assertEqual(read_yaml("/tmp/test_sync_with_sort_order/cards/5.yaml"), {
      "ExternalId": "5",
      "ExternalUrl": "https://www.example.com/5",
      "Title": "node 5"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_sort_order/cards/5.html"), "card content")
    self.assertEqual(read_yaml("/tmp/test_sync_with_sort_order/cards/6.yaml"), {
      "ExternalId": "6",
      "ExternalUrl": "https://www.example.com/6",
      "Title": "node 6"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_sort_order/cards/6.html"), "card content")

  @use_guru()
  def test_splitting_a_node_twice(self, g):
    sync = g.bundle("test_splitting_a_node_twice")

    # make two nodes, one with content, and add that one to the other.
    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1")
    node2 = sync.node(id="2", url="https://www.example.com/2", title="node 2", content="""<p>first card</p>
<h2>split here</h2>
<p>second card</p>
<table><tr><td>third card</td></tr></table>
    """)
    node3 = sync.node(id="3", url="https://www.example.com/3", title="node 3", content="card content")
    node2.add_to(node1)
    node3.add_to(node1)

    node2.split(
      "h2", "split here",
      "table", ""
    )

    sync.zip()

    self.assertEqual(read_yaml("/tmp/test_splitting_a_node_twice/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": [{
        "ID": "1",
        "Title": "node 1",
        "Type": "folder"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_splitting_a_node_twice/folders/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Items": [{
        "ID": "2",
        "Type": "card"
      }, {
        "ID": "2_part1",
        "Type": "card"
      }, {
        "ID": "2_part2",
        "Type": "card"
      }, {
        "ID": "3",
        "Type": "card"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_splitting_a_node_twice/cards/2.yaml"), {
      "ExternalId": "2",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "node 2"
    })
    self.assertEqual(read_html("/tmp/test_splitting_a_node_twice/cards/2.html"), "<p>first card</p>")

    self.assertEqual(read_yaml("/tmp/test_splitting_a_node_twice/cards/2_part1.yaml"), {
      "ExternalId": "2_part1",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "split here"
    })
    # we make sure the <h2> tag is removed since it matches the card's title.
    self.assertEqual(read_html("/tmp/test_splitting_a_node_twice/cards/2_part1.html"), "<p>second card</p>")

    # we didn't specify a title so this part inherits "node 2" as its title
    self.assertEqual(read_yaml("/tmp/test_splitting_a_node_twice/cards/2_part2.yaml"), {
      "ExternalId": "2_part2",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "node 2"
    })
    self.assertEqual(read_html("/tmp/test_splitting_a_node_twice/cards/2_part2.html"), "<table><tr><td>third card</td></tr></table>")

  @use_guru()
  def test_splitting_a_node_on_all_headings(self, g):
    sync = g.bundle("test_splitting_a_node_on_all_headings")

    # make two nodes, one with content, and add that one to the other.
    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1")
    node2 = sync.node(id="2", url="https://www.example.com/2", title="node 2", content="""<p>first card</p>
<h2>split here</h2>
<p>second card</p>
<h1>also split here</h1>
<table><tr><td>third card</td></tr></table>
    """)
    node3 = sync.node(id="3", url="https://www.example.com/3", title="node 3", content="card content")
    node2.add_to(node1)
    node3.add_to(node1)

    node2.split_all("h1, h2")

    sync.zip()

    self.assertEqual(read_yaml("/tmp/test_splitting_a_node_on_all_headings/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": [{
        "ID": "1",
        "Title": "node 1",
        "Type": "folder"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_splitting_a_node_on_all_headings/folders/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Items": [{
        "ID": "2",
        "Type": "card"
      }, {
        "ID": "2_part1",
        "Type": "card"
      }, {
        "ID": "2_part2",
        "Type": "card"
      }, {
        "ID": "3",
        "Type": "card"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_splitting_a_node_on_all_headings/cards/2.yaml"), {
      "ExternalId": "2",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "node 2"
    })
    self.assertEqual(read_html("/tmp/test_splitting_a_node_on_all_headings/cards/2.html"), "<p>first card</p>")

    self.assertEqual(read_yaml("/tmp/test_splitting_a_node_on_all_headings/cards/2_part1.yaml"), {
      "ExternalId": "2_part1",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "split here"
    })
    # we make sure the <h2> tag is removed since it matches the card's title.
    self.assertEqual(read_html("/tmp/test_splitting_a_node_on_all_headings/cards/2_part1.html"), "<p>second card</p>")

    # we didn't specify a title so this part inherits "node 2" as its title
    self.assertEqual(read_yaml("/tmp/test_splitting_a_node_on_all_headings/cards/2_part2.yaml"), {
      "ExternalId": "2_part2",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "also split here"
    })
    self.assertEqual(read_html("/tmp/test_splitting_a_node_on_all_headings/cards/2_part2.html"), "<table><tr><td>third card</td></tr></table>")

  @use_guru()
  def test_splitting_a_node_on_all_headings_and_nesting(self, g):
    sync = g.bundle("test_splitting_a_node_on_all_headings_and_nesting")

    # make two nodes, one with content, and add that one to the other.
    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1")
    node2 = sync.node(id="2", url="https://www.example.com/2", title="node 2", content="""<p>first card</p>
<h2>split here</h2>
<p>second card</p>
<h1>also split here</h1>
<table><tr><td>third card</td></tr></table>
    """)
    node3 = sync.node(id="3", url="https://www.example.com/3", title="node 3", content="card content")
    node2.add_to(node1)
    node3.add_to(node1)

    node2.split_all("h1, h2", nest=True)

    sync.zip(favor_sections=True)

    self.assertEqual(read_yaml("/tmp/test_splitting_a_node_on_all_headings_and_nesting/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": [{
        "ID": "1",
        "Title": "node 1",
        "Type": "folder"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_splitting_a_node_on_all_headings_and_nesting/folders/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Items": [{
        "Title": "node 2",
        "Type": "section",
        "Items": [{
          "ID": "2_content",
          "Type": "card"
        }, {
          "ID": "2_part1",
          "Type": "card"
        }, {
          "ID": "2_part2",
          "Type": "card"
        }]
      }, {
        "ID": "3",
        "Type": "card"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_splitting_a_node_on_all_headings_and_nesting/cards/2_content.yaml"), {
      "ExternalId": "2_content",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "node 2"
    })
    self.assertEqual(read_html("/tmp/test_splitting_a_node_on_all_headings_and_nesting/cards/2_content.html"), "<p>first card</p>")

    self.assertEqual(read_yaml("/tmp/test_splitting_a_node_on_all_headings_and_nesting/cards/2_part1.yaml"), {
      "ExternalId": "2_part1",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "split here"
    })
    # we make sure the <h2> tag is removed since it matches the card's title.
    self.assertEqual(read_html("/tmp/test_splitting_a_node_on_all_headings_and_nesting/cards/2_part1.html"), "<p>second card</p>")

    # we didn't specify a title so this part inherits "node 2" as its title
    self.assertEqual(read_yaml("/tmp/test_splitting_a_node_on_all_headings_and_nesting/cards/2_part2.yaml"), {
      "ExternalId": "2_part2",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "also split here"
    })
    self.assertEqual(read_html("/tmp/test_splitting_a_node_on_all_headings_and_nesting/cards/2_part2.html"), "<table><tr><td>third card</td></tr></table>")

  @use_guru()
  def test_removing_a_node(self, g):
    sync = g.bundle("test_removing_a_node")

    # make two nodes, one with content, and add that one to the other.
    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1")
    node2 = sync.node(id="2", url="https://www.example.com/2", title="node 2", content="card content")
    node2.add_to(node1)
    node2.remove()
    sync.zip()

    self.assertEqual(read_yaml("/tmp/test_removing_a_node/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": [{
        "ID": "1",
        "Title": "node 1",
        "Type": "folder"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_removing_a_node/folders/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Items": []
    })

    # assert these files don't exist.
    with self.assertRaises(FileNotFoundError):
      read_html("/tmp/test_removing_a_node/cards/2.html")
    with self.assertRaises(FileNotFoundError):
      read_html("/tmp/test_removing_a_node/cards/2.yaml")

  @use_guru()
  def test_handling_a_table_inside_a_list(self, g):
    bundle = g.bundle("test_handling_a_table_inside_a_list")

    # todo: add some more complicated tests here.
    html = """<ul><li>test<table><tr><td>table</td></tr></table>after table</li><li>second item</li></ul>"""
    new_html = """<ul><li>test</li></ul><table><tr><td>table</td></tr></table><ul><li>after table</li><li>second item</li></ul>"""
    node1 = bundle.node(id="1", title="node 1", content=html)
    bundle.zip()

    self.assertEqual(read_html("/tmp/test_handling_a_table_inside_a_list/cards/1.html"), new_html)

  @use_guru()
  def test_handling_a_code_block_inside_a_list(self, g):
    bundle = g.bundle("test_handling_a_code_block_inside_a_list")

    html = """<ul><li>test<pre>here's a code block
it's multiple lines
    with indentation
</pre>after table</li><li>second item</li></ul>"""
    new_html = """<ul><li>test</li></ul><pre>here's a code block
it's multiple lines
    with indentation
</pre><ul><li>after table</li><li>second item</li></ul>"""
    node1 = bundle.node(id="1", title="node 1", content=html)
    bundle.zip()

    self.assertEqual(read_html("/tmp/test_handling_a_code_block_inside_a_list/cards/1.html"), new_html)

  @use_guru()
  def test_handling_an_iframe_inside_nested_lists(self, g):
    bundle = g.bundle("test_handling_an_iframe_inside_nested_lists")

    html = """<ul>
  <li>
    test
  </li>
  <li>
    <ol>
      <li>
        one
      </li>
      <li>
        two
      </li>
    </ol>
  </li>
  <li>
    <ul>
      <li>
        <ol>
          <li>
            iframe:​ ​<iframe src="https://www.example.com"></iframe>
          </li>
        </ol>
      </li>
    </ul>
  </li>
  <li>
    <ol>
      <li>
        three
      </li>
    </ol>
  </li>
  <li>
    end
  </li>
</ul>"""

    new_html = """<ul>
<li>
    test
  </li>
<li>
<ol>
<li>
        one
      </li>
<li>
        two
      </li>
</ol>
</li>
<li>
<ul>
<li>
<ol>
<li>
            iframe:​ ​</li></ol></li></ul></li></ul><iframe src="https://www.example.com"></iframe><ul><li><ul><li><ol start="2"><li>
</li>
</ol>
</li>
</ul>
</li>
<li>
<ol>
<li>
        three
      </li>
</ol>
</li>
<li>
    end
  </li>
</ul>"""
    node1 = bundle.node(id="1", title="node 1", content=html)
    bundle.zip()

    self.assertEqual(read_html("/tmp/test_handling_an_iframe_inside_nested_lists/cards/1.html"), new_html)

  @use_guru()
  def test_splitting_a_numbered_list(self, g):
    bundle = g.bundle("test_splitting_a_numbered_list")

    # todo: nest with nested <ol> tags to make sure each starts at the right number.
    html = """<ol>
<li>one</li>
<li>two</li>
<li>three<pre>code block</pre></li>
<li>four</li>
</ol>"""
    new_html = """<ol>
<li>one</li>
<li>two</li>
<li>three</li></ol><pre>code block</pre><ol start="4">
<li>four</li>
</ol>"""

    node1 = bundle.node(id="1", title="node 1", content=html)
    bundle.zip()

    self.assertEqual(read_html("/tmp/test_splitting_a_numbered_list/cards/1.html"), new_html)

  @use_guru()
  def test_splitting_a_numbered_list_that_doesnt_start_at_1(self, g):
    bundle = g.bundle("test_splitting_a_numbered_list_that_doesnt_start_at_1")

    html = """<ol start="3">
<li>one</li>
<li>two</li>
<li>three<pre>code block</pre></li>
<li>four</li>
</ol>"""
    new_html = """<ol start="3">
<li>one</li>
<li>two</li>
<li>three</li></ol><pre>code block</pre><ol start="6">
<li>four</li>
</ol>"""

    node1 = bundle.node(id="1", title="node 1", content=html)
    bundle.zip()

    self.assertEqual(read_html("/tmp/test_splitting_a_numbered_list_that_doesnt_start_at_1/cards/1.html"), new_html)

  @use_guru()
  def test_referencing_a_resource_that_doesnt_exist(self, g):
    bundle = g.bundle("test_referencing_a_resource_that_doesnt_exist")

    html = """<a href="doesnt_exist.html">bad link</a><img src="doesnt_exist.png" />"""

    node1 = bundle.node(id="1", title="node 1", url="/tmp/local.html", content=html)
    bundle.zip()

    self.assertEqual(read_html("/tmp/test_referencing_a_resource_that_doesnt_exist/cards/1.html"), "bad link")

  @use_guru()
  def test_empty_and_removed_nodes(self, g):
    bundle = g.bundle("test_empty_and_removed_nodes", skip_empty_sections=True)

    folder = bundle.node(id="folder", title="folder")
    section1 = bundle.node(id="section1", title="section1")
    section2 = bundle.node(id="section2", title="section2")
    card1 = bundle.node(id="card1", title="card 1", content="""card 1""")
    card2 = bundle.node(id="card2", title="card 2")

    section1.add_to(folder)
    section2.add_to(folder)
    card1.add_to(folder)
    card2.add_to(section2)

    bundle.zip(favor_sections=True)

    self.assertEqual(read_yaml("/tmp/test_empty_and_removed_nodes/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": [{
        "ID": "folder",
        "Title": "folder",
        "Type": "folder"
      }]
    })

    # card2 is removed because it has no content.
    # section2 is removed because removing card2 leaves it empty.
    # section1 is removed because it was always empty.
    self.assertEqual(read_yaml("/tmp/test_empty_and_removed_nodes/folders/folder.yaml"), {
      "Title": "folder",
      "ExternalId": "folder",
      "Items": [{
        "ID": "card1",
        "Type": "card"
      }]
    })

  @use_guru()
  def test_linking_edge_cases(self, g):
    bundle = g.bundle("test_linking_edge_cases")

    # edge cases:
    # linking to a folder
    # linking to a folder group
    # a link with no href
    # linking to a node's alt_url
    # linking to a removed node.
    # linking to a section's url.

    folder_group = bundle.node(id="node1", title="node 1", url="https://www.example.com/node1")
    folder = bundle.node(id="node2", title="node 2", url="https://www.example.com/node2", alt_urls=["https://www.example.com/folder"])
    section = bundle.node(id="node3", title="node 3", url="https://www.example.com/section")
    card = bundle.node(id="node4", title="node 4", content="""<p>
<a href="https://www.example.com/node1">folder group link</a>
<a href="https://www.example.com/folder">folder link</a>
<a href="https://www.example.com/section">section link</a>
<a href="https://www.example.com/removed_card">removed card</a>
<a href="">link with no href</a>
</p>""")
    removed_card = bundle.node(id="node5", title="node 5", url="https://www.example.com/removed_card")

    card.add_to(section)
    section.add_to(folder)
    removed_card.add_to(folder)
    folder.add_to(folder_group)

    bundle.zip()

    self.assertEqual(read_html("/tmp/test_linking_edge_cases/cards/node4.html"), """<p>
<a href="folder-groups/node1">folder group link</a>
<a href="folders/node2">folder link</a>
<a href="https://www.example.com/section">section link</a>
<a href="https://www.example.com/removed_card">removed card</a>
<a href="">link with no href</a>
</p>""")

  @use_guru()
  def test_guru_markdown_blocks(self, g):
    bundle = g.bundle("test_guru_markdown_blocks")

    # make sure the attributes on the markdown block's div are preserved and
    # that style attributes on elements inside the markdown are left alone.
    node1 = bundle.node(id="1", url="https://www.example.com/1", title="node 1", content="""<div class="ghq-card-content__markdown" data-ghq-card-content-markdown-content="%3Cdiv%20style%3D%22background-color%3A%23F89E91%3Bcolor%3A%234A1717%3Bpadding%3A1px%3Btext-align%3Aleft%3Bfont-size%3A16px%3Bmargin-bottom%3A16px%22%3E%0A%3Cp%20style%3D%22margin%3A%2016px%22%3Etest%20content%20%3Cstrong%3Eabcd%201234.%3C%2Fstrong%3E%3C%2Fp%3E%0A%3C%2Fdiv%3E" data-ghq-card-content-type="MARKDOWN">
	<div style="background-color:#F89E91;color:#4A1717;padding:1px;text-align:left;font-size:16px;margin-bottom:16px" class="">
		<p style="margin: 16px" class="">
			test content
			<strong>
				abcd 1234.
			</strong>
		</p>
	</div>
</div>""")
    bundle.zip()

    self.assertEqual(read_html("/tmp/test_guru_markdown_blocks/cards/1.html"), """<div class="ghq-card-content__markdown" data-ghq-card-content-markdown-content="%3Cdiv%20style%3D%22background-color%3A%23F89E91%3Bcolor%3A%234A1717%3Bpadding%3A1px%3Btext-align%3Aleft%3Bfont-size%3A16px%3Bmargin-bottom%3A16px%22%3E%0A%3Cp%20style%3D%22margin%3A%2016px%22%3Etest%20content%20%3Cstrong%3Eabcd%201234.%3C%2Fstrong%3E%3C%2Fp%3E%0A%3C%2Fdiv%3E" data-ghq-card-content-type="MARKDOWN">
<div style="background-color:#F89E91;color:#4A1717;padding:1px;text-align:left;font-size:16px;margin-bottom:16px">
<p style="margin: 16px">
			test content
			<strong>
				abcd 1234.
			</strong>
</p>
</div>
</div>""")

  @use_guru()
  def test_removing_empty_lists_and_list_items(self, g):
    bundle = g.bundle("test_removing_empty_lists_and_list_items")

    # the ul contains an image, so one li is removed but the list remains.
    # the ol only contains an li that'll be removed, so we expect the ol to be removed too.
    html = """<ul><li><br/></li><li><img src="https://www.example.com/test.png"/></li></ul><ol><li><br/></li></ol>"""
    new_html = """<ul><li><img src="https://www.example.com/test.png"/></li></ul>"""
    node1 = bundle.node(id="1", title="node 1", content=html)
    bundle.zip()

    self.assertEqual(read_html("/tmp/test_removing_empty_lists_and_list_items/cards/1.html"), new_html)
