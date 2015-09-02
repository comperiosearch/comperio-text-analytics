from StringIO import StringIO
from unittest import TestCase

from elasticsearch.client import Elasticsearch, IndicesClient
from gensim.corpora.dictionary import Dictionary

from es_text_analytics.term_weight_provider import SimpleTermWeightProvider, ESIndexTermWeightProvider, \
    weight_map_from_term_counts, term_counts_line_parser, term_counts_iter_from_file, GensimIDFProvider
from es_text_analytics.test import es_runner


class TestTermWeightProviderHelpers(TestCase):
    def test_weight_map_from_term_counts(self):
        wm = sorted(weight_map_from_term_counts([('foo', 2), ('ba', 1), ('knark', 4), ('knirk', 1)]).items())
        self.assertEqual(wm, [('ba', 0.125), ('foo', 0.25), ('knark', 0.5), ('knirk', 0.125)])

        wm = sorted(weight_map_from_term_counts([('foo', 2), ('ba', 1), ('knark', 4), ('knirk', 1)], min_count=4).items())
        self.assertEqual(wm, [('knark', .5)])

    def test_term_counts_line_parser(self):
        self.assertEqual(('absolutely', 342), term_counts_line_parser('5949\tabsolutely\t342\n'))
        self.assertEqual(('finished', 136), term_counts_line_parser('497\tfinished\t136'))

    def test_term_counts_iter_from_file(self):
        f = StringIO('5949\tabsolutely\t342\n497\tfinished\t136')

        self.assertEqual([('absolutely', 342), ('finished', 136)], list(term_counts_iter_from_file(f)))


class TestSimpleTermWeightProvider(TestCase):
    def test_getitem_single(self):
        provider = SimpleTermWeightProvider([('ba', 2), ('foo', 1), ('ba', 1), ('knark', 1),
                                             ('knirk', 1), ('ba', 1), ('knark', 1)])
        term, w = provider['ba']
        self.assertEqual('ba', term)
        self.assertAlmostEqual(.5, w)
        term, w = provider['knark']
        self.assertEqual('knark', term)
        self.assertAlmostEqual(.25, w)
        term, w = provider['knirk']
        self.assertEqual('knirk', term)
        self.assertAlmostEqual(.125, w)
        term, w = provider['foo']
        self.assertEqual('foo', term)
        self.assertAlmostEqual(.125, w)

    def test_inverse(self):
        provider = SimpleTermWeightProvider([('ba', 2), ('foo', 1), ('ba', 1), ('knark', 1),
                                             ('knirk', 1), ('ba', 1), ('knark', 1)],
                                            inverse=True)
        term, w = provider['ba']
        self.assertEqual('ba', term)
        self.assertAlmostEqual(2., w)
        term, w = provider['knark']
        self.assertEqual('knark', term)
        self.assertAlmostEqual(4., w)
        term, w = provider['knirk']
        self.assertEqual('knirk', term)
        self.assertAlmostEqual(8., w)
        term, w = provider['foo']
        self.assertEqual('foo', term)
        self.assertAlmostEqual(8., w)

    def test_sublinear(self):
        provider = SimpleTermWeightProvider([('ba', 2), ('foo', 1), ('ba', 1), ('knark', 1),
                                             ('knirk', 1), ('ba', 1), ('knark', 1)],
                                            sublinear=True)
        term, w = provider['ba']
        self.assertEqual('ba', term)
        self.assertAlmostEqual(-0.693147, w, places=4)
        term, w = provider['knark']
        self.assertEqual('knark', term)
        self.assertAlmostEqual(-1.386294, w, places=4)
        term, w = provider['knirk']
        self.assertEqual('knirk', term)
        self.assertAlmostEqual(-2.079442, w, places=4)
        term, w = provider['foo']
        self.assertEqual('foo', term)
        self.assertAlmostEqual(-2.079442, w, places=4)

    def test_inverse_sublinear(self):
        provider = SimpleTermWeightProvider([('ba', 2), ('foo', 1), ('ba', 1), ('knark', 1),
                                             ('knirk', 1), ('ba', 1), ('knark', 1)],
                                            sublinear=True, inverse=True)
        term, w = provider['ba']
        self.assertEqual('ba', term)
        self.assertAlmostEqual(0.693147, w, places=4)
        term, w = provider['knark']
        self.assertEqual('knark', term)
        self.assertAlmostEqual(1.386294, w, places=4)
        term, w = provider['knirk']
        self.assertEqual('knirk', term)
        self.assertAlmostEqual(2.079442, w, places=4)
        term, w = provider['foo']
        self.assertEqual('foo', term)
        self.assertAlmostEqual(2.079442, w, places=4)

    def test_getitem_multiple(self):
        provider = SimpleTermWeightProvider([('ba', 2), ('foo', 1), ('ba', 1), ('knark', 1),
                                             ('knirk', 1), ('ba', 1), ('knark', 1)])

        weights = dict(provider[['ba', 'foo', 'knark', 'knirk']])
        self.assertEqual(['ba', 'foo', 'knark', 'knirk'], sorted(weights.keys()))
        self.assertAlmostEqual(weights['ba'], .5)
        self.assertAlmostEqual(weights['knark'], .25)
        self.assertAlmostEqual(weights['knirk'], .125)
        self.assertAlmostEqual(weights['foo'], .125)

        provider = SimpleTermWeightProvider([('ba', 2), ('foo', 1), ('ba', 1), ('knark', 1),
                                             ('knirk', 1), ('ba', 1), ('knark', 1)])

        weights = dict(provider['ba', 'foo', 'knark', 'knirk'])
        self.assertEqual(['ba', 'foo', 'knark', 'knirk'], sorted(weights.keys()))
        self.assertAlmostEqual(weights['ba'], .5)
        self.assertAlmostEqual(weights['knark'], .25)
        self.assertAlmostEqual(weights['knirk'], .125)
        self.assertAlmostEqual(weights['foo'], .125)

    def test_getitem_missing(self):
        provider = SimpleTermWeightProvider([('ba', 2), ('foo', 1), ('ba', 1), ('knark', 1),
                                             ('knirk', 1), ('ba', 1), ('knark', 1)])

        self.assertRaises(KeyError, lambda: provider['notfound'])
        self.assertRaises(KeyError, lambda: provider['ba', 'notfound'])

        provider = SimpleTermWeightProvider([('ba', 2), ('foo', 1), ('ba', 1), ('knark', 1),
                                             ('knirk', 1), ('ba', 1), ('knark', 1)], missing='ignore')
        self.assertEqual([('ba', .5)], list(provider['ba', 'notfound']))
        self.assertIsNone(provider['notfound'])


