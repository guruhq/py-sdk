import json
import unittest
import responses

from tests.util import use_guru, get_calls

import guru


class TestFindAndReplace(unittest.TestCase):


  @use_guru()
  def test_replace_term_in_text(self,g):
    term = "Test"
    term_for_testing_titlecase = "Test case"
    replacement = "Purple"
    content = "TEST, Test"
    titlecased_content = "Test Case"

    # md_content="""#Header 1\n##Header2\n###Header3\n\n\n\n# Header 1\n## Header 2\n### Header 3\n\nHere is a test paragraph. Here is a test paragraph."""

    expected = "PURPLE, Purple"
    expected_term_case_sensitive = "TEST, Purple"
    expected_replacement_case_sensitive = "Purple, Purple"
    expected_titlecase = "Purple"
    
    test_result = guru.replace_text_in_text(content, term, replacement)
    term_case_sensitive_test_result = guru.replace_text_in_text(content, term, replacement, term_case_sensitive=True)
    replacement_case_sensitive_test_result = guru.replace_text_in_text(content, term, replacement, replacement_case_sensitive=True)
    test_titlecase_result = guru.replace_text_in_text(titlecased_content, term_for_testing_titlecase, replacement)
    ## replacement is not case-sensitive
    print("RESULT 1: ", test_result)
    self.assertEqual(test_result, expected)
    ## term is case-sensitive
    print("RESULT 2: ", term_case_sensitive_test_result)
    self.assertEqual(term_case_sensitive_test_result, expected_term_case_sensitive)
    ## replacement is case-sensitive
    print("RESULT 3: ", replacement_case_sensitive_test_result)
    self.assertEqual(replacement_case_sensitive_test_result, expected_replacement_case_sensitive)
    ## uncommon content, so need to replace will only find 
    print("RESULT 4: ", guru.replace_text_in_text("TesT test", term, replacement))
    self.assertEqual(guru.replace_text_in_text("TesT test", "TesT", "PurplE", term_case_sensitive=True), "PurplE test")
    ## titlecase
    print("RESULT 5: ", test_titlecase_result)
    self.assertEqual(test_titlecase_result, expected_titlecase)


  @use_guru()
  def test_replace_term_in_text_with_highlight_span(self,g):
    term = "Test"
    replacement = "[GURU_SDK_HIGHLIGHT_START]Test[GURU_SDK_HIGHLIGHT_END]"
    content= "TEST, Test"

    expected = "[GURU_SDK_HIGHLIGHT_START]TEST[GURU_SDK_HIGHLIGHT_END], [GURU_SDK_HIGHLIGHT_START]Test[GURU_SDK_HIGHLIGHT_END]"
    expected_term_case_sensitive = "TEST, [GURU_SDK_HIGHLIGHT_START]Test[GURU_SDK_HIGHLIGHT_END]"
    expected_replacement_case_sensitive = "[GURU_SDK_HIGHLIGHT_START]Test[GURU_SDK_HIGHLIGHT_END], [GURU_SDK_HIGHLIGHT_START]Test[GURU_SDK_HIGHLIGHT_END]"
    
    test_result = guru.replace_text_in_text(content, term, replacement)
    term_case_sensitive_test_result = guru.replace_text_in_text(content, term, replacement, term_case_sensitive=True)
    replacement_case_sensitive_test_result = guru.replace_text_in_text(content, term, replacement, replacement_case_sensitive=True)
    ## replacement is not case-sensitive
    print("RESULT 1: ", test_result)
    self.assertEqual(test_result, expected)
    ## term is case-sensitive
    print("RESULT 2: ", term_case_sensitive_test_result)
    self.assertNotEqual(term_case_sensitive_test_result, expected_term_case_sensitive)
    ## replacement is case-sensitive
    print("RESULT 3: ", replacement_case_sensitive_test_result)
    self.assertNotEqual(replacement_case_sensitive_test_result, expected_replacement_case_sensitive)

  
  @use_guru()
  @responses.activate
  def test_replace_term_in_html(self,g):
    term = "Test"
    replacement = "Purple"
    html_content = """<p>TEST</p>"""
    md_content="""#Header 1\n##Header2\n###Header3\n\n\n\n# Header 1\n## Header 2\n### Header 3\n\nHere is a test paragraph. Here is a test paragraph. Here is a test paragraph. Here is a test paragraph. Here is a test paragraph. Here is a test paragraph.\n\nHere is a test paragraph. Here is a test paragraph. Here is a test paragraph. Here is a test paragraph. Here is a test paragraph."""
    
    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", json={
      "content": html_content
    })
    card_content = g.get_card("1111").doc


    expected_html = """<p>PURPLE</p>"""
    expected_html_replacement_case_sensitive = """<p>Purple</p>"""
    
    test_result = guru.replace_text_in_html(html_content, term, replacement)
    card_content_test_result = guru.replace_text_in_html(card_content, term, replacement)
    replacement_case_sensitive_test_result = guru.replace_text_in_html(html_content, term, replacement, replacement_case_sensitive=True)
    ## replacement term is not case-sensitive
    print("RESULT 1: ", test_result)
    self.assertEqual(test_result, expected_html)
    ## replacement term is case-sensitive
    print("RESULT 2: ", replacement_case_sensitive_test_result)
    self.assertEqual(replacement_case_sensitive_test_result, expected_html_replacement_case_sensitive)
    ## html is from a card (BeautifulSoup instance)
    print("RESULT 3: ", card_content_test_result)
    self.assertEqual(card_content_test_result, expected_html)
  
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

    expected_term = """<p><span class="sdk-orig-highlight">Test</span></p>"""
    expected_replacement = """<p><span class="sdk-replacement-highlight">Purple</span></p>"""
    
    # card.content
    test_term_result = guru.add_highlight(term_card.content, term, term, highlight="original")
    test_replacement_result = guru.add_highlight(replacement_card.content, replacement, replacement, highlight="replacement")
    # card instance
    test_term_card_result = guru.add_highlight(term_card, term, term, highlight="original")
    test_replacement_card_result = guru.add_highlight(replacement_card, replacement, replacement, highlight="replacement")
    
    ## term highlight
    print("RESULT 1: ", test_term_result)
    self.assertEqual(test_term_result, expected_term)
    ## replacement highlight
    print("RESULT 2: ", test_replacement_result)
    self.assertEqual(test_replacement_result, expected_replacement)
    
    ## term highlight (card instance)
    print("RESULT 3: ", test_term_card_result)
    self.assertEqual(test_term_card_result, expected_term)
    ## replacement highlight (card instance)
    print("RESULT 4: ", test_replacement_card_result)
    self.assertEqual(test_replacement_card_result, expected_replacement)
    
  @use_guru()
  @responses.activate
  def test_replace_term_in_card(self,g):
    term = "Test"
    replacement = "Purple"

    # register the response for the API call we'll make.
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/1111/extended", json={
      "preferredPhrase": "Testing 1, 2, 3",
      "content": """<p>TEST</p>"""
    })
    responses.add(responses.GET, "https://api.getguru.com/api/v1/cards/2222/extended", json={
      "preferredPhrase": "Testing 1, 2, 3",
      "content": """#Header 1\n##Header2\n###Header3\n\n\n\n# Header 1\n## Header 2\n### Header 3\n\nHere is a test paragraph. Here is a test paragraph. Here is a test paragraph. Here is a test paragraph. Here is a test paragraph. Here is a test paragraph.\n\nHere is a test paragraph. Here is a test paragraph. Here is a test paragraph. Here is a test paragraph. Here is a test paragraph."""
    })
    card = g.get_card("1111")
    markdown_card = g.get_card("2222")

    expected_html = """<p>PURPLE</p>"""
    expected_html_highlight = """<p><span class="sdk-replacement-highlight">PURPLE</span></p>"""
    expected_markdown = """<p><Purple</p>"""
    expected_markdown_highlight = """<p><span class="sdk-replacement-highlight">Purple</span></p>"""
    
    test_result = guru.replace_text_in_card(card, term, replacement)
    markdown_test_result = guru.replace_text_in_card(markdown_card, term, replacement)
    test_highlight_result = guru.replace_text_in_card(card, term, replacement, replacement_highlight=True, orig_highlight=True)
    markdown_highlight_test_result = guru.replace_text_in_card(markdown_card, term, replacement, replacement_highlight=True, orig_highlight=True)
    ## replace title and content

    ## content is html
    print("RESULT 1: ", test_result)
    self.assertEqual(test_result, expected_html)
    ## content is markdown
    # print("RESULT 2: ", markdown_test_result)
    # self.assertEqual(markdown_test_result, expected_markdown)
    ## highlighted content: is html
    print("RESULT 3: ", test_highlight_result)
    self.assertEqual(test_highlight_result, expected_html_highlight)
    ## highlighted content: is markdown
    print("RESULT 4: ", markdown_highlight_test_result)
    # self.assertEqual(markdown_highlight_test_result, expected_markdown_highlight)
    
  



  