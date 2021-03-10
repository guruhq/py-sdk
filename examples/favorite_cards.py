
import guru

g = guru.Guru()

all_favorites = []

for favorite_list in g.get_favorite_lists():
  print(favorite_list.id, favorite_list.title, len(favorite_list.items))
  for card in favorite_list.cards:
    all_favorites.append(card.id)

print(all_favorites)
