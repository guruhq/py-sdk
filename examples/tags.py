
import guru

g = guru.Guru()

# get all tags on the team.
tags = g.get_tags()
print(len(tags), "tags")

# find a folder, then add a tag to all the cards on it.
folder = g.get_folder("Onfoldering", collection="Engineering")

for card in folder.cards:
  card.add_tag("onfoldering")
