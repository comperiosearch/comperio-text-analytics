from abc import ABCMeta, abstractmethod
import logging
from math import log
import re

from elasticsearch.client import IndicesClient
from gensim.corpora import Dictionary
from gensim.models import TfidfModel

ES_TERM_WEIGHTING_INDEX_DEFAULT_NAME = 'es_term_weighting_index'

ES_TERMWEIGHTING_INDEX_SETTINGS = {"mappings": {
    "term": {"properties": {"form": {"type": "string", "index": "not_analyzed"}, "value": {"type": "float"}}}}}


class TermWeightingProvider:
    """
    Base class for term weighting providers handling common weighting transforms, basic missing terms policies and
     the weight retrieval API.
    """
    __metaclass__ = ABCMeta

    def __init__(self, missing='error', inverse=False, sublinear=False):
        """
        :param missing: Missing terms policy. 'error' raises KeyError, 'ignore' removes missing terms from the result,
            and a number value returns that value for missing terms.
        :type missing: str|unicode|int|long|float
        :param inverse: Inverse the frequency ratio (for IDF and similar weighttings).
        :type inverse:bool
        :param sublinear: Log the frequency ratio. Applied after inversion if applicable.
        :type sublinear:bool
        :raise ValueError: When passed invalid missing argument.
        """
        self.inverse = inverse
        self.sublinear = sublinear

        self.default_value = None

        if isinstance(missing, (str, unicode)):
            self.missing_value_policy = missing
        elif isinstance(missing, (int, long, float)):
            self.missing_value_policy = 'value'
            self.default_value = float(missing)
        else:
            raise ValueError

    def _handle_missing_term(self, term):
        """
        Implements missing terms according to configured policy

        :param term:
        :type term:str|unicode
        :rtype : None|float
        :return: :raise KeyError:
        """
        if self.missing_value_policy == 'error':
            raise KeyError(term)
        elif self.missing_value_policy == 'ignore':
            return None
        else:
            return self.default_value

    def __getitem__(self, terms):
        """
        Retrieves the weights for one or more term.

        :param terms: single or list of terms
        :type terms: str|unicode|list|tuple
        :rtype : (str|unicode, float)|list
        :raise NotImplementedError:
        """
        # single term retrievals are returned in a special format
        single = False

        if isinstance(terms, (str, unicode)):
            terms = [terms]
            single = True

        # retrieve the term weight map implemented in the superclass
        tw = self._weights_for_terms(terms)

        w = []

        for term in terms:
            if term in tw:
                w.append((term, tw[term]))
            else:
                # check missing value policy
                val = self._handle_missing_term(term)

                if val:
                    w.append((term, val))

        # do transforms
        if self.inverse:
            w = [(term, 1. / freq) for term, freq in w]

        if self.sublinear:
            w = [(term, log(freq)) for term, freq in w]

        # if we're returning a single or null result we unwrap the list
        if single and (len(w) == 1):
            return w[0]
        elif len(w) == 0:
            return None
        else:
            return w

    @abstractmethod
    def _weights_for_terms(self, terms):
        """
        Implement this method to retrieve the actual weights for the terms in the query.
        If a term is missing it should not be included, the base class will handle missing values.

        :param terms:
        :type terms:list
        :rtype : dict
        :raise NotImplementedError:
        """
        raise NotImplementedError


def weight_map_from_term_counts(term_count_iter, min_count=1):
    """
    Create a map of terms and their frequencies from a list of terms and counts.

    :param term_count_iter: An iterator with tuples of terms and counts, ie, (term, count).
    :param min_count: Minimum count value that will be added to the weight map:
    :type min_count: int|long
    :rtype : dict
    :return: A dict with the terms as keys and the frequency ratios as values.
    """
    weight_map = {}
    total = 0

    for term, count in term_count_iter:
        total += count

        if count >= min_count:
            weight_map[term] = weight_map.get(term, 0) + count

    for term in weight_map.keys():
        w = weight_map[term] / float(total)

        weight_map[term] = w

    return weight_map


def term_counts_line_parser(line, delim='\t', term_index=1, count_index=2):
    """
    Parses a line from a file with terms and counts as line items.

    The defaults f.ex. parses "34\tba\t45\n" into ('ba', 45)

    :param line:
    :type line: unicode|str
    :param delim: Character used to split tokens.
    :type delim: unicode|str
    :param term_index: Token index for the term element.
    :type term_index: int|long
    :param count_index: Token index for the count element.
    :type count_index: int|long
    :rtype : (unicode|str, int|long)
    :return: Tuple with the term and count from the passed line string.
    """
    tokens = line.split(delim)

    return tokens[term_index], int(tokens[count_index])


def term_counts_iter_from_file(f, line_parser=None):
    """
    Reads term counts from a file with term/count pairs as line items.

    :param f: A FileIO instance
    :type f: FileIO
    :param line_parser: Function that parses a line into a term, count tuple. Default parses Gensim Dictionary
        text format.
    :type line_parser: function
    :rtype : generator
    """
    if not line_parser:
        line_parser = term_counts_line_parser

    for line in f:
        yield line_parser(line)


