import guru

# call script with the credentials of the user you want to use
# ex: GURU_USER=user@example.com GURU_TOKEN=abcd1234-abcd-abcd-abcd-abcdabcdabcd python getCardExport.py
email = "mhornak@getguru.com"
token = "0ab65098-43df-42d6-9d22-bf4117f6b163"

g = guru.Guru(email, token, qa=True)

g.get_folder()

for folder in g.get_folders(collection="786f6fc8-413b-418d-ba9b-fba974192401"):
  print("Id: %s --> %s" % (folder.id, folder.title))

folder = get_folder("iGqxqEgT/413-Testing")
