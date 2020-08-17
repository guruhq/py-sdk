
import json
import yaml
import unittest
import responses

from unittest.mock import Mock, patch
from requests.auth import HTTPBasicAuth

from tests.util import use_guru, get_calls

import guru


class TestCore(unittest.TestCase):
  @use_guru()
  @responses.activate
  def test_invite_user(self, g):
    responses.add(responses.POST, "https://api.getguru.com/api/v1/members/invite", json={})

    g.invite_user("user@example.com")

    self.assertEqual(get_calls(), [{
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/members/invite",
      "body": {
        "emails": "user@example.com"
      }
    }])
  
  @use_guru()
  @responses.activate
  def test_invite_user_and_add_to_groups(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1234",
      "name": "Experts"
    }, {
      "id": "5678",
      "name": "other group"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/members/invite", json={})
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?search=user@example.com", json=[{
      "user": {"email": "user@example.com"},
      "groups": []
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/groups/1234/members")
    responses.add(responses.POST, "https://api.getguru.com/api/v1/groups/5678/members")

    g.invite_user("user@example.com", "Experts", "other group")

    self.assertEqual(get_calls(), [{
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/members/invite",
      "body": {
        "emails": "user@example.com"
      }
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/members?search=user@example.com"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/groups/1234/members",
      "body": [
        "user@example.com"
      ]
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/groups/5678/members",
      "body": [
        "user@example.com"
      ]
    }])

  @use_guru()
  @responses.activate
  def test_invite_user_to_invalid_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1234",
      "name": "Experts"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/members/invite", json={})
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?search=user@example.com", json=[{
      "user": {"email": "user@example.com"},
      "groups": []
    }])

    g.invite_user("user@example.com", "other group")

    self.assertEqual(get_calls(), [{
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/members/invite",
      "body": {
        "emails": "user@example.com"
      }
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/members?search=user@example.com"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }])
  
  @use_guru()
  @responses.activate
  def test_add_user_to_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?search=user@example.com", json=[{
      "user": {"email": "user@example.com"},
      "groups": []
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1234",
      "name": "Experts"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/groups/1234/members")

    g.add_user_to_group("user@example.com", "Experts")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/members?search=user@example.com"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/groups/1234/members",
      "body": [
        "user@example.com"
      ]
    }])

  @use_guru()
  @responses.activate
  def test_add_user_to_invalid_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?search=user@example.com", json=[{
      "user": {"email": "user@example.com"},
      "groups": []
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1234",
      "name": "Other Group"
    }])

    g.add_user_to_group("user@example.com", "Experts")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/members?search=user@example.com"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }])

  @use_guru()
  @responses.activate
  def test_add_user_to_groups(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?search=user@example.com", json=[{
      "user": {"email": "user@example.com"},
      "groups": []
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1234",
      "name": "Experts"
    }, {
      "id": "5678",
      "name": "other group"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/groups/1234/members")
    responses.add(responses.POST, "https://api.getguru.com/api/v1/groups/5678/members")

    g.add_user_to_groups("user@example.com", "Experts", "other group")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/members?search=user@example.com"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/groups/1234/members",
      "body": [
        "user@example.com"
      ]
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/groups/5678/members",
      "body": [
        "user@example.com"
      ]
    }])

  @use_guru()
  @responses.activate
  def test_add_user_to_groups_where_first_one_is_invalid(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?search=user@example.com", json=[{
      "user": {"email": "user@example.com"},
      "groups": []
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "5678",
      "name": "other group"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/groups/5678/members")

    result = g.add_user_to_groups("user@example.com", "Experts", "other group")

    self.assertEqual(result, {
      "Experts": False,
      "other group": True
    })

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/members?search=user@example.com"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/groups/5678/members",
      "body": [
        "user@example.com"
      ]
    }])

  @use_guru()
  @responses.activate
  def test_add_user_to_groups_where_second_one_is_invalid(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?search=user@example.com", json=[{
      "user": {"email": "user@example.com"},
      "groups": []
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1234",
      "name": "Experts"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/groups/1234/members")

    result = g.add_user_to_groups("user@example.com", "Experts", "other group")

    self.assertEqual(result, {
      "Experts": True,
      "other group": False
    })

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/members?search=user@example.com"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/groups/1234/members",
      "body": [
        "user@example.com"
      ]
    }])
  
  @use_guru()
  @responses.activate
  def test_add_users_to_group(self, g):
    users = [
      "user1@example.com",
      "user2@example.com",
      "user3@example.com"
    ]
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1234",
      "name": "Experts"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/groups/1234/members", json=[
      {"id": email} for email in users
    ])

    results = g.add_users_to_group(users, "Experts")

    self.assertEqual(results, {
      email: True for email in users
    })
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/groups/1234/members",
      "body": users
    }])

  @use_guru()
  @responses.activate
  def test_add_users_to_invalid_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[])
    
    g.add_users_to_group([], "Experts")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }])
  
  @use_guru()
  @responses.activate
  def test_add_users_to_group_with_multiple_batches(self, g):
    users = ["user%s@example.com" % i for i in range(110)]
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1234",
      "name": "Experts"
    }])

    # make the call for the first page work and the second call fail.
    responses.add(responses.POST, "https://api.getguru.com/api/v1/groups/1234/members", json=[
      {"id": email} for email in users[0:100]
    ], status=200)
    responses.add(responses.POST, "https://api.getguru.com/api/v1/groups/1234/members", status=400)

    results = g.add_users_to_group(users, "Experts")

    # users 0..99 succeeded, 100..109 didn't.
    for i in range(110):
      self.assertEqual(results["user%s@example.com" % i], i < 100)
    
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/groups/1234/members",
      "body": users[0:100]
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/groups/1234/members",
      "body": users[100:]
    },
    # trying again with a batch size of 2
    {"method": "POST", "url": "https://api.getguru.com/api/v1/groups/1234/members", "body": users[100:102]},
    {"method": "POST", "url": "https://api.getguru.com/api/v1/groups/1234/members", "body": users[102:104]},
    {"method": "POST", "url": "https://api.getguru.com/api/v1/groups/1234/members", "body": users[104:106]},
    {"method": "POST", "url": "https://api.getguru.com/api/v1/groups/1234/members", "body": users[106:108]},
    {"method": "POST", "url": "https://api.getguru.com/api/v1/groups/1234/members", "body": users[108:110]},
    # trying again with a batch size of 1.
    {"method": "POST", "url": "https://api.getguru.com/api/v1/groups/1234/members", "body": [users[100]]},
    {"method": "POST", "url": "https://api.getguru.com/api/v1/groups/1234/members", "body": [users[101]]},
    {"method": "POST", "url": "https://api.getguru.com/api/v1/groups/1234/members", "body": [users[102]]},
    {"method": "POST", "url": "https://api.getguru.com/api/v1/groups/1234/members", "body": [users[103]]},
    {"method": "POST", "url": "https://api.getguru.com/api/v1/groups/1234/members", "body": [users[104]]},
    {"method": "POST", "url": "https://api.getguru.com/api/v1/groups/1234/members", "body": [users[105]]},
    {"method": "POST", "url": "https://api.getguru.com/api/v1/groups/1234/members", "body": [users[106]]},
    {"method": "POST", "url": "https://api.getguru.com/api/v1/groups/1234/members", "body": [users[107]]},
    {"method": "POST", "url": "https://api.getguru.com/api/v1/groups/1234/members", "body": [users[108]]},
    {"method": "POST", "url": "https://api.getguru.com/api/v1/groups/1234/members", "body": [users[109]]},
    ])

  @use_guru()
  @responses.activate
  def test_remove_user_from_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1234",
      "name": "Experts"
    }])
    responses.add(responses.DELETE, "https://api.getguru.com/api/v1/groups/1234/members/user@example.com")

    g.remove_user_from_group("user@example.com", "Experts")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "DELETE",
      "url": "https://api.getguru.com/api/v1/groups/1234/members/user@example.com"
    }])
  
  @use_guru()
  @responses.activate
  def test_remove_user_from_groups(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1234",
      "name": "Experts"
    }, {
      "id": "5678",
      "name": "other group"
    }])
    responses.add(responses.DELETE, "https://api.getguru.com/api/v1/groups/1234/members/user@example.com")
    responses.add(responses.DELETE, "https://api.getguru.com/api/v1/groups/5678/members/user@example.com")

    result = g.remove_user_from_groups("user@example.com", "Experts", "other group")

    self.assertEqual(result, {
      "Experts": True,
      "other group": True
    })
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "DELETE",
      "url": "https://api.getguru.com/api/v1/groups/1234/members/user@example.com"
    }, {
      "method": "DELETE",
      "url": "https://api.getguru.com/api/v1/groups/5678/members/user@example.com"
    }])
  
  @use_guru()
  @responses.activate
  def test_remove_user_from_groups_with_invalid_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1234",
      "name": "Experts"
    }])
    responses.add(responses.DELETE, "https://api.getguru.com/api/v1/groups/1234/members/user@example.com")

    result = g.remove_user_from_groups("user@example.com", "Experts", "other group")

    self.assertEqual(result, {
      "Experts": True,
      "other group": False
    })
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "DELETE",
      "url": "https://api.getguru.com/api/v1/groups/1234/members/user@example.com"
    }])

  @use_guru()
  @responses.activate
  def test_remove_user_from_team(self, g):
    responses.add(responses.DELETE, "https://api.getguru.com/api/v1/members/user@example.com/replaceverifier")

    g.remove_user_from_team("user@example.com")

    self.assertEqual(get_calls(), [{
      "method": "DELETE",
      "url": "https://api.getguru.com/api/v1/members/user@example.com/replaceverifier",
      "body": {
        "collectionVerifiers": {}
      }
    }])

  @use_guru()
  @responses.activate
  def test_get_members(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?search=", json=[])

    g.get_members()

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/members?search="
    }])
