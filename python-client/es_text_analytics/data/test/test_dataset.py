# coding=utf-8
from StringIO import StringIO
from unittest import TestCase

from es_text_analytics.data.dataset import fn_from_url, parse_conll

NDT_CONLL_SAMPLE = """
1	Nokre	nokon	det
2	refleksjonar	refleksjon	subst
3	|	$|	clb

1	Eg	eg	pron
2	var	vere	verb
3	på	på	prep
4	bibeltime	bibeltime	subst
5	.	$.	clb

"""


class TestDataset(TestCase):
    def test_fn_from_url(self):
        self.assertEqual(fn_from_url('http://qwone.com/~jason/20Newsgroups/20news-18828.tar.gz'), '20news-18828.tar.gz')

    def test_parse_conll(self):
        result = list(parse_conll(StringIO(NDT_CONLL_SAMPLE)))

        self.assertEqual(2, len(result))
        self.assertEqual([[1, 'Nokre', 'nokon', 'det'],
                          [2, 'refleksjonar', 'refleksjon', 'subst'],
                          [3, '|', '$|', 'clb']],
                         result[0])
        self.assertEqual([[1, 'Eg', 'eg', 'pron'],
                          [2, 'var', 'vere', 'verb'],
                          [3, u'på', u'på', 'prep'],
                          [4, 'bibeltime', 'bibeltime', 'subst'],
                          [5, '.', '$.', 'clb']],
                         result[1])
