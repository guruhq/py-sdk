import guru

g = guru.Guru(dry_run=False)

# make a new webhook.
g.create_webhook("https://someserver.com", "card-created,card-updated")

# get webhooks.
list_of_webhooks = g.get_webhooks()
# get webhook by ID
webhook_at_someserver = next((webhook for webhook in list_of_webhooks if webhook["target_url"] == "https://someserver.com"), None)
individual_webhook = g.get_webhook(webhook_at_someserver.id)

# delete the webhook.
g.delete_webhook(individual_webhook.id)

