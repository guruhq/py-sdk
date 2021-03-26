import guru

g = guru.Guru()

## resolve all open comments
for card in g.find_cards():
  open_comments = card.get_open_card_comments()
  for comment in open_comments():
    if comment.is_before("2021-03-01"):
      comment.resolve()