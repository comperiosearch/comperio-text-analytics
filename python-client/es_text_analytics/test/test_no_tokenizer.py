# coding=utf-8
from unittest import TestCase

from es_text_analytics.tokenizer import NOTokenizer


class TestNOTokenizer(TestCase):
    def test_tokenize(self):
        tokenizer = NOTokenizer()
        self.assertEqual(['Dette', 'er', u'vårt', 'hus', '.'],
                         tokenizer.tokenize(u'Dette er vårt hus.'))