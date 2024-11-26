from types import NoneType
import guru

# API token info
email = "mhornak@getguru.com"
token = "2485e758-b975-4aa6-a3af-584bd38a63a4"

g = guru.Guru(email, token, qa=True)


# Create a new bundle
bundle = g.bundle("ozmo_knowledge_sync")

# Create root folder
root_folder = bundle.node(id="root_folder", title="Root Folder")

# Level 1 folder
folder_level_1 = bundle.node(id="folder_level_1", title="Folder Level 1")
root_folder.add_child(folder_level_1)

# Level 2 folder
folder_level_2 = bundle.node(id="folder_level_2", title="Folder Level 2")
folder_level_1.add_child(folder_level_2)

# Level 3 folder
folder_level_3 = bundle.node(id="folder_level_3", title="Folder Level 3")
folder_level_2.add_child(folder_level_3)

# Level 4 folder (should be discarded)
folder_level_4 = bundle.node(id="folder_level_4", title="Folder Level 4")
folder_level_3.add_child(folder_level_4)

# Add a card to level 3 folder
card_at_level_3 = bundle.node(id="card_level_3", title="Card at Level 3", content="This is a card at level 3.")
folder_level_3.add_child(card_at_level_3)

# Add a card to level 4 folder (should be discarded)
card_at_level_4 = bundle.node(id="card_level_4", title="Card at Level 4", content="This card should be discarded.")
folder_level_4.add_child(card_at_level_4)

# Process the bundle
bundle.zip()

# Print the tree
bundle.print_tree()
