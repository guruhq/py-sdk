import json
import unittest
import responses

from urllib.parse import quote
from tests.util import use_guru, get_calls

import guru

from guru.find_and_replace import Preview, PreviewData

class TestFindAndReplace(unittest.TestCase):
  @use_guru()
  def test_replace_term_in_text(self,g):
    term = "Test"
    term_for_testing_titlecase = "Test case"
    replacement = "Purple"
    content = "TEST, Test"
    titlecased_content = "Test Case"

    test_result = guru.replace_text_in_text(content, term, replacement)
    term_case_sensitive_test_result = guru.replace_text_in_text(content, term, replacement, term_case_sensitive=True)
    replacement_case_sensitive_test_result = guru.replace_text_in_text(content, term, replacement, replacement_case_sensitive=True)
    test_titlecase_result = guru.replace_text_in_text(titlecased_content, term_for_testing_titlecase, replacement)
    
    expected = "PURPLE, Purple"
    expected_term_case_sensitive = "TEST, Purple"
    expected_replacement_case_sensitive = "Purple, Purple"
    expected_titlecase = "Purple"
    
    ## replacement is not case-sensitive
    self.assertEqual(test_result, expected)
    ## term is case-sensitive
    self.assertEqual(term_case_sensitive_test_result, expected_term_case_sensitive)
    ## replacement is case-sensitive
    self.assertEqual(replacement_case_sensitive_test_result, expected_replacement_case_sensitive)
    ## uncommon content, so will only replace exact term
    self.assertEqual(guru.replace_text_in_text("TesT test", "TesT", "PurplE", term_case_sensitive=True), "PurplE test")
    ## titlecase
    self.assertEqual(test_titlecase_result, expected_titlecase)


  @use_guru()
  def test_replace_term_in_text_with_highlight_span(self,g):
    term = "Test"
    replacement = "[GURU_SDK_HIGHLIGHT_START]Test[GURU_SDK_HIGHLIGHT_END]"
    content= "TEST, Test"

    test_result = guru.replace_text_in_text(content, term, replacement)
    term_case_sensitive_test_result = guru.replace_text_in_text(content, term, replacement, term_case_sensitive=True)
    replacement_case_sensitive_test_result = guru.replace_text_in_text(content, term, replacement, replacement_case_sensitive=True)
    
    expected = "[GURU_SDK_HIGHLIGHT_START]TEST[GURU_SDK_HIGHLIGHT_END], [GURU_SDK_HIGHLIGHT_START]Test[GURU_SDK_HIGHLIGHT_END]"
    expected_term_case_sensitive = "TEST, [GURU_SDK_HIGHLIGHT_START]Test[GURU_SDK_HIGHLIGHT_END]"
    expected_replacement_case_sensitive = "[GURU_SDK_HIGHLIGHT_START]Test[GURU_SDK_HIGHLIGHT_END], [GURU_SDK_HIGHLIGHT_START]Test[GURU_SDK_HIGHLIGHT_END]"
    
    ## replacement is not case-sensitive
    self.assertEqual(test_result, expected)
    ## term is case-sensitive
    self.assertNotEqual(term_case_sensitive_test_result, expected_term_case_sensitive)
    ## replacement is case-sensitive
    self.assertNotEqual(replacement_case_sensitive_test_result, expected_replacement_case_sensitive)

  
  @use_guru()
  @responses.activate
  def test_replace_term_in_html(self,g):
    term = "Test"
    term_with_special_characters = "$Test$"
    replacement = "Purple"
    replacement_with_special_characters = "$Purple$"
    html_content = """<p>TEST</p>"""
    quoted_content = """<p>"TEST"</p><a href="mailto:test@example.com">"Email us here"</a>"""
    html_with_link = """<p>TEST</p><a href="mailto:test@example.com">Email us here</a>"""
    html_content_with_special_characters = """<p>Card - card$TEST$ (Test)</p>"""
    
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", json={
      "content": html_content
    })
    card_content = g.get_card("1111").doc


    test_result = guru.replace_text_in_html(html_content, term, replacement)
    html_with_link_test_result = guru.replace_text_in_html(html_with_link, term, replacement, replace_html_attributes=True)
    quoted_content_result = guru.replace_text_in_html(quoted_content, term, replacement)
    quoted_content_result_term_sensitive = guru.replace_text_in_html(quoted_content, term, replacement, term_case_sensitive=True)
    quoted_content_result_replacement_sensitive = guru.replace_text_in_html(quoted_content, term, replacement, replacement_case_sensitive=True)
    card_content_test_result = guru.replace_text_in_html(card_content, term, replacement)
    replacement_case_sensitive_test_result = guru.replace_text_in_html(html_content, term, replacement, replacement_case_sensitive=True)
    html_with_special_characters_result = guru.replace_text_in_html(html_content_with_special_characters, term_with_special_characters, replacement_with_special_characters)
    
    expected_html = """<p>PURPLE</p>"""
    expected_html_with_special_characters = """<p>Card - card$PURPLE$ (Test)</p>"""
    expected_html_with_link = """<p>PURPLE</p><a href="mailto:purple@example.com">Email us here</a>"""
    expected_quoted = """<p>"PURPLE"</p><a href="mailto:test@example.com">"Email us here"</a>"""
    expected_quoted_term_sensitive = """<p>"TEST"</p><a href="mailto:test@example.com">"Email us here"</a>"""
    expected_quoted_replacement_sensitive = """<p>"Purple"</p><a href="mailto:test@example.com">"Email us here"</a>"""
    expected_html_replacement_case_sensitive = """<p>Purple</p>"""
    
    ## replacement term is not case-sensitive
    self.assertEqual(test_result, expected_html)
    ## replacement term is case-sensitive
    self.assertEqual(replacement_case_sensitive_test_result, expected_html_replacement_case_sensitive)
    ## html is from a card (BeautifulSoup instance
    self.assertEqual(card_content_test_result, expected_html)
    ## replace term in href
    self.assertEqual(html_with_link_test_result, expected_html_with_link)
    ## quoted html text
    self.assertEqual(quoted_content_result, expected_quoted)
    ## quoted html text term-sensitive
    self.assertEqual(quoted_content_result_term_sensitive, expected_quoted_term_sensitive)
    ## quoted html text replacement-sensitive
    self.assertEqual(quoted_content_result_replacement_sensitive, expected_quoted_replacement_sensitive)
    ## term contains symbols that should be escaped
    self.assertEqual(html_with_special_characters_result, expected_html_with_special_characters)
  
  @use_guru()
  @responses.activate
  def test_add_highlight(self, g):
    term = "Test"
    replacement = "Purple"
  
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", json={
      "content": """<p>Test</p>"""
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/2222/extended", json={
      "content": """<p>Purple</p>"""
    })
    term_card = g.get_card("1111")
    replacement_card = g.get_card("2222")

    # card.content
    test_term_result = guru.add_highlight(term_card.content, term, highlight="original")
    test_replacement_result = guru.add_highlight(replacement_card.content, replacement, highlight="replacement")
    # card instance
    test_term_card_result = guru.add_highlight(term_card, term, highlight="original")
    test_replacement_card_result = guru.add_highlight(replacement_card, replacement, highlight="replacement")
    
    expected_term = """<p><span class="sdk-orig-highlight">Test</span></p>"""
    expected_replacement = """<p><span class="sdk-replacement-highlight">Purple</span></p>"""
    
    ## term highlight
    self.assertEqual(test_term_result, expected_term)
    ## replacement highlight
    self.assertEqual(test_replacement_result, expected_replacement)
    
    ## term highlight (card instance)
    self.assertEqual(test_term_card_result, expected_term)
    ## replacement highlight (card instance)
    self.assertEqual(test_replacement_card_result, expected_replacement)
    
  @use_guru()
  @responses.activate
  def test_replace_term_in_card(self,g):

    term = "Test"
    replacement = "Purple"
    md_content = """#Header 1\n##Header2\n###Header3\n\n\n\nHere is a test paragraph. \n\nHere is a test paragraph."""

    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", json={
      "preferredPhrase": "Testing 1, 2, 3",
      "content": """<p>TEST</p>"""
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/2222/extended", json={
      "preferredPhrase": "Testing 1, 2, 3",
      "content": md_content
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/3333/extended", json={
      "preferredPhrase": "Testing 1, 2, 3",
      "content": """<p class="ghq-card-content__markdown" data-ghq-card-content-type="MARKDOWN" data-ghq-card-content-markdown-content=%s></p>""" % quote(md_content)
    })
    card = g.get_card("1111")
    markdown_card = g.get_card("2222")
    card_with_md_block = g.get_card("3333")

    test_result = guru.replace_text_in_card(card, term, replacement)
    markdown_test_result = guru.replace_text_in_card(markdown_card, term, replacement)
    with_md_block_test_result = guru.replace_text_in_card(card_with_md_block, term, replacement)
    test_orig_highlight_result = guru.replace_text_in_card(card, term, term, orig_highlight=True)
    test_replacement_highlight_result = guru.replace_text_in_card(card, replacement, replacement, replacement_highlight=True)
    markdown_highlight_test_result = guru.replace_text_in_card(markdown_card, replacement, replacement, replacement_highlight=True, orig_highlight=True)

    expected_html = """<p>PURPLE</p>"""
    expected_html_highlight = """<p><span class="sdk-replacement-highlight">PURPLE</span></p>"""
    expected_title = "Purpleing 1, 2, 3"
    expected_markdown = """#Header 1\n##Header2\n###Header3\n\n\n\nHere is a purple paragraph. \n\nHere is a purple paragraph."""
    expected_with_md_block = """<p class="ghq-card-content__markdown" data-ghq-card-content-markdown-content="%s" data-ghq-card-content-type="MARKDOWN"></p>""" % quote("""#Header 1\n##Header2\n###Header3\n\n\n\nHere is a purple paragraph. \n\nHere is a purple paragraph.""")
    expected_markdown_highlight = """#Header 1\n##Header2\n###Header3\n\n\n\nHere is a <span class="sdk-replacement-highlight">purple</span> paragraph. \n\nHere is a <span class="sdk-replacement-highlight">purple</span> paragraph."""
    
    ## replace title and content
    guru.replace_text_in_card(card, term, replacement, replace_title=True)

    ## content is html
    self.assertEqual(test_result, expected_html)
    ## content is markdown
    self.assertEqual(markdown_test_result, expected_markdown)
    ## highlighted content: is html
    self.assertEqual(test_replacement_highlight_result, expected_html_highlight)
    ## highlighted content: is markdown
    self.assertEqual(markdown_highlight_test_result, expected_markdown_highlight)
    ## replace title
    self.assertEqual(card.title, expected_title)
    ## replace markdown in attribute on md block
    self.assertEqual(with_md_block_test_result, expected_with_md_block)
    
  @use_guru()
  @responses.activate
  def test_Preview(self,g):
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", json={
      "id": "1111",
      "preferredPhrase": "Testing 1, 2, 3"
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/2222/extended", json={
      "id": "2222",
      "preferredPhrase": "Testing 4, 5, 6"
    })

    card = g.get_card("1111")
    card_2 = g.get_card("2222")
    term = "Test"
    replacement = "Purple"

    preview_data = PreviewData(
      card=card,
      term=term,
      replacement=replacement,
      orig_content="""<h1>Testing Card</h1><p>TEST</p>""",
      new_content="""<h1>Purpleing Card</h1><p>PURPLE</p>"""
    )
    preview_data_2 = PreviewData(
      card=card_2,
      term=term,
      replacement=replacement,
      orig_content="""<h1>Testing Card</h1><p>T E S T</p>""",
      new_content="""<h1>Purpleing Card</h1><p>T E S T</p>"""
    )

    # test term and replacement counts
    self.assertEqual(preview_data.original_term_count, 2)
    self.assertEqual(preview_data.replacement_term_count, 2)

    # instantiate Preview instance
    preview_list = [preview_data, preview_data_2]
    preview = Preview(
      preview_list,
      term,
      replacement, 
      task_name="test_find_and_replace"
    )
    # build the html tree
    preview.make_html_tree()
    self.assertEqual(
      preview.html_pieces[0], 
      '<a href="/tmp/test_find_and_replace/new_content/new_1111.html" data-original-url="/tmp/test_find_and_replace/old_content/orig_1111.html" target="iframe">Testing 1, 2, 3 (2/2)*(0/0)</a>'
    )
