import guru
import re
import csv
import os


# API token info
email = "<username>"
token = "<apitoken>"
# update with collection name, slug or id.
targetCollection = "<collectionid>"

# RegEx pattern to get Slug
pattern = r'^([^/]+)'

# Function to recursively dump out folders hierarchy
def write_folder_hierarchy(homefolder, path=None):
    # If no path is provided, default to <collectionName>_folder_hierarchy.csv"
    if path is None:
        path = f"{homefolder.title}_folder_hierarchy.csv"
    
    with open(path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)

        # Call a recursive function that writes each folder's hierarchy
        for folder in homefolder.folders:
            print_folder_hierarchy(folder, writer)

def print_folder_hierarchy(folder, writer, parent_chain=None):
    if parent_chain is None:
        parent_chain = []

    current_chain = parent_chain + [folder.title]
    writer.writerow(current_chain)

    for subfolder in folder.folders:
        print_folder_hierarchy(subfolder, writer, current_chain)

# Create the Guru object
g = guru.Guru(email, token, silent=True, qa=True)

# Get the Collection
col = g.get_collection(targetCollection)

# Get the collections slug
match = re.match(pattern, col.homeFolderSlug)
if match:
    slug = match.group(1)

# Get the homefolder for the collection
homefolder = g.get_folder(slug)

# Write out the file. Note: optional path to directory or choice
write_folder_hierarchy(homefolder)
# write_folder_hierarchy(homefolder, path=os.path.expanduser("~/Downloads/folder_hierarchy.csv"))