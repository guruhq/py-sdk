import unittest
import responses

from tests.util import use_guru, get_calls

import guru


class TestCore(unittest.TestCase):
  @use_guru()
  @responses.activate
  def test_get_webhooks(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/webhooks", json=[{
      "owner": {
        "status": "ACTIVE",
        "email": "beth@getguru.com",
        "firstName": "beth",
        "lastName": "jones",
        "profilePicUrl": "https://lh3.googleusercontent.com/a-/beth"
    },
    "filter": "card-to-pdf",
    "id": "2222",
    "status": "ENABLED",
    "deliveryMode": "BATCH",
    "dateCreated": "2021-05-10T17:05:32.245+0000",
    "team": {
        "id": "17724bbf-b6b2-4f78-b3db-91188cac3444",
        "status": "ACTIVE",
        "dateCreated": "2019-11-05T18:48:38.821+0000",
        "profilePicUrl": "https://assets.getguru.com/default-team-logo.png",
        "name": "TestImageTeam"
    },
    "dateLastModified": "2021-05-10T17:05:32.245+0000",
    "targetUrl": "https://someotherserver.com/"
    }])

    webhooks = g.get_webhooks()

    self.assertEqual(webhooks[0].id, "2222")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/webhooks",
    }])


  @use_guru()
  @responses.activate
  def test_get_webhook(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/webhooks/1111", json={
      "owner": {
        "status": "ACTIVE",
        "email": "bob@getguru.com",
        "firstName": "bob",
        "lastName": "smith",
        "profilePicUrl": "https://lh3.googleusercontent.com/a-/bob"
    },
    "filter": "card-created",
    "id": "1111",
    "status": "ENABLED",
    "deliveryMode": "BATCH",
    "dateCreated": "2021-05-10T17:05:32.245+0000",
    "team": {
        "id": "17724bbf-b6b2-4f78-b3db-91188cac3444",
        "status": "ACTIVE",
        "dateCreated": "2019-11-05T18:48:38.821+0000",
        "profilePicUrl": "https://assets.getguru.com/default-team-logo.png",
        "name": "TestImageTeam"
    },
    "dateLastModified": "2021-05-10T17:05:32.245+0000",
    "targetUrl": "https://someserver.com/"
    })

    webhook = g.get_webhook("1111")

    self.assertEqual(webhook.id, "1111")
    
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/webhooks/1111"
    }])
  
  @use_guru()
  @responses.activate
  def test_delete_webhook(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/webhooks/1111", status=200, json=[{
      "owner": {
        "status": "ACTIVE",
        "email": "bob@getguru.com",
        "firstName": "bob",
        "lastName": "smith",
        "profilePicUrl": "https://lh3.googleusercontent.com/a-/bob"
    },
    "filter": "card-created",
    "id": "1111",
    "status": "ENABLED",
    "deliveryMode": "BATCH",
    "dateCreated": "2021-05-10T17:05:32.245+0000",
    "team": {
        "id": "17724bbf-b6b2-4f78-b3db-91188cac3444",
        "status": "ACTIVE",
        "dateCreated": "2019-11-05T18:48:38.821+0000",
        "profilePicUrl": "https://assets.getguru.com/default-team-logo.png",
        "name": "TestImageTeam"
    },
    "dateLastModified": "2021-05-10T17:05:32.245+0000",
    "targetUrl": "https://someserver.com/"
    }])
    responses.add(responses.DELETE, "https://api.getguru.com/api/v1/webhooks/1111")

    delete_status = g.delete_webhook("1111")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/webhooks/1111"
    },{
      "method": "DELETE",
      "url": "https://api.getguru.com/api/v1/webhooks/1111",
    }])

  @use_guru()
  @responses.activate
  def test_create_webhook(self, g):
    responses.add(responses.POST, "https://api.getguru.com/api/v1/webhooks", json={
      "owner": {
        "status": "ACTIVE",
        "email": "bob@getguru.com",
        "firstName": "bob",
        "lastName": "smith",
        "profilePicUrl": "https://lh3.googleusercontent.com/a-/bob"
      },
      "filter": "card-created,card-to-pdf",
      "id": "1111",
      "status": "ENABLED",
      "deliveryMode": "BATCH",
      "dateCreated": "2021-05-10T17:05:32.245+0000",
      "team": {
          "id": "17724bbf-b6b2-4f78-b3db-91188cac3444",
          "status": "ACTIVE",
          "dateCreated": "2019-11-05T18:48:38.821+0000",
          "profilePicUrl": "https://assets.getguru.com/default-team-logo.png",
          "name": "TestImageTeam"
      },
      "dateLastModified": "2021-05-10T17:05:32.245+0000",
      "targetUrl": "https://someserver.com"
    })

    result = g.create_webhook("https://someserver.com", "card-created,card-to-pdf")

    self.assertEqual(result.target_url, "https://someserver.com")
    self.assertEqual(get_calls(), [{
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/webhooks",
      "body": {
        "deliveryMode": "BATCH",
        "targetUrl": "https://someserver.com",
        "status": "ENABLED",
        "filter": "card-created,card-to-pdf"
      }
    }])