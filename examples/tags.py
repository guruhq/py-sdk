
import guru

g = guru.Guru()

# get all tags on the team.
tags = g.get_tags()
print(len(tags), "tags")

# find a board, then add a tag to all the cards on it.
board = g.get_board("Onboarding", collection="Engineering")

for card in board.cards:
  card.add_tag("onboarding")
