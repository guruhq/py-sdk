
import guru

g = guru.Guru()

# we load a few different sets of cards.
# change the collection names to ones that exist on your team.
product_cards = g.find_cards(collection="Product")
march_1_to_15 = g.find_cards(created_after="2021-03-01", created_before="2021-03-15")
your_cards = g.find_cards(author=g.username)

# you can also combine these filters:
your_engineering_cards_after_march_1 = g.find_cards(
  collection="Engineering",
  created_after="2021-03-01",
  author=g.username
)

print(len(product_cards), "product cards")
print(len(march_1_to_15), "cards created 3/1 - 3/15")
print(len(your_cards), "cards created by", g.username)
print(len(your_engineering_cards_after_march_1), "cards in Engineering created by you after 3/1")
