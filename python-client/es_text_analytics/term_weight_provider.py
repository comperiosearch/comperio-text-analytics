from abc import ABCMeta, abstractmethod
from math import log
import re


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


def weight_map_from_term_counts(term_count_iter):
    """
    Create a map of terms and their frequencies from a list of terms and counts.

    :param term_count_iter: An iterator with tuples of terms and counts, ie, (term, count).
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

        weight_map[term] = w

    return weight_map


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


class ESTermWeightProvider(TermWeightingProvider):
    """
    Term weight provider for DF/IDF values based on an Elasticsearch index using the terms aggregator.

    Defaults to logged IDF values.
    """

    def __init__(self, es, index, doc_type, field, **kwargs):
        super(ESTermWeightProvider, self).__init__(**kwargs)

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
