from abc import ABCMeta, abstractmethod
from math import log
import re


class TermWeightingProvider:
    __metaclass__ = ABCMeta

    @abstractmethod
    def __getitem__(self, terms):
        """
        Retrives the weights for one or more term.

        :param terms: single or list of terms
        :type terms: str|unicode|list
        :rtype : (str|unicode, float)|generator
        :raise NotImplementedError:
        """
        raise NotImplementedError


def weight_map_from_term_counts(term_count_iter, inverse=False, sublinear=False):
    """
    Create a map of terms and their frequencies from a list of terms and counts.

    :param term_count_iter: An iterator with tuples of terms and counts, ie, (term, count).
    :param inverse: Return the inverse frequencies.
    :type inverse: bool
    :param sublinear: Returned logged frequencies.
    :type inverse: bool
    :rtype : dict
    :return: A dict with the terms as keys and the frequency ratios as values.
    """
    weight_map = {}
    total = 0

    for term, count in term_count_iter:
        total += count
        weight_map[term] = weight_map.get(term, 0) + count

    for term in weight_map.keys():
        w = weight_map[term] / float(total)

        if inverse:
            w = 1. / w
        if sublinear:
            w = log(w)

        weight_map[term] = w

    return weight_map


class SimpleTermWeightProvider(TermWeightingProvider):
    """
    Simple term weight provider for term count ratios supplied by an iterator. Takes options for returning
    logged or inverse ratios.
    """
    def __init__(self, term_count_iter, inverse=False, sublinear=False):
        self.weight_map = weight_map_from_term_counts(term_count_iter, inverse=inverse, sublinear=sublinear)

    def __getitem__(self, terms):
        single = False

        if isinstance(terms, (str, unicode)):
            terms = [terms]
            single = True

        w = ((term, self.weight_map[term]) for term in terms if self.weight_map.has_key(term))

        if single:
            try:
                return w.next()
            except StopIteration:
                # preserves dict like behaviour for single term lookups
                raise KeyError(terms[0])
        else:
            return w


class ESTermWeightProvider(TermWeightingProvider):
    """
    Term weight provider for DF/IDF values based on an Elasticsearch index using the terms aggregator.

    Defaults to logged IDF values.
    """
    def __init__(self, es, index, doc_type, field, inverse=True, sublinear=True):
        self.es = es
        self.index = index
        self.doc_type = doc_type
        self.field = field
        self.inverse = inverse
        self.sublinear = sublinear

    def __getitem__(self, terms):
        single = False

        if isinstance(terms, (str, unicode)):
            terms = [terms]
            single = True

        q = {"size": 0,
             "aggs": {"df": {"terms": {"field": self.field, "size": len(terms),
                                       "include": '|'.join([re.escape(term) for term in terms])}}}}

        resp = self.es.search(index=self.index, doc_type=self.doc_type, body=q)

        # no matching terms in query
        if len(resp['aggregations']['df']['buckets']) == 0:
            raise KeyError

        try:
            n_doc = resp['hits']['total']
            tf = ((e['key'], e['doc_count']) for e in resp['aggregations']['df']['buckets'])
            w = ((term, freq / float(n_doc)) for term, freq in tf)

            if self.inverse:
                w = ((term, 1. / freq) for term, freq in w)

            if self.sublinear:
                w = ((term, log(freq)) for term, freq in w)

            if single:
                return w.next()
            else:
                return w
        except KeyError:
            # malformed response
            raise RuntimeError
