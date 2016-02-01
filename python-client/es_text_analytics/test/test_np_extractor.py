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

        self.assertEqual(extractor.extract([(u'Dette', 'PRON_PERS'),
                                            (u'er', 'VERB'),
                                            (u'vårt', 'DET'),
                                            (u'fine', 'ADJ'),
                                            (u'hus', 'SUBST'),
                                            (u'.', 'PUNKT')]),
                         [[u'fine', u'hus']])
        extractor = NONPExtractor(keep_index=True)
        self.assertEqual(extractor.extract([(u'Dette', 'PRON_PERS'),
                                            (u'er', 'VERB'),
                                            (u'vårt', 'DET'),
                                            (u'hus', 'SUBST'),
                                            (u'.', 'PUNKT')]),
                         [(u'hus', 3)])

        self.assertEqual(extractor.extract([(u'Dette', 'PRON_PERS'),
                                            (u'er', 'VERB'),
                                            (u'vårt', 'DET'),
                                            (u'fine', 'ADJ'),
                                            (u'hus', 'SUBST'),
                                            (u'.', 'PUNKT')]),
                         [([u'fine', u'hus'], 3)])
