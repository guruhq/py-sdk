
import guru

g = guru.Guru()

events = g.get_events(max_pages=1)

for event in events:
  print()
  print(event)

print(len(events), "events")
