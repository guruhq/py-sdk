import guru

g = guru.Guru("ahojnowski+demo@getguru.com","3fc2aa39-592f-401f-b553-b3a99a3a7bcd")

categories = g.get_tag_category_names("help")
g.get_tag_category()
print (categories)