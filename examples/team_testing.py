#from types import NoneType
import guru

# API token info
email = "<username>"
token = "<apitoken>"


g = guru.Guru(email, token, qa=True)

# Get all teams you have access to
team_stats = g.get_team_stats
print(team_stats)

