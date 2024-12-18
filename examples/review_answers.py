#from types import NoneType
import guru

"""
Use this example to retrieve the review Answers that are shown in the AI Training Center

To use this script:
- update <username> to your guru account
- update <apitoken> to the API token generated for your account

This exampple shows how to print out various properties of the Answers and the Sources
associated with them.
"""


# API token info
email = "<username>"
token = "<apitoken>"


g = guru.Guru(email, token, qa=False)

# Get Reviewed Answers - AITC
reviewedAnswers = g.get_reviewed_answers()
for ra in reviewedAnswers:
    print(f"Question: {ra.question}")
    print(f"--Status: {ra.status}")
    print(f"--Agent: {ra.knowledge_agent}")
    for s in ra.sources:
       print(f"--Document Type: {s.document_type}")
       print(f"--Definition Type: {s.definition_type}")