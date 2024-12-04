#from types import NoneType
import guru

# API token info
email = "username"
token = "aptoken4"

g = guru.Guru(email, token, qa=False)


# Create a new bundle
bundle = g.bundle("ozmo_knowledge_sync")

# Level 1 folder (depth = 1)
folder_lvl_1 = bundle.node(id="folder_lvl_1", title="Folder 1")

# Add a card to level 1 folder 
card_at_lvl_1 = bundle.node(
    id="card_lvl_1",
    title="Card at Level 1",
    content="This is a card at Level 1."
)
folder_lvl_1.add_child(card_at_lvl_1)

# Level 2 folder (depth = 2)
Folder_lvl_2 = bundle.node(id="folder_lvl_2", title="Folder 2")
folder_lvl_1.add_child(Folder_lvl_2)


# Level 3 folder (depth = 3)
folder_lvl_3 = bundle.node(id="folder_lvl_3", title="Folder 3")
Folder_lvl_2.add_child(folder_lvl_3)

# Add a card to level 3 folder (depth = 3)
card_level_3 = bundle.node(
    id="card_level_3",
    title="Card at level 3",
    content="This is a card at level 3."
)
folder_lvl_3.add_child(card_level_3)

# Level 4 folder (depth = 4) - This should be discarded
folder_lvl_4 = bundle.node(id="folder_level_4", title="Folder Level 4")
folder_lvl_3.add_child(folder_lvl_4)

# Add a card to level 4 folder (depth = 4) - This should be discarded
card_at_level_4 = bundle.node(
    id="card_level_4",
    title="Card at Level 4",
    content="This card should be discarded."
)
folder_lvl_4.add_child(card_at_level_4)

# Process the bundle
bundle.zip()

# Print the tree
bundle.print_tree()
