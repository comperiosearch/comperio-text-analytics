from unittest import TestCase

from es_text_analytics.data.newsgroups import parse


class TestNewsgroups(TestCase):
    def test_parse(self):
        self.assertEqual(parse('From: ba\nSubject: foo\nThe\nmessage.\n--\nSig\n'),
                         {'raw': 'From: ba\nSubject: foo\nThe\nmessage.\n--\nSig\n',
                          'msg': 'The\nmessage.',
                          'from': 'ba',
                          'subject': 'foo',
                          'sig': 'Sig\n'})
        self.assertEqual(parse('Subject: foo\nFrom: ba\nThe\nmessage.\n--\nSig\n'),
                         {'raw': 'Subject: foo\nFrom: ba\nThe\nmessage.\n--\nSig\n',
                          'msg': 'The\nmessage.',
                          'from': 'ba',
                          'subject': 'foo',
                          'sig': 'Sig\n'})
