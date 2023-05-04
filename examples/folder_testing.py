import guru

# call script with the credentials of the user you want to use
# ex: GURU_USER=user@example.com GURU_TOKEN=abcd1234-abcd-abcd-abcd-abcdabcdabcd python getCardExport.py

""" 
email = "someperson@yourcompany.com"
token = "yourapitokengoeshere" 
"""


g = guru.Guru(email, token, qa=True)

folder = g.get_folder("TEqxqbac")
print("folder name: %s" % folder.title)
print("folder has_items(): %s" % folder.has_items)

# iterate thru the folders
for subfolder in folder.folders:
  print("sub folder name: %s" % subfolder.title)
  # Ok, now see if lazy loading of the folders work, not explicity calling get_items, that is handled undder the .folders and .cards methods of the Folder object.
  # subfolder.get_items()
  print("subfolder has_items(): %s" % subfolder.has_items)

  for subsubfolder in subfolder.folders:
    print("subfolder has_items(): %s" % subfolder.has_items)
    print("sub-sub-folder name: %s" % subsubfolder.title)

for card in folder.cards:
  print("card name: %s" % card.title)