class SimpleTermWeightProvider(TermWeightingProvider):
    """
    Simple term weight provider for term count ratios supplied by an iterator. Takes options for returning
    logged or inverse ratios.
    """

    def __init__(self, term_count_iter, **kwargs):
        super(SimpleTermWeightProvider, self).__init__(**kwargs)

        self.weight_map = weight_map_from_term_counts(term_count_iter)

    def _weights_for_terms(self, terms):
        # just return the whole weight dict
        return self.weight_map


class ESTermAggregationWeightProvider(TermWeightingProvider):
    """
    Term weight provider for DF/IDF values based on an Elasticsearch index using the terms aggregator.

    Defaults to logged IDF values.
    """

    def __init__(self, es, index, doc_type, field, **kwargs):
        super(ESTermAggregationWeightProvider, self).__init__(**kwargs)

        self.es = es
        self.index = index
        self.doc_type = doc_type
        self.field = field

    def _weights_for_terms(self, terms):
        q = {"size": 0,
             "aggs": {"df": {"terms": {"field": self.field, "size": len(terms),
                                       "include": '|'.join([re.escape(term) for term in terms])}}}}

        resp = self.es.search(index=self.index, doc_type=self.doc_type, body=q)

        try:
            n_doc = resp['hits']['total']
            tf = dict((e['key'], e['doc_count'] / float(n_doc)) for e in resp['aggregations']['df']['buckets'])
        except KeyError:
            # malformed response
            raise RuntimeError

        return dict(tf)


class GensimIDFProvider(TermWeightingProvider):
    """
    IDF TermWeightingProvider based on a Gensim Dictionary using the Gensim TfIdf model.
    """
    def __init__(self, dictionary, **kwargs):
        super(GensimIDFProvider, self).__init__(**kwargs)

        if {'missing', 'linear', 'linear'} <= set(kwargs):
            logging.warning('<%s> argumemts to GensimIDFProvider can generate incorrect weights and should not be used'
                            % '|'.join({'missing', 'linear', 'linear'}))

        if isinstance(dictionary, (str, unicode)):
            dictionary = Dictionary.load(dictionary)
        self.dictionary = dictionary
        self.tfidf = TfidfModel(dictionary=dictionary, normalize=False)

    def _weights_for_terms(self, terms):
        return {self.dictionary[bow_id]: val for bow_id, val in self.tfidf[self.dictionary.doc2bow(terms)]}


class ESTermIndexWeightingProvider(TermWeightingProvider):
    """
    Class implementing storage of term weights in an Elasticsearch index.
    """
    def __init__(self, es, index=None, initial_weights=None, **kwargs):
        """
        :param es: Elasticsearch instance from py-elasticsearch API.
        :type es:elasticsearch.Elasticsearch
        :param index: Name of the index where term weights are stored. If it doesn't exist it is created.
        :type index:str|unicode
        :param initial_weights: Iterator with term/weight pairs that will be added to the index during initialization.
        """
        super(ESTermIndexWeightingProvider, self).__init__(**kwargs)

        self.es = es
        self.index = index

        if not self.index:
            self.index = ES_TERM_WEIGHTING_INDEX_DEFAULT_NAME

        ESTermIndexWeightingProvider._create_weight_index(self.es, self.index)

        if initial_weights:
            ESTermIndexWeightingProvider._add_terms_iter(self.es, self.index, initial_weights)

    @staticmethod
    def _create_weight_index(es, index):
        """
        Creates the index with the right mapping if it doesn't exist.

        :param es:
        :type es:elasticsearch.Elasticsearch
        :param index:
        :type index:str|unicode
        """
        ic = IndicesClient(es)

        if ic.exists(index):
            logging.info('Index %s already exists ...' % index)
        else:
            ic.create(index=index, body=ES_TERMWEIGHTING_INDEX_SETTINGS)

    @staticmethod
    def _add_terms_iter(es, index, iter, bulk_size=1000):
        """
        Adds term documents to the index from the term weight pairs in the iterator.

        :param es:
        :type es:elasticsearch.Elasticsearch
        :param index:
        :type index:str|unicode
        :param iter:
        """
        bulk_actions = []
        count = 0

        for term, weight in iter:
            count = 1

            bulk_actions += [{'index': {'_index': index, '_type': 'term'}},
                             {'form': term, 'value': weight}]

            if len(bulk_actions) % (2 * bulk_size) == 0:
                es.bulk(index=index, doc_type='term', body=bulk_actions)
                logging.info('Added %d documents ...' % count)
                bulk_actions = []

        if bulk_actions:
            es.bulk(index=index, doc_type='term', body=bulk_actions)
            logging.info('Added %d documents ...' % count)

    def _weights_for_terms(self, terms):
        should_clauses = [{'match': {'form': term}} for term in terms]

        resp = self.es.search(index=self.index, doc_type='term',
                       body={'query': {
                           'bool': {
                               'should': should_clauses
                           }
                       },
                       'fields': ['form', 'value']})

        return {hit['fields']['form'][0]: float(hit['fields']['value'][0]) for hit in resp['hits']['hits']}
