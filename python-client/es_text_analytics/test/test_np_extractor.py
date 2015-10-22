# coding=utf-8
from unittest import TestCase

from es_text_analytics.np_extractor import NONPExtractor


class TestNONPExtractor(TestCase):
    def test_tag(self):
        extractor = NONPExtractor()
        self.assertEqual(extractor.extract([(u'Dette', 'PRON_PERS'),
                                            (u'er', 'VERB'),
                                            (u'vårt', 'DET'),
                                            (u'hus', 'SUBST'),
                                            (u'.', 'PUNKT')]),
                         [u'hus'])
