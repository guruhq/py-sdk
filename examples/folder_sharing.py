
import guru

g = guru.Guru()

# find the Products folder group in the CS collection.
folder_group = g.get_folder_group("Products", collection="CS")

# share each folder in the Products folder group with the 'Knowledge Pilot Team' group.
for folder in folder_group.items:
  folder.add_group("Knowledge Pilot Team")
