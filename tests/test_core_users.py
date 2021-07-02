
import json
import yaml
import unittest
import responses

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
        "emails": "user@example.com",
        "teamMemberType": "CORE"
      }
    }])
  
  @use_guru()
  @responses.activate
  def test_invite_core_user(self, g):
    responses.add(responses.POST, "https://api.getguru.com/api/v1/members/invite", json={})

    g.invite_core_user("user@example.com")

    self.assertEqual(get_calls(), [{
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/members/invite",
      "body": {
        "emails": "user@example.com",
        "teamMemberType": "CORE"
      }
    }])
  
  @use_guru()
  @responses.activate
  def test_invite_light_user(self, g):
    responses.add(responses.POST, "https://api.getguru.com/api/v1/members/invite", json={})

    g.invite_light_user("user@example.com")

    self.assertEqual(get_calls(), [{
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/members/invite",
      "body": {
        "emails": "user@example.com",
        "teamMemberType": "LIGHT"
      }
    }])
  
  @use_guru()
  @responses.activate
  def test_upgrade_light_user(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?search=light%40example.com", json=[{
      "id": "light@example.com",
      "user": {"email": "light@example.com"},
      "userAttributes": {
        "BILLING_TYPE": "FREE",
        "ACCESS_TYPE": "READ_ONLY"
      }
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?search=core%40example.com", json=[{
      "id": "core@example.com",
      "user": {"email": "core@example.com"},
      "userAttributes": {
        "BILLING_TYPE": "CORE",
        "ACCESS_TYPE": "CORE"
      }
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/members/light@example.com/upgrade", json={})
    responses.add(responses.POST, "https://api.getguru.com/api/v1/members/core@example.com/upgrade", json={})

    light_user_result = g.upgrade_light_user("light@example.com")
    core_user_result = g.upgrade_light_user("core@example.com")

    self.assertEqual(light_user_result, True)
    self.assertIsNone(core_user_result)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/members?search=light%40example.com"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/members/light@example.com/upgrade",
      "body": {}
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/members?search=core%40example.com"
    }])
  
  @use_guru()
  @responses.activate
  def test_downgrade_core_user(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?search=core%40example.com", json=[{
      "id": "core@example.com",
      "user": {"email": "core@example.com"},
      "groups": [],
      "userAttributes": {
        "BILLING_TYPE": "CORE",
        "ACCESS_TYPE": "CORE"
      }
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?search=light%40example.com", json=[{
      "id": "light@example.com",
      "user": {"email": "light@example.com"},
      "userAttributes": {
        "BILLING_TYPE": "FREE",
        "ACCESS_TYPE": "READ_ONLY"
      }
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/members/core@example.com/downgrade", json={})
    responses.add(responses.POST, "https://api.getguru.com/api/v1/members/light@example.com/downgrade", json={})

    core_user_result = g.downgrade_core_user("core@example.com")
    light_user_result = g.downgrade_core_user("light@example.com")

    self.assertEqual(core_user_result, True)
    self.assertIsNone(light_user_result)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/members?search=core%40example.com"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/members/core@example.com/downgrade",
      "body": {}
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/members?search=light%40example.com"
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
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?search=user%40example.com", json=[{
      "user": {"email": "user@example.com"},
      "groups": [],
      "userAttributes": {
        "BILLING_TYPE": "CORE",
        "ACCESS_TYPE": "CORE"
      }
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/groups/1234/members")
    responses.add(responses.POST, "https://api.getguru.com/api/v1/groups/5678/members")

    g.invite_user("user@example.com", "Experts", "other group")

    self.assertEqual(get_calls(), [{
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/members/invite",
      "body": {
        "emails": "user@example.com",
        "teamMemberType": "CORE"

      }
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/members?search=user%40example.com"
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
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?search=user%40example.com", json=[{
      "user": {"email": "user@example.com"},
      "groups": [],
      "userAttributes": {
        "BILLING_TYPE": "CORE",
        "ACCESS_TYPE": "CORE"
      }
    }])

    g.invite_user("user@example.com", "other group")

    self.assertEqual(get_calls(), [{
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/members/invite",
      "body": {
        "emails": "user@example.com",
        "teamMemberType": "CORE"
      }
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/members?search=user%40example.com"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }])
  
  @use_guru()
  @responses.activate
  def test_add_user_to_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?search=user%40example.com", json=[{
      "user": {"email": "user@example.com"},
      "groups": [],
      "userAttributes": {
        "BILLING_TYPE": "CORE",
        "ACCESS_TYPE": "CORE"
      }
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1234",
      "name": "Experts"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/groups/1234/members")

    g.add_user_to_group("user@example.com", "Experts")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/members?search=user%40example.com"
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
  def test_add_light_user_to_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?search=user%40example.com", json=[{
      "user": {"email": "user@example.com"},
      "userAttributes": {
        "BILLING_TYPE": "FREE",
        "ACCESS_TYPE": "READ_ONLY"
      }
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1234",
      "name": "Experts"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/groups/1234/members")

    result = g.add_user_to_group("user@example.com", "Experts")
    
    self.assertIsNone(result)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/members?search=user%40example.com"
    }])
    

  @use_guru()
  @responses.activate
  def test_add_user_to_invalid_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?search=user%40example.com", json=[{
      "user": {"email": "user@example.com"},
      "groups": [],
      "userAttributes": {
        "BILLING_TYPE": "CORE",
        "ACCESS_TYPE": "CORE"
      }
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1234",
      "name": "Other Group"
    }])

    g.add_user_to_group("user@example.com", "Experts")

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/members?search=user%40example.com"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }])

  @use_guru()
  @responses.activate
  def test_add_user_to_groups(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?search=user%40example.com", json=[{
      "user": {"email": "user@example.com"},
      "groups": [],
      "userAttributes": {
        "BILLING_TYPE": "CORE",
        "ACCESS_TYPE": "CORE"
      }
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
      "url": "https://api.getguru.com/api/v1/members?search=user%40example.com"
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
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?search=user%40example.com", json=[{
      "user": {"email": "user@example.com"},
      "groups": [],
      "userAttributes": {
        "BILLING_TYPE": "CORE",
        "ACCESS_TYPE": "CORE"
      }
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
      "url": "https://api.getguru.com/api/v1/members?search=user%40example.com"
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
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?search=user%40example.com", json=[{
      "user": {"email": "user@example.com"},
      "groups": [],
      "userAttributes": {
        "BILLING_TYPE": "CORE",
        "ACCESS_TYPE": "CORE"
      }
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
      "url": "https://api.getguru.com/api/v1/members?search=user%40example.com"
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
  def test_add_user_to_groups_with_invalid_user(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?search=invalid%40example.com", json=[])
    result = g.add_user_to_groups("invalid@example.com", "Experts")

    self.assertEqual(result, None)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/members?search=invalid%40example.com"
    }])

  @use_guru()
  @responses.activate
  def test_add_user_to_groups_where_the_user_is_already_in_one_group(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?search=user%40example.com", json=[{
      "user": {"email": "user@example.com"},
      "groups": [{
        "id": "1111",
        "name": "Experts"
      }],
      "userAttributes": {
        "BILLING_TYPE": "CORE",
        "ACCESS_TYPE": "CORE"
      }
    }])
    responses.add(responses.GET, "https://api.getguru.com/api/v1/groups", json=[{
      "id": "1111",
      "name": "Experts"
    }, {
      "id": "2222",
      "name": "other group"
    }])
    responses.add(responses.POST, "https://api.getguru.com/api/v1/groups/2222/members")

    result = g.add_user_to_groups("user@example.com", "Experts", "other group")

    self.assertEqual(result, {
      "Experts": True,
      "other group": True
    })
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/members?search=user%40example.com"
    }, {
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/groups"
    }, {
      "method": "POST",
      "url": "https://api.getguru.com/api/v1/groups/2222/members",
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
  def test_email_validation(self, g):
    invalid_emails = [
      "username",
      "@",
      "a@",
      "abc.def"
    ]
    for email in invalid_emails:
      with self.assertRaises(ValueError):
        g.add_user_to_group(email, "Experts")
      with self.assertRaises(ValueError):
        g.add_user_to_groups(email, "Experts")
      with self.assertRaises(ValueError):
        g.add_users_to_group([email], "Experts")
      with self.assertRaises(ValueError):
        g.remove_user_from_team(email)
      with self.assertRaises(ValueError):
        g.invite_user(email)
      with self.assertRaises(ValueError):
        g.remove_user_from_groups(email, "Experts")
    
    # all of these methods should error before making any API calls.
    self.assertEqual(get_calls(), [])

  @use_guru()
  @responses.activate
  def test_get_members(self, g):
    responses.add(responses.GET, "https://api.getguru.com/api/v1/members?search=", json=[])

    g.get_members()

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/members?search="
    }])
