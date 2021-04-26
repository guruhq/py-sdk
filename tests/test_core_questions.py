
import json
import yaml
import unittest
import responses

from tests.util import use_guru, get_calls

import guru


class TestCore(unittest.TestCase):
  @use_guru()
  @responses.activate
  def test_get_questions_inbox(self, g):
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/tasks/questions?filter=INBOX", json=[{
      "answerer": {
        "type": "user",
        "user": {
          "email": "jchappelle@getguru.com",
        }
      },
      "answerable": True,
      "archivable": False,
      "asker": {
        "email": "rmiller@getguru.com"
      },
      "id": "1111",
      "question": "did this work?",
      "createdDate": "2019-09-19T19:36:49.504+0000",
      "lastActivityDate": "2019-09-19T19:36:49.764+0000",
      "lastActivityType": "ASK",
      "lastActivityUser": {
        "email": "rmiller@getguru.com"
      }
    }])

    questions = g.get_questions_inbox()
    self.assertEqual(len(questions), 1)

    question = questions[0]
    self.assertEqual(question.answerer.user.email, "jchappelle@getguru.com")
    self.assertEqual(question.asker.email, "rmiller@getguru.com")
    self.assertEqual(question.answerable, True)
    self.assertEqual(question.archivable, False)

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/tasks/questions?filter=INBOX"
    }])

  @use_guru()
  @responses.activate
  def test_get_questions_sent(self, g):
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/tasks/questions?filter=SENT", json=[])

    # the test that gets your inbox checks that we parse questions
    # and return the correct response, so this test just needs to
    # check that we correctly pass filter=SENT for this call.
    g.get_questions_sent()

    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://api.getguru.com/api/v1/tasks/questions?filter=SENT"
    }])