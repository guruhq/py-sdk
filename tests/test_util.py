
import json
import yaml
import unittest
import responses

import guru

from tests.util import use_guru, get_calls

def read_html(filename):
  with open(filename) as file_in:
    return file_in.read()


class TestUtil(unittest.TestCase):
  @use_guru()
  @responses.activate
  def test_load_html(self, g):
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://www.example.com/test/index.html", body="""<p>
  <a href="../page.html">link</a>
  <img src="test.png" />
</p>""")

    bundle = g.bundle("http")
    doc = bundle.load_html("https://www.example.com/test/index.html")
    self.assertEqual(doc.find("a").attrs["href"], "https://www.example.com/page.html")
    self.assertEqual(doc.find("img").attrs["src"], "https://www.example.com/test/test.png")

    # load it again with caching and assert that we still only made one call.
    bundle.load_html("https://www.example.com/test/index.html", cache=True)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://www.example.com/test/index.html"
    }])

  @use_guru()
  @responses.activate
  def test_load_html_with_local_file(self, g):
    bundle = g.bundle("http")
    doc = bundle.load_html("./tests/test_sync_with_local_files_node1.html")
    self.assertEqual(doc.find("img").attrs["src"], "tests/test_sync_with_local_files_test.png")

  @use_guru()
  @responses.activate
  def test_download_file(self, g):
    bundle = g.bundle("http")

    html = "<p>test</p>"
    responses.add(responses.GET, "https://www.example.com/example.html", body=html)
    bundle.download_file("https://www.example.com/example.html", "./tests/example.html")
    self.assertEqual(read_html("./tests/example.html"), html)

  def test_edge_cases(self):
    guru.clear_dir("/tmp/this_does_not_exist/test")
    guru.read_file("/tmp/this_does_not_exist")
    guru.copy_file("/tmp/this_does_not_exist/a", "/tmp/this_does_not_exist/b")

  @use_guru()
  @responses.activate
  def test_character_encoding_edge_cases(self, g):
    bundle = g.bundle("http")

    responses.add(responses.GET, "https://www.example.com/test1", body="test1")
    test1 = bundle.http_get("https://www.example.com/test1", cache=False)
    self.assertEqual(test1, "test1")

    responses.add(responses.GET, "https://www.example.com/test2", body="Yes 👍")
    test2 = bundle.http_get("https://www.example.com/test2", cache=False)
    self.assertEqual(test2, "Yes 👍")

    responses.add(responses.GET, "https://www.example.com/test3", body="háček señor Chișinău")
    test3 = bundle.http_get("https://www.example.com/test3", cache=False)
    self.assertEqual(test3, "háček señor Chișinău")

  def test_format_timestamp(self):
    self.assertEqual(guru.format_timestamp("2021-03-01"), "2021-03-01T00:00:00-00:00")
    self.assertEqual(guru.format_timestamp("2021-03-01T01:23:45"), "2021-03-01T01:23:45-00:00")

  @use_guru()
  @responses.activate
  def test_http_post(self, g):
    bundle = g.bundle("http")

    responses.add(responses.POST, "https://www.example.com/post1", body="post1")
    post1 = bundle.http_post("https://www.example.com/post1", data={}, cache=False)
    self.assertEqual(post1, "post1")

    responses.add(responses.POST, "https://www.example.com/post2", body="post2")
    post2 = bundle.http_post("https://www.example.com/post2", data=["a"], cache=False)
    self.assertEqual(post2, "post2")

    # make the same call again but since cache=True, it won't make a call.
    responses.add(responses.POST, "https://www.example.com/post2", body="post2")
    post2 = bundle.http_post("https://www.example.com/post2", data=["a"], cache=True)
    self.assertEqual(post2, "post2")

    self.assertEqual(get_calls(), [{
      "method": "POST",
      "url": "https://www.example.com/post1",
      "body": {}
    }, {
      "method": "POST",
      "url": "https://www.example.com/post2",
      "body": ["a"]
    }])

  @use_guru()
  @responses.activate
  def test_429_responses(self, g):
    bundle = g.bundle("http")

    # we set this up so each endpoint gets a 429 the first time and a 200 the second time.
    responses.add(responses.GET, "https://www.example.com/http_get", status=429)
    responses.add(responses.GET, "https://www.example.com/http_get", status=200, body="test")
    responses.add(responses.GET, "https://www.example.com/load_html", status=429)
    responses.add(responses.GET, "https://www.example.com/load_html", status=200, body="test")
    responses.add(responses.GET, "https://www.example.com/download_file", status=429)
    responses.add(responses.GET, "https://www.example.com/download_file", status=200, body="test")
    responses.add(responses.POST, "https://www.example.com/http_post", status=429)
    responses.add(responses.POST, "https://www.example.com/http_post", status=200, body="test")

    response = bundle.http_get("https://www.example.com/http_get", wait=0.1)
    response = bundle.load_html("https://www.example.com/load_html", wait=0.1)
    response = bundle.download_file("https://www.example.com/download_file", "./tests/download_file.html", wait=0.1)
    response = bundle.http_post("https://www.example.com/http_post", wait=0.1)
    self.assertEqual(get_calls(), [{
      "method": "GET",
      "url": "https://www.example.com/http_get"
    }, {
      "method": "GET",
      "url": "https://www.example.com/http_get"
    }, {
      "method": "GET",
      "url": "https://www.example.com/load_html"
    }, {
      "method": "GET",
      "url": "https://www.example.com/load_html"
    }, {
      "method": "GET",
      "url": "https://www.example.com/download_file"
    }, {
      "method": "GET",
      "url": "https://www.example.com/download_file"
    }, {
      "method": "POST",
      "url": "https://www.example.com/http_post"
    }, {
      "method": "POST",
      "url": "https://www.example.com/http_post"
    }])
