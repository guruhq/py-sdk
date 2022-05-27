import guru

g = guru.Guru("ahojnowski+demo@getguru.com","3c5d9c2d-0fb1-4067-a6e5-f9eaeb63e121")


cats = g.get_tag_categorys()

for cat in cats:
  print(f"Category Name =>  {cat['name']} -- Category ID => {cat['id']} ")