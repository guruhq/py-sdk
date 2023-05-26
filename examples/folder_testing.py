from types import NoneType
import guru

# call script with the credentials of the user you want to use
# ex: GURU_USER=user@example.com GURU_TOKEN=abcd1234-abcd-abcd-abcd-abcdabcdabcd python getCardExport.py


# API token info
email = "someperson@yourcompany.com"
token = "yourapitokengoeshere"

# test collection id
test_collid = "your collection id here"
test_homeslug = "your homeslug here"
test_folderid = "your folder slug here"
test_collSlug = "your collection slug here"
test_parentFolder = "parent folder slug here"
test_cardId = "card Id to use for Testing"
test_deleteFolderId = "delete folder id here"
test_cardId = "card Id to use for Testing"
test_cardItemId = "card itemID for moving a card"
test_targetFolderId = "folderId for move/add card"
test_sourceFolderId = "folderId for move/add card"
test_invalidFolderId = "#$NoBueno!~"
test_doesNotExistFolderId = "BadSlug"
test_cardNotInFolderId = "cardId not in target folder"


g = guru.Guru(email, token, qa=True)


# get folders for a collection
# print("#########  Folders stuff #########")
# collectionFolders = g.get_folders(test_collid)
# print("# of folders: %s" % len(collectionFolders))
# for colFolder in collectionFolders:
#   print("collection Folder: %s" % colFolder.title)

# get a folder now...
print("#########  Folder stuff #########")
folder = g.get_folder(test_folderid)
print("folder name: %s" % folder)

# iterate thru the folders
# for subfolder in folder.folders:
#   print("sub folder name: %s" % subfolder.title)
#   # Ok, now see if lazy loading of the folders work, not explicity calling get_items, that is handled undder the .folders and .cards methods of the Folder object.
#   # subfolder.get_items()

#   for subsubfolder in subfolder.folders:
#     print("sub-sub-folder name: %s" % subsubfolder.title)

# get a non-existent folder now...
# print("#########  Non-Existent Folder stuff #########")
# nonfolder = g.get_folder("ThisFolderSlugDoesntExist")
# if nonfolder == None:
#   print("folder does not exist!!!")

# print("#########  Cards #########")
# for card in folder.cards:
#   print("card name: %s" % card.title)

# print("#########  All Items #########")
# for item in folder.items:
#   print("folder items: %s" % item.title)

# print("########  Add a Folder Test #1 add folder to top of Collection ######")
# addFolder = g.add_folder(
#     "folder top of collection", test_collSlug)
# print("add folder top of Collection - Title: %s" % addFolder.title)

# print("########  Add a Folder Test #2 add folder to another folder in the collection")
# addFolder = g.add_folder(
#     "folder in another folder 1", test_collSlug, parentFolder=test_parentFolder)
# print("add folder top of Collection - Title: %s" % addFolder.title)

# print("########  Add a Folder Test #3 add folder 2 folder, verify first")
# addFolder = g.add_folder(
#     "folder in another folder - first", test_collSlug, parentFolder=test_parentFolder)
# print("add folder in folder, make sure it's still first - Title: %s" %
#       addFolder.title)

# print("########  Add a Card to a Folder Testing... ##########")
# updatedFolder = g.add_card_to_folder(test_cardId, test_folderid)
# print(f"Card title: {updatedFolder}")

# print("########  Delete a Folder Test #1 using UUID, Slug, Object and Name")
# response = g.delete_folder(test_deleteFolderId)
# print("Delete worked? : %s" % response)

# get Card, Source and Target objects to test add/move cards w/objects..
# card = g.get_card(test_cardId)
# print(f"card name: {card.title}")

# source_folder = g.get_folder(test_sourceFolderId)
# print(f"folder name: {source_folder.title}")

# target_folder = g.get_folder(test_targetFolderId)
# print(f"target folder nane: {target_folder.title}")

# print("######## Remove a Card from a Folder ##########")
# response = g.remove_card_from_folder(test_cardNotInFolderId, target_folder)
# print(f"Response: {response}")

# print("######## Remove a Card from a Folder using Folder helper ##########")

# response = source_folder.remove_card(card)
# print(f"Response: {response}")


# move a card from one folder to another, needs card, source and target folders
# response = g.move_card_to_folder(
#     card, source_folder, target_folder)
# print(response)
# add an existing card to a folder, need card and target folder

# response = g.add_card_to_folder(test_cardId, test_targetFolderId)

# for x in source_folder.cards:
#   print(f"source card title: {x.title}")

# for c in target_folder.cards:
#   print(f"target card title: {c.title}")


# # add an existing card to a folder, need card and target folder
# response = g.add_card_to_folder(test_cardId, test_targetFolderId)

# # move a card using the Folder object's .move_card() method
# response = source_folder.move_card(card, target_folder)

# # add a card using the Folder object's .add_card() method
# response = source_folder.add_card(card)

# move folder to another collection
# response = folder.move_to_collection(test_collid)

response = folder.add_group("Third Folder Group")
print(response)

folder_perms = folder.get_groups()
for pg in folder_perms:
  print(f"Perm: {pg.group.name}")

response = folder.remove_group("Third Folder Group")
print(response)

folder_perms = folder.get_groups()
for pg in folder_perms:
  print(f"Perm: {pg.group.name}")
