
import guru

g = guru.Guru()

# set the order of items in a home board:
home_board = g.get_home_board("Board Order Test 1")
home_board.set_item_order("Board A", "Board B")

# set the order of items in a board group:
board_group = g.get_board_group("My Board Group", "Board Order Test 2")
board_group.set_item_order("item 2", "item 0 Content", "item 1", "item 3")

# set the order of items in a board:
board_a = g.get_board("Board A")
board_a.set_item_order("Card B", "Card A", "Card C")

# # make a new board group:
g.make_board_group("Engineering", "Test")
