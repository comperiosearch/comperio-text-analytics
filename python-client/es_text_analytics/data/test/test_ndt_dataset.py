# coding=utf-8
from unittest import TestCase

from es_text_analytics.data.ndt_dataset import filelist, normalize


class TestNDTDatasetHelpers(TestCase):
    def test_filelist(self):
        files = filelist()

        self.assertEqual(2, len(files))
        self.assertTrue('ndt_1-0_nno.conll' in files)
        self.assertTrue('ndt_1-0_nob.conll' in files)

        files = filelist(lang='nob', sections=['parliament'])

        self.assertEqual(1, len(files))
        self.assertTrue('parliament_ndt_1-0_nob.conll' in files)

    def test_normalize(self):
        doc = [[1, 'Eg', 'eg', 'pron'],
               [2, 'var', 'vere', 'verb'],
               [3, u'på', u'på', 'prep'],
               [4, 'bibeltime', 'bibeltime', 'subst'],
               [5, '.', '$.', 'clb']]

        result = normalize(doc)
        self.assertEqual(1, len(result))
        self.assertTrue('content' in result)
        self.assertTrue(u'Eg var på bibeltime .' in result.values())
