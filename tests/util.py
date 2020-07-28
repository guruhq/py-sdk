
import json
import responses

import guru


def use_guru(username="user@example.com", api_token="abcdabcd-abcd-abcd-abcd-abcdabcdabcd", silent=True, dry_run=False):
  def wrapper(func):
    def call_func(self):
      g = guru.Guru(username, api_token, silent=silent, dry_run=dry_run)
      func(self, g)
    return call_func
  return wrapper

def get_calls():
  calls = []
  for call in responses.calls:
    c = {
      "method": call.request.method,
      "url": call.request.url
    }
    if call.request.method != "GET" and call.request.body:
      try:
        c["body"] = json.loads(call.request.body)
      except:
        c["body"] = call.request.body
    calls.append(c)
  return calls
