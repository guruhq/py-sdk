#from types import NoneType
import guru

"""
Use this example to retrieve the Team Stats for the team the API token was generated for

To use this script:
- update <username> to your guru account
- update <apitoken> to the API token generated for your account

In this example the stats are printed out.

"""


# API token info
email = "<username>"
token = "<apitoken>"


g = guru.Guru(email, token, qa=False)

# Get stats for your current team.
team_stats = g.get_team_stats()
print(f"card count: {team_stats.card_count}")
print(f"verification count: {team_stats.needs_verification_count}")