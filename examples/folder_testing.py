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
email = "mhornak@getguru.com"
token = "0ab65098-43df-42d6-9d22-bf4117f6b163"
test_collid = "786f6fc8-413b-418d-ba9b-fba974192401"
test_homeslug = "iGqxqEgT"
test_folderid = "TEqxqbac"
test_collSlug = "88p0n1"
test_otherCollSlug = "dx7vjz"
test_addfolderSlug = "TKa7z7Bc"
test_addfolderTitle = "Another Folder"
test_delFolderSlug = "iR8n8KyT"

g = guru.Guru(email, token, qa=True)

""" 
# get folders for a collection
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
  print("folder items: %s" % item.title)
 """
booDel = g.delete_folder(test_delFolderSlug)
print(f"delete folder status: {booDel}")
