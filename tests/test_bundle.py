
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
        "Type": "board"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_two_nodes/boards/1.yaml"), {
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
        "Type": "board"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_where_the_child_has_no_content/boards/1.yaml"), {
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
  def test_sync_with_a_node_on_two_boards(self, g):
    sync = g.bundle("test_sync_with_a_node_on_two_boards")

    # make two nodes, one with content, and add that one to the other.
    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1")
    node2 = sync.node(id="2", url="https://www.example.com/2", title="node 2")
    node3 = sync.node(id="3", url="https://www.example.com/3", title="node 3", content="card content")
    node3.add_to(node1)
    node3.add_to(node2)
    sync.zip()

    self.assertEqual(read_yaml("/tmp/test_sync_with_a_node_on_two_boards/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": [{
        "ID": "1",
        "Title": "node 1",
        "Type": "board"
      }, {
        "ID": "2",
        "Title": "node 2",
        "Type": "board"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_a_node_on_two_boards/boards/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Items": [{
        "ID": "3",
        "Type": "card"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_a_node_on_two_boards/boards/2.yaml"), {
      "ExternalId": "2",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "node 2",
      "Items": [{
        "ID": "3",
        "Type": "card"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_a_node_on_two_boards/cards/3.yaml"), {
      "ExternalId": "3",
      "ExternalUrl": "https://www.example.com/3",
      "Title": "node 3"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_a_node_on_two_boards/cards/3.html"), "card content")

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
        "Type": "board"
      }, {
        "ID": "2",
        "Title": "node 2",
        "Type": "board"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_move_to/boards/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Items": []
    })
    self.assertEqual(read_yaml("/tmp/test_sync_move_to/boards/2.yaml"), {
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

    # make three nodes in a vertical hierarchy (board-group -> board -> card)
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
    self.assertEqual(read_yaml("/tmp/test_sync_with_three_nodes/board-groups/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Boards": ["2"]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_three_nodes/boards/2.yaml"), {
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
  def test_sync_where_a_board_group_contains_a_card(self, g):
    sync = g.bundle("test_sync_where_a_board_group_contains_a_card")

    # make three nodes in a vertical hierarchy (board-group -> board -> card)
    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1")
    node2 = sync.node(id="2", url="https://www.example.com/2", title="node 2")
    node3 = sync.node(id="3", url="https://www.example.com/3", title="node 3", content="card3 content")
    node3.add_to(node2)
    node2.add_to(node1)

    # add a node with content to the board group (node 1)
    node4 = sync.node(id="4", url="https://www.example.com/4", title="node 4", content="card4 content")
    node4.add_to(node1)
    sync.zip()

    self.assertEqual(read_yaml("/tmp/test_sync_where_a_board_group_contains_a_card/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": [{
        "ID": "1",
        "Title": "node 1",
        "Type": "section"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_where_a_board_group_contains_a_card/board-groups/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Boards": ["1_content_board", "2"]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_where_a_board_group_contains_a_card/boards/2.yaml"), {
      "ExternalId": "2",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "node 2",
      "Items": [{
        "ID": "3",
        "Type": "card"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_where_a_board_group_contains_a_card/cards/3.yaml"), {
      "ExternalId": "3",
      "ExternalUrl": "https://www.example.com/3",
      "Title": "node 3"
    })
    self.assertEqual(read_html("/tmp/test_sync_where_a_board_group_contains_a_card/cards/3.html"), "card3 content")

    # this is a board that's inserted because node4 can't be directly on node1 because node1 is a board group.
    self.assertEqual(read_yaml("/tmp/test_sync_where_a_board_group_contains_a_card/boards/1_content_board.yaml"), {
      "ExternalId": "1_content_board",
      "Title": "node 1 Content",
      "Items": [{
        "ID": "4",
        "Type": "card"
      }]
    })
    self.assertEqual(read_html("/tmp/test_sync_where_a_board_group_contains_a_card/cards/4.html"), "card4 content")

  @use_guru()
  def test_sync_add_child_edge_cases(self, g):
    sync = g.sync("test_sync_with_three_nodes")

    # make three nodes in a vertical hierarchy (board-group -> board -> card)
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
    self.assertEqual(read_yaml("/tmp/test_sync_with_three_nodes/board-groups/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Boards": ["2"]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_three_nodes/boards/2.yaml"), {
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

    # make three nodes in a vertical hierarchy (board -> section -> card)
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
        "Type": "board"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_three_nodes_favor_sections/boards/1.yaml"), {
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
    self.assertEqual(read_yaml("/tmp/test_sync_with_three_nodes_that_all_have_content/board-groups/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Boards": ["1_content_board", "2"]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_three_nodes_that_all_have_content/boards/1_content_board.yaml"), {
      "ExternalId": "1_content_board",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1 Content",
      "Items": [{
        "ID": "1_content",
        "Type": "card"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_three_nodes_that_all_have_content/boards/2.yaml"), {
      "ExternalId": "2",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "node 2",
      "Items": [{
        "ID": "2_content",
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
    self.assertEqual(read_yaml("/tmp/test_sync_with_five_nodes/board-groups/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Boards": ["2"]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_five_nodes/boards/2.yaml"), {
      "ExternalId": "2",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "node 2",
      "Items": [{
        "Title": "node 3",
        "Type": "section",
        "Items": [{
          "ID": "4",
          "Type": "card"
        }, {
          "ID": "5",
          "Type": "card"
        }]
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_five_nodes/cards/4.yaml"), {
      "ExternalId": "4",
      "ExternalUrl": "https://www.example.com/4",
      "Title": "node 4"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_five_nodes/cards/4.html"), "")

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
    # enough that we need to use board groups, boards, and sections.
    self.assertEqual(read_yaml("/tmp/test_sync_with_five_nodes_and_favor_sections/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": [{
        "ID": "1",
        "Title": "node 1",
        "Type": "section"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_five_nodes_and_favor_sections/board-groups/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Boards": ["2"]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_five_nodes_and_favor_sections/boards/2.yaml"), {
      "ExternalId": "2",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "node 2",
      "Items": [{
        "Title": "node 3",
        "Type": "section",
        "Items": [{
          "ID": "4",
          "Type": "card"
        }, {
          "ID": "5",
          "Type": "card"
        }]
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_five_nodes_and_favor_sections/cards/4.yaml"), {
      "ExternalId": "4",
      "ExternalUrl": "https://www.example.com/4",
      "Title": "node 4"
    })
    self.assertEqual(read_html("/tmp/test_sync_with_five_nodes_and_favor_sections/cards/4.html"), "")

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

    # make sure the '1_content' node was generated because the node that becomes a board
    # also needs a new node to be generated to hold its content.
    self.assertEqual(read_yaml("/tmp/test_sync_with_container_that_has_content/collection.yaml"), {
      "Title": "test",
      "Tags": [],
      "Items": [{
        "ID": "1",
        "Title": "node 1",
        "Type": "board"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_container_that_has_content/boards/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
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
    download_mock.return_value = True
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
<p><img src="https://www.example.com/test"/></p>
<table>
  <caption>test</caption>
  <tr>
    <td data-something="5">
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

<p><img src="https://www.example.com/test"/></p>
<table>

<tr>
<td>
<p>test</p>

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
  def test_sync_with_tags_and_board_descriptions(self, g):
    sync = g.bundle("test_sync_with_tags_and_board_descriptions")

    # make two nodes, one with content, and add that one to the other.
    node1 = sync.node(id="1", url="https://www.example.com/1", title="node 1", desc="board description")
    node2 = sync.node(id="2", url="https://www.example.com/2", title="node 2", content="card content", tags=["tag1"])
    node3 = sync.node(id="3", url="https://www.example.com/3", title="node 3", content="card content", tags=["tag1", "tag2"])
    node2.add_to(node1)
    node3.add_to(node1)
    sync.zip()

    self.assertEqual(read_yaml("/tmp/test_sync_with_tags_and_board_descriptions/collection.yaml"), {
      "Title": "test",
      "Tags": ["tag1", "tag2"],
      "Items": [{
        "ID": "1",
        "Title": "node 1",
        "Type": "board"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_tags_and_board_descriptions/boards/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Description": "board description",
      "Items": [{
        "ID": "2",
        "Type": "card"
      }, {
        "ID": "3",
        "Type": "card"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_tags_and_board_descriptions/cards/2.yaml"), {
      "ExternalId": "2",
      "ExternalUrl": "https://www.example.com/2",
      "Title": "node 2",
      "Tags": ["tag1"]
    })
    self.assertEqual(read_html("/tmp/test_sync_with_tags_and_board_descriptions/cards/2.html"), "card content")
    self.assertEqual(read_yaml("/tmp/test_sync_with_tags_and_board_descriptions/cards/3.yaml"), {
      "ExternalId": "3",
      "ExternalUrl": "https://www.example.com/3",
      "Title": "node 3",
      "Tags": ["tag1", "tag2"]
    })
    self.assertEqual(read_html("/tmp/test_sync_with_tags_and_board_descriptions/cards/3.html"), "card content")

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
        "Type": "board"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_verbose_true/boards/1.yaml"), {
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

    # make two boards and one has four nodes.
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
        "Type": "board"
      }, {
        "ID": "2",
        "Title": "node 2",
        "Type": "board"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_without_sort_order/boards/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Items": []
    })
    self.assertEqual(read_yaml("/tmp/test_sync_without_sort_order/boards/2.yaml"), {
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

    # make two boards and one has four nodes.
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
        "Type": "board"
      }, {
        "ID": "1",
        "Title": "node 1",
        "Type": "board"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_sort_order/boards/1.yaml"), {
      "ExternalId": "1",
      "ExternalUrl": "https://www.example.com/1",
      "Title": "node 1",
      "Items": []
    })
    self.assertEqual(read_yaml("/tmp/test_sync_with_sort_order/boards/2.yaml"), {
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
        "Type": "board"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_splitting_a_node_twice/boards/1.yaml"), {
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
        "Type": "board"
      }]
    })
    self.assertEqual(read_yaml("/tmp/test_removing_a_node/boards/1.yaml"), {
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