class TestESIndexTermWeightProvider(TestCase):

    def setUp(self):
        super(TestESIndexTermWeightProvider, self).setUp()

        self.es = Elasticsearch(hosts=['localhost:%d' % es_runner.es_state.port])
        self.ic = IndicesClient(self.es)
        self.index = 'es_term_weight_provider_test'
        self.doc_type = 'test-doc'
        self.field = 'text'

        if self.ic.exists(self.index):
            self.ic.delete(self.index)

        self.ic.create(self.index)
        self.es.create(self.index, self.doc_type, {self.field: 'foo'})
        self.es.create(self.index, self.doc_type, {self.field: 'knark'})
        self.es.create(self.index, self.doc_type, {self.field: 'ba'})
        self.es.create(self.index, self.doc_type, {self.field: 'knirk'})
        self.es.create(self.index, self.doc_type, {self.field: 'ba'})
        self.es.create(self.index, self.doc_type, {self.field: 'ba'})
        self.es.create(self.index, self.doc_type, {self.field: 'knark '})
        self.es.create(self.index, self.doc_type, {self.field: 'ba'}, refresh=True)

    def tearDown(self):
        super(TestESIndexTermWeightProvider, self).tearDown()

        self.ic.delete(self.index)


    def test_getitem_single(self):
        provider = ESIndexTermWeightProvider(self.es, self.index, self.doc_type, self.field,
                                        inverse=False, sublinear=False)

        term, w = provider['ba']
        self.assertEqual('ba', term)
        self.assertAlmostEqual(.5, w)
        term, w = provider['knark']
        self.assertEqual('knark', term)
        self.assertAlmostEqual(.25, w)
        term, w = provider['knirk']
        self.assertEqual('knirk', term)
        self.assertAlmostEqual(.125, w)
        term, w = provider['foo']
        self.assertEqual('foo', term)
        self.assertAlmostEqual(.125, w)

    def test_inverse(self):
        provider = ESIndexTermWeightProvider(self.es, self.index, self.doc_type, self.field,
                                        inverse=True, sublinear=False)
        term, w = provider['ba']
        self.assertEqual('ba', term)
        self.assertAlmostEqual(2., w)
        term, w = provider['knark']
        self.assertEqual('knark', term)
        self.assertAlmostEqual(4., w)
        term, w = provider['knirk']
        self.assertEqual('knirk', term)
        self.assertAlmostEqual(8., w)
        term, w = provider['foo']
        self.assertEqual('foo', term)
        self.assertAlmostEqual(8., w)

    def test_sublinear(self):
        provider = ESIndexTermWeightProvider(self.es, self.index, self.doc_type, self.field,
                                        inverse=False, sublinear=True)
        term, w = provider['ba']
        self.assertEqual('ba', term)
        self.assertAlmostEqual(-0.693147, w, places=4)
        term, w = provider['knark']
        self.assertEqual('knark', term)
        self.assertAlmostEqual(-1.386294, w, places=4)
        term, w = provider['knirk']
        self.assertEqual('knirk', term)
        self.assertAlmostEqual(-2.079442, w, places=4)
        term, w = provider['foo']
        self.assertEqual('foo', term)
        self.assertAlmostEqual(-2.079442, w, places=4)

    def test_inverse_sublinear(self):
        provider = ESIndexTermWeightProvider(self.es, self.index, self.doc_type, self.field,
                                        inverse=True, sublinear=True)
        term, w = provider['ba']
        self.assertEqual('ba', term)
        self.assertAlmostEqual(0.693147, w, places=4)
        term, w = provider['knark']
        self.assertEqual('knark', term)
        self.assertAlmostEqual(1.386294, w, places=4)
        term, w = provider['knirk']
        self.assertEqual('knirk', term)
        self.assertAlmostEqual(2.079442, w, places=4)
        term, w = provider['foo']
        self.assertEqual('foo', term)
        self.assertAlmostEqual(2.079442, w, places=4)

    def test_getitem_multiple(self):
        provider = ESIndexTermWeightProvider(self.es, self.index, self.doc_type, self.field,
                                        inverse=False, sublinear=False)

        weights = dict(provider[['ba', 'foo', 'knark', 'knirk']])
        self.assertEqual(['ba', 'foo', 'knark', 'knirk'], sorted(weights.keys()))
        self.assertAlmostEqual(weights['ba'], .5)
        self.assertAlmostEqual(weights['knark'], .25)
        self.assertAlmostEqual(weights['knirk'], .125)
        self.assertAlmostEqual(weights['foo'], .125)

        weights = dict(provider['ba', 'foo', 'knark', 'knirk'])
        self.assertEqual(['ba', 'foo', 'knark', 'knirk'], sorted(weights.keys()))
        self.assertAlmostEqual(weights['ba'], .5)
        self.assertAlmostEqual(weights['knark'], .25)
        self.assertAlmostEqual(weights['knirk'], .125)
        self.assertAlmostEqual(weights['foo'], .125)

    def test_getitem_missing(self):
        provider = ESIndexTermWeightProvider(self.es, self.index, self.doc_type, self.field,
                                        inverse=False, sublinear=False)

        self.assertRaises(KeyError, lambda: provider['notfound'])
        self.assertRaises(KeyError, lambda: provider['ba', 'notfound'])

        provider = ESIndexTermWeightProvider(self.es, self.index, self.doc_type, self.field,
                                        inverse=False, sublinear=False, missing='ignore')

        self.assertIsNone(provider['notfound'])
        self.assertEqual([('ba', .5)], list(provider['ba', 'notfound']))

