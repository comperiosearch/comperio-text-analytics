# coding: utf-8
import sys
from operator import itemgetter

sys.path.append('F:\projects\comperio-text-analytics\python-client')
from elasticsearch import Elasticsearch
import pandas as pd
from gensim.models.ldamodel import LdaModel
from gensim.corpora.dictionary import Dictionary
from gensim.models.tfidfmodel import TfidfModel
import logging
from NOB_kera import NOB_kera

num_words_from_topic = 20
num_results_from_es = 5
modelfile = 'F:/projects/elasticsearch-enterprise-system/data/topic_models/nowiki_v2_3pass_lda_250'
vocabulary = 'F:/projects/elasticsearch-enterprise-system/data/topic_models/voc_vocabulary_0.vocab'

def flatten(x):
    if isinstance(x, tuple):
        return " ".join([i for i in x]).lower()
    else:
        return x.lower()


def add_keywords(results, kera):
    for topicresult in results:
        toptitle = ''
        kkw = {}
        logging.debug(topicresult['topics'][0:300])
        for hits in topicresult['result']['hits']['hits']:
            title = hits['_source']['title']
            topbody = hits['_source']['article']
            toptitle += title + ' _ '
            kwlist = kera.extract_keywords(toptitle + topbody)
            kw = dict(kwlist)
            logging.debug(kw)
            logging.debug("t: %s len kw:%d" % (toptitle, len(kw)))
            for keyword, keyvalue in kw.iteritems():
                if keyword in kkw:
                    kkw[keyword] += float(keyvalue)
                else:
                    kkw[keyword] = float(keyvalue)
        kkw = sorted(kkw.items(), key=itemgetter(1), reverse=True)
        logging.debug(kkw)
        logging.debug('kkw %d' % len(kkw))
        topicresult['keywords'] = kkw
        topicresult['keyword_string'] = " ".join([flatten(k_kw[0]) for k_kw in kkw])
        topicresult['titles'] = toptitle
    return results


def get_doc_topics(ldamodel, num_topics, num_words_from_topic, vocab, tfidfmodel):
    for num_topic in range(num_topics):
        topics = ldamodel.show_topic(num_topic, num_words_from_topic)
        # filter out high/low frequent words from the vocabulary

        toks = [topic[1] for topic in topics]
        logging.debug(toks)
        tfidf = tfidfmodel[vocab.doc2bow(toks)]
        # cut off 10 percent from top and bottom
        cutoff = int(num_words_from_topic * 0.1)
        outdoc = [vocab.get(wd[0]) for wd in sorted(tfidf, key=itemgetter(1), reverse=True)[cutoff:num_words_from_topic-cutoff]]
        logging.debug(outdoc)
        ss = set(toks)
        sb = set(outdoc)
        logging.debug(ss.difference(sb))
        yield (' '.join(outdoc), num_topic)


def main():
    logformat = '%(asctime)s %(name)-12s: %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=logformat)
    kera = NOB_kera()
    es = Elasticsearch(port=9201)
    mod = LdaModel.load(modelfile)
    vocab = Dictionary.load(vocabulary)
    tfidf = TfidfModel(dictionary=vocab)
    results = []
    for (topics, topicid) in get_doc_topics(mod, mod.num_topics, num_words_from_topic, vocab, tfidf):
        res = es.search(index='wiki4', body={"query": {"match": {"_all": topics}}}, size=num_results_from_es)
        results.append({'topics': topics, 'result': res, 'topicid': topicid})
    results = add_keywords(results, kera)
    df = pd.DataFrame(results)
    df.to_csv('nowiki_4_with_kera_250_topics.csv', encoding='utf-8')


main()