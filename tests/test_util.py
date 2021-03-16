
import json
import yaml
import unittest
import responses

import guru

def read_html(filename):
  with open(filename) as file_in:
    return file_in.read()

def get_calls():
  calls = []
  for call in responses.calls:
    c = {
      "method": call.request.method,
      "url": call.request.url
    }
    calls.append(c)
  return calls

class TestUtil(unittest.TestCase):
  @responses.activate
  def test_load_html(self):
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://www.example.com/test/index.html", body="""<p>
  <a href="../page.html">link</a>
  <img src="test.png" />
</p>""")

    doc = guru.load_html("https://www.example.com/test/index.html")
    self.assertEqual(doc.find("a").attrs["href"], "https://www.example.com/page.html")
    self.assertEqual(doc.find("img").attrs["src"], "https://www.example.com/test/test.png")

    # load it again with caching and assert that we still only made one call.
    guru.load_html("https://www.example.com/test/index.html", cache=True)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://www.example.com/test/index.html"
    }])

  @responses.activate
  def test_load_html_with_local_file(self):
    doc = guru.load_html("./tests/test_sync_with_local_files_node1.html")
    self.assertEqual(doc.find("img").attrs["src"], "tests/test_sync_with_local_files_test.png")

  @responses.activate
  def test_download_file(self):
    html = "<p>test</p>"
    responses.add(responses.GET, "https://www.example.com/example.html", body=html)
    guru.download_file("https://www.example.com/example.html", "./tests/example.html")
    self.assertEqual(read_html("./tests/example.html"), html)

  def test_edge_cases(self):
    guru.clear_dir("/tmp/this_does_not_exist/test")
    guru.read_file("/tmp/this_does_not_exist")
    guru.copy_file("/tmp/this_does_not_exist/a", "/tmp/this_does_not_exist/b")

  @responses.activate
  def test_character_encoding_edge_cases(self):
    responses.add(responses.GET, "https://www.example.com/test1", body="test1")
    test1 = guru.http_get("https://www.example.com/test1", cache=False)
    self.assertEqual(test1, "test1")

    responses.add(responses.GET, "https://www.example.com/test2", body="Yes 👍")
    test2 = guru.http_get("https://www.example.com/test2", cache=False)
    self.assertEqual(test2, "Yes 👍")

    responses.add(responses.GET, "https://www.example.com/test3", body="háček señor Chișinău")
    test3 = guru.http_get("https://www.example.com/test3", cache=False)
    self.assertEqual(test3, "háček señor Chișinău")