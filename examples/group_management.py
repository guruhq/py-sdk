
import guru

g = guru.Guru(dry_run=False)

# make a new collection.
g.make_collection("Test Collection")

# add some groups to it.
g.add_group_to_collection("group 3", "Test Collection", guru.READ_ONLY)
g.add_group_to_collection("Experts", "Test Collection", guru.COLLECTION_OWNER)

# change some existing group permissions.
g.add_group_to_collection("All Members", "Test Collection", guru.AUTHOR)

# remove some groups from it.
# g.remove_group_from_collection("All Members", "Test Collection")

# delete the collection.
# g.delete_collection("Test Collection")



