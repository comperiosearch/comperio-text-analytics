__author__ = 'cvig'
from  es_text_analytics import single_doc_sigterms

from elasticsearch import Elasticsearch
es = Elasticsearch()

sdt = single_doc_sigterms.SingleDocSigTerms(es, 'wiki', 'doc', 'article', None)
print sdt.by_doc_id_idf(178472                        , 20)