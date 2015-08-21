from operator import itemgetter


class SingleDocSigTerms:
    def __init__(self, es, index,  doc_type, field, term_weight_provider):
        self.es = es
        self.index = index
        self.doc_type = doc_type
        self.field = field
        self.term_weight_provider = term_weight_provider

    def tf_for_doc_id(self, doc_id):
        resp = self.es.termvector(index=self.index, doc_type=self.doc_type, id=doc_id, fields=[self.field])

        if resp['found']:
            return [(term, val['term_freq']) for term, val in resp['term_vectors'][self.field]['terms'].items()]

    def by_doc_id(self, doc_id, n=5):
        term_freqs = self.tf_for_doc_id(doc_id)

        if self.term_weight_provider:
            weights = self.term_weight_provider[(term for term, _ in term_freqs)]

            term_freqs = [(term , freq*weights[term]) for term, freq in term_freqs]

        return sorted(term_freqs, key=itemgetter(1), reverse=True)[0:n]
