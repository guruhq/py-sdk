
import json
import yaml
import unittest
import responses

from tests.util import use_guru, get_calls

import guru


class TestCore(unittest.TestCase):
  @use_guru()
  @responses.activate
  def test_delete_knowledge_trigger(self, g):
    # register the response for the API call we'll make.
    responses.add(responses.DELETE, "https://api.getguru.com/api/v1/newcontexts/1111", status=204)

    result = g.delete_knowledge_trigger("1111")
    
    self.assertEqual(get_calls(), [{
      "method": "DELETE",
      "url": "https://api.getguru.com/api/v1/newcontexts/1111"
    }])

  