
import guru

g = guru.Guru()

# find the Products board group in the CS collection.
board_group = g.get_board_group("Products", collection="CS")

# share each board in the Products board group with the 'Knowledge Pilot Team' group.
for board in board_group.items:
  board.add_group("Knowledge Pilot Team")
