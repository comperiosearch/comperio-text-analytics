from unittest import TestCase

from elasticsearch import Elasticsearch
from elasticsearch.client import IndicesClient

from es_text_analytics.single_doc_sigterms import SingleDocSigTerms
from es_text_analytics.test import es_runner


class TestSingleDocSigTerms(TestCase):
    def setUp(self):
        super(TestSingleDocSigTerms, self).setUp()

        self.es = Elasticsearch(hosts=['localhost:%d' % es_runner.es_state.port])
        self.ic = IndicesClient(self.es)
        self.index = 'single_doc_sigterms_test'
        self.doc_type = 'test-doc'
        self.field = 'text'

        if self.ic.exists(self.index):
            self.ic.delete(self.index)

        self.ic.create(self.index)
        self.es.create(self.index, self.doc_type, {self.field: 'foo ba knark foo knirk knark foo'}, id='doc_1')

    def test_tf_for_doc_id(self):
        sigterms = SingleDocSigTerms(self.es, self.index, self.doc_type, self.field, None)

        resp = dict(sigterms.tf_for_doc_id('doc_1'))
        self.assertEquals(4, len(resp))
        self.assertEquals(3, resp['foo'])
        self.assertEquals(2, resp['knark'])
        self.assertEquals(1, resp['ba'])
        self.assertEquals(1, resp['knirk'])
