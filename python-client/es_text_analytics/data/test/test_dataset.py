from unittest import TestCase

from es_text_analytics.data.dataset import fn_from_url


class TestDataset(TestCase):
  def test_fn_from_url(self):
    self.assertEqual(fn_from_url('http://qwone.com/~jason/20Newsgroups/20news-18828.tar.gz'), '20news-18828.tar.gz')
