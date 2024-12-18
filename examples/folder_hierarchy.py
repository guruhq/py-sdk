import guru
import re
import csv
import os

"""
Use this example to generate a collection's folder hierarchy to a csv file

To use this script:
- update <username> to your guru account
- update <apitoken> to the API token generated for your account
- update <collectionid> to the collection's name, slug or id

The output is written to a CSV file. If no path is specified, the default name is:
<collectionName>_folder_hierarchy.csv in the scripts working directory.  An example of setting
a path is shown below

"""


# API token info
email = "<username>"
token = "<apitoken>"
# update with collection name, slug or id.
targetCollection = "<collectionid>"

# RegEx pattern to get Slug
pattern = r'^([^/]+)'

# Write out the folder hierarchy to a csv file
def write_folder_hierarchy(homefolder, path=None):
    # If no path is provided, default to <collectionName>_folder_hierarchy.csv"
    if path is None:
        path = f"{homefolder.title}_folder_hierarchy.csv"
    
    with open(path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)

        # traverse the folder structure
        for folder in homefolder.folders:
            print_folder_hierarchy(folder, writer)

# recursively call this function to process all folders/sub-folders
def print_folder_hierarchy(folder, writer, parent_chain=None):
    if parent_chain is None:
        parent_chain = []

    current_chain = parent_chain + [folder.title]
    writer.writerow(current_chain)

    for subfolder in folder.folders:
        print_folder_hierarchy(subfolder, writer, current_chain)

# Create the Guru object
g = guru.Guru(email, token, silent=True, qa=False)

# Get the Collection
col = g.get_collection(targetCollection)

# Get the collections slug
match = re.match(pattern, col.homeFolderSlug)
if match:
    slug = match.group(1)
    # Get the homefolder for the collection
    homefolder = g.get_folder(slug)
    # Write out the file.
    write_folder_hierarchy(homefolder)
    # OPTION to write a specified path example:
    # write_folder_hierarchy(homefolder, path=os.path.expanduser("~/Downloads/folder_hierarchy.csv"))
else:
    print(f"could not find a home folder slug for collection: {col.name}")