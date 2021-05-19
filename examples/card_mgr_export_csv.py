import guru
import csv

# call script with the credentials of the user you want to use 
# ex: GURU_USER=user@example.com GURU_TOKEN=abcd1234-abcd-abcd-abcd-abcdabcdabcd python getCardExport.py
email = "user@example.com"
token = "abcd1234-abcd-abcd-abcd-abcdabcdabcd"

g_user = guru.Guru(email, token) 
collection = "General" 
all_cards = []

EXPORT_FOLDER_PATH = "/tmp/" # replace with the folder you want the export to go
TEAM = "Most Informative Knowledge" # edit this line with the team name

def write_csv(filename, coll):
    labels = ["Title","Content","ID","Boards","Tags","Date Created","Created By","Last Modified","Last Modified By","Last Verified","Last Verified By","Verifier","Views","Copies","Favorites","Trust State","Verification Interval","Collection","Link"]
    with open(filename, "w") as file_out:
      csv_out = csv.writer(file_out)
      csv_out.writerow(labels)
      for card in g_user.find_cards(collection=coll):
        row = []
        row.append(card.title)
        row.append(card.content)
        row.append(card.id)
        row.append(", ".join([b.title for b in card.boards]) if card.boards else None)
        row.append(", ".join([t.value for t in card.tags]) if card.tags else None)
        row.append(card.created_date)
        row.append(card.original_owner.full_name)
        row.append(card.last_modified_date)
        row.append(card.last_modified_by.full_name)
        row.append(card.last_verified_date)
        row.append(card.last_verified_by.full_name)
        row.append(card.verifier_label)
        row.append(card.views)
        row.append(card.copies)
        row.append(card.favorites)
        row.append(card.verification_state)
        row.append(card.interval_label)
        row.append(card.collection.title)
        row.append(card.url)

        csv_out.writerow(row)

write_csv(EXPORT_FOLDER_PATH + "export_%s.csv" % TEAM, collection)