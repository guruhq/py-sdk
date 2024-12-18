#from types import NoneType
import guru

# API token info
email = "<username>"
token = "<apitoken>"


g = guru.Guru(email, token, qa=False)

# Get all teams you have access to
team_stats = g.get_team_stats()
print(f"card count: {team_stats.card_count}")
print(f"verification count: {team_stats.needs_verification_count}")