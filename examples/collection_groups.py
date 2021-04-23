
import guru

g = guru.Guru()

general_collection = g.get_collection("General")

# print out the list of groups that can access the General collection.
for access in general_collection.get_groups():
  print(access.group_name, access.role)

# give all groups author access to the General collection.
for group in g.get_groups():
  general_collection.add_group(group, guru.AUTHOR)
