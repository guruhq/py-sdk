import guru
import re


# API token info
email = "<username>"
token = "<apitoken>"
test_collid = "<collectionId>"

# RegEx pattern to get Slug
pattern = r'^([^/]+)'

# Function to recursively dump out folders hierarchy
def print_folder_hierarchy(folder, parent_chain=None):
    if parent_chain is None:
        parent_chain = []

    # Add the current folder's title to the chain
    current_chain = parent_chain + [folder.title]

    # Print the current folder hierarchy
    print(" > ".join(current_chain))

    # Recursively process any subfolders this folder has
    # Assuming folder.folders returns a tuple of subfolder objects
    for subfolder in folder.folders:
        print_folder_hierarchy(subfolder, current_chain)

# Create the Guru object
g = guru.Guru(email, token, silent=True, qa=False)

# Get the Collection
col = g.get_collection(test_collid)

# Get the collections slug
match = re.match(pattern, col.homeFolderSlug)
if match:
    slug = match.group(1)

# Get the homefolder for the collection
homefolder = g.get_folder(slug)

#  Get folders in the home folder
folders = homefolder.folders

# recursively call the print_folder_hierarchy to process the folers
for folder in folders:
    print_folder_hierarchy(folder)