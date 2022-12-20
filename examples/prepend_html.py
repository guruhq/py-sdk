import guru
import os

# this script loops through all cards within a collection and 
# prepends specific HTML to the beginning of each card, if it doesn't already exist

g = guru.Guru("{username@email.com}","{guruApiToken}")
# set up the script to run for all cards within a specific collection

cards = g.find_cards(collection="{collectionName}")
print(len(cards), "cards")

# a good way to figure out what HTML you need in the variable below is to 
# create a card in Guru's UI to display exactly how you want it, then call 
# our /cards API endpoint and look at the "content" field, which will give you the HTML​
PREPEND_HTML = """{insertHTMLtoAppendHere}"""

for card in cards:
  update = False

  if PREPEND_HTML not in card.content:
    card.content = PREPEND_HTML + card.content
    update = True

  if update:
    #uncomment the line below to actually execute this script
    #card.patch()
    print(card.url)