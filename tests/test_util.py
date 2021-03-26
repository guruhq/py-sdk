
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

  def test_compare_datetime_string(self):
    date_str = "2021-03-18"
    datetime_str = "2021-03-18T17:29:04.527+0000"
    comparison_date_str = "2020-01-18"
    date_format_1 = "%Y-%m-%d"
    date_format_2 = "%Y-%m-%dT%H:%M:%S.%f%z"
    
    ## if no date_to_compare_against is provided, it will compare against datetime.now()
    self.assertTrue(guru.compare_datetime_string(date_str, "lt", date_format_1))
    self.assertTrue(guru.compare_datetime_string(date_str, "lt_or_eq", date_format_1))
    self.assertFalse(guru.compare_datetime_string(date_str, "gt", date_format_1))
    self.assertFalse(guru.compare_datetime_string(date_str, "gt_or_eq", date_format_1))
    self.assertFalse(guru.compare_datetime_string(date_str, "eq", date_format_1))
    self.assertTrue(guru.compare_datetime_string(date_str, "ne", date_format_1))
    ## pass in comparison date
    self.assertFalse(guru.compare_datetime_string(date_str, "lt_or_eq", date_format_1, date_to_compare_against=comparison_date_str))
    self.assertTrue(guru.compare_datetime_string(date_str, "gt_or_eq", date_format_1, date_to_compare_against=comparison_date_str))
    self.assertTrue(guru.compare_datetime_string(date_str, "ne", date_format_1, date_to_compare_against=comparison_date_str))
    ## pass a different string format
    self.assertTrue(guru.compare_datetime_string(datetime_str, "lt_or_eq", date_format_2, tz_aware=True))
    self.assertFalse(guru.compare_datetime_string(datetime_str, "gt_or_eq", date_format_2, tz_aware=True))
    self.assertTrue(guru.compare_datetime_string(datetime_str, "ne", date_format_2, tz_aware=True))

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

  def test_format_timestamp(self):
    self.assertEqual(guru.format_timestamp("2021-03-01"), "2021-03-01T00:00:00-00:00")
    self.assertEqual(guru.format_timestamp("2021-03-01T01:23:45"), "2021-03-01T01:23:45-00:00")

  @responses.activate
  def test_http_post(self):
    responses.add(responses.POST, "https://www.example.com/post1", body="post1")
    post1 = guru.http_post("https://www.example.com/post1", data={}, cache=False)
    self.assertEqual(post1, "post1")

    responses.add(responses.POST, "https://www.example.com/post2", body="post2")
    post2 = guru.http_post("https://www.example.com/post2", data=["a"], cache=False)
    self.assertEqual(post2, "post2")

    # make the same call again but since cache=True, it won't make a call.
    responses.add(responses.POST, "https://www.example.com/post2", body="post2")
    post2 = guru.http_post("https://www.example.com/post2", data=["a"], cache=True)
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
