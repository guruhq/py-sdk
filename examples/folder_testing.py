from types import NoneType
import guru

# call script with the credentials of the user you want to use
# ex: GURU_USER=user@example.com GURU_TOKEN=abcd1234-abcd-abcd-abcd-abcdabcdabcd python getCardExport.py

""" 
email = "someperson@yourcompany.com"
token = "yourapitokengoeshere" 


#test collection id
test_collid = "your collection id here"
test_homeslug = "your homeslug here"
test_folderid = "your folder slug here"
"""


g = guru.Guru(email, token, qa=True)

""" # get folders for a collection
print("#########  Folders stuff #########")
collectionFolders = g.get_folders(test_collid)
print("# of folders: %s" % len(collectionFolders))
for colFolder in collectionFolders:
  print("collection Folder: %s" % colFolder.title)

# get a folder now...
print("#########  Folder stuff #########")
folder = g.get_folder(test_folderid)
print("folder name: %s" % folder)

# iterate thru the folders
for subfolder in folder.folders:
  print("sub folder name: %s" % subfolder.title)
  # Ok, now see if lazy loading of the folders work, not explicity calling get_items, that is handled undder the .folders and .cards methods of the Folder object.
  # subfolder.get_items()

  for subsubfolder in subfolder.folders:
    print("sub-sub-folder name: %s" % subsubfolder.title)

# get a non-existent folder now...
print("#########  Non-Existent Folder stuff #########")
nonfolder = g.get_folder("ThisFolderSlugDoesntExist")
if nonfolder == None:
  print("folder does not exist!!!")

print("#########  Cards #########")
for card in folder.cards:
  print("card name: %s" % card.title)

print("#########  All Items #########")
for item in folder.items:
  print("folder items: %s" % item.title) """


print("########  Add a Folder to a Collection ######")
addFolder = g.add_folder(
    "Add Folder Folder", test_otherCollSlug, test_addfolderTitle)
print("add folder title: %s" % addFolder.title)