class TestGensimIDFProvider(TestCase):
    def setUp(self):
        super(TestGensimIDFProvider, self).setUp()

        self.dictionary = Dictionary([['foo'], ['knark'], ['ba'], ['knirk'], ['ba'], ['ba'], ['knark'], ['ba']])

    def test_getitem_single(self):
        provider = GensimIDFProvider(self.dictionary)

        term, w = provider['ba']
        self.assertEqual('ba', term)
        self.assertAlmostEqual(1, w)
        term, w = provider['knark']
        self.assertEqual('knark', term)
        self.assertAlmostEqual(2, w)
        term, w = provider['knirk']
        self.assertEqual('knirk', term)
        self.assertAlmostEqual(3, w)
        term, w = provider['foo']
        self.assertEqual('foo', term)
        self.assertAlmostEqual(3, w)

    def test_getitem_multiple(self):
        provider = GensimIDFProvider(self.dictionary)

        weights = dict(provider[['ba', 'foo', 'knark', 'knirk']])
        self.assertEqual(['ba', 'foo', 'knark', 'knirk'], sorted(weights.keys()))
        self.assertAlmostEqual(weights['ba'], 1)
        self.assertAlmostEqual(weights['knark'], 2)
        self.assertAlmostEqual(weights['knirk'], 3)
        self.assertAlmostEqual(weights['foo'], 3)

        weights = dict(provider['ba', 'foo', 'knark', 'knirk'])
        self.assertEqual(['ba', 'foo', 'knark', 'knirk'], sorted(weights.keys()))
        self.assertAlmostEqual(weights['ba'], 1)
        self.assertAlmostEqual(weights['knark'], 2)
        self.assertAlmostEqual(weights['knirk'], 3)
        self.assertAlmostEqual(weights['foo'], 3)

    def test_getitem_missing(self):
        provider = GensimIDFProvider(self.dictionary)

        self.assertRaises(KeyError, lambda: provider['notfound'])
        self.assertRaises(KeyError, lambda: provider['ba', 'notfound'])

        provider = GensimIDFProvider(self.dictionary, missing='ignore')

        self.assertIsNone(provider['notfound'])
        self.assertEqual([('ba', 1)], list(provider['ba', 'notfound']))