
import guru

g = guru.Guru()

# set the order of items in a home folder:
home_folder = g.get_home_folder("Folder Order Test 1")
home_folder.set_item_order("Folder A", "Folder B")

# set the order of items in a folder group:
folder_group = g.get_folder_group("My Folder Group", "Folder Order Test 2")
folder_group.set_item_order("item 2", "item 0 Content", "item 1", "item 3")

# set the order of items in a folder:
folder_a = g.get_folder("Folder A")
folder_a.set_item_order("Card B", "Card A", "Card C")

# # make a new folder group:
g.make_folder_group("Engineering", "Test")
