import logging
from argparse import ArgumentParser
import sys
import re

from gensim.corpora import Dictionary
from gensim.models.lsimodel import LsiModel
from gensim.models.ldamodel import LdaModel
from gensim.models.word2vec import Word2Vec
from gensim.models.hdpmodel import HdpModel
from gensim.models.tfidfmodel import TfidfModel

from es_text_analytics.data.wikipedia import WikipediaDataset
from es_text_analytics.data.elasticsearch_dataset import ElasticsearchDataset
from nltk.corpus import stopwords


class IterableDataset(object):
        def __init__(self, args_dataset, stopwords, vocabulary, doc2bow=True):
            self.dataset = args_dataset
            self.doc2bow = doc2bow
            self.stopwords = stopwords
            self.vocabulary = vocabulary

        def __len__(self):
            return sum(1 for _ in self.dataset)

        def __iter__(self):
            for page in self.dataset:
                doc = [token.lower() for token in fast_tokenize(page) if token not in self.stopwords]
                if self.doc2bow:
                    yield self.vocabulary.doc2bow(doc)
                else:
                    yield doc


def fast_tokenize(str):
    return re.findall('[^\W\d_]+', str, re.MULTILINE | re.UNICODE)

def normalize_es(doc):
    return doc['_source']['article']

def normalize_wiki(doc):
    return doc['article.text']

def main():
    parser = ArgumentParser(description='wrapper script for churning datasets of wiki or elasticsearch kind through gensim to produce topic models please see gensim documentation for more information')
    parser.add_argument('-ds', '--dataset', default='wiki', help='What kind of dataset to use. (wiki or es)')
    parser.add_argument('-d', '--dump-file', help='Wiki: bz2 dump file with wiki in it')
    parser.add_argument('-l', '--limit', help='Wiki: How many documents to scrape from wiki')
    parser.add_argument('--model-id', default='model', help='Filename for created model.')
    parser.add_argument('--model-type', default='lsi', help='Model type (lsi, lda, word2vec, hdp).')
    parser.add_argument('--n-topics', default=10, help='Number of topics to model.')
    parser.add_argument('--context', default='document', help='Context (document or sentence).')
    parser.add_argument('-q', '--query', default=None, help='Elasticsearch: Query to use to fetch documents')
    parser.add_argument('--index',  help='Elasticsearch: index to read from.')
    parser.add_argument('--doc_type', default='doc', help='Elasticsearch: data type in index.')

    opts = parser.parse_args()

    context = opts.context.lower()

    if context not in ['sentence', 'document']:
        logging.error("Invalid context %s" % context)
        parser.print_usage()
        exit(-1)
    logging.info("Using %s contexts." % context)

    model_type = opts.model_type.lower()
    if model_type not in ['lsi', 'lda', 'word2vec',  'hdp']:
        logging.error("Invalid model type %s" % model_type)
        parser.print_usage()
        exit(-1)

    logging.info("Using model type %s" % model_type)

    dump_fn = opts.dump_file

    data_type = opts.dataset.lower()
    if data_type not in ['es', 'wiki']:
        logging.error("Invalid dataset  type %s" % data_type)
        parser.print_usage()
        exit(-1)
    limit = None
    if opts.limit:
        limit = int(opts.limit)
    if not dump_fn and data_type in ['wiki']:
        logging.error('--dump-file required for wiki dataset')
        sys.exit(1)

    query = opts.query
    index = opts.index
    doc_type = opts.doc_type
    if data_type == 'es' and index is None:
        logging.error("Please be kind to at least specify the index you want to fetch from elasticsearch using the --index parameter")
        sys.exit(1)


    n_topics = int(opts.n_topics)

    logging.info("Using %d topics." % n_topics)

    model_id = opts.model_id
    model_fn = '%s_%s_%d_%s' % (model_id, model_type, n_topics, context)

    logging.info("Writing models to %s." % model_fn)

    if data_type == 'es':
        logging.info("Using data type %s with index %s, doc_type %s query %s" % (data_type, index, doc_type, query))
        dataset = ElasticsearchDataset(read_index=index, read_doc_type=doc_type, query=query,
                                       normalize_func=normalize_es)

    else:
        logging.info("Using data type %s with dump_file %s and limit %s" % (data_type, dump_fn, limit))
        dataset = WikipediaDataset(dump_fn=dump_fn, num_articles=limit, normalize_func=normalize_wiki)

    vocab = Dictionary()

    sw = set(stopwords.words('norwegian'))

    vocab.add_documents(([token.lower() for token in fast_tokenize(page)
                          if token not in sw]
                         for page in dataset))
    vocab.filter_extremes()
    vocab.compactify()
    vocab.save(model_fn + '.vocab')


    tfidf = TfidfModel(dictionary=vocab)
    if model_type == 'lsi':
        corpus = IterableDataset(dataset,  sw, vocab)
        model = LsiModel(corpus=tfidf[corpus], num_topics=n_topics,
                         id2word=vocab)
    elif model_type == 'lda':
        corpus = IterableDataset(dataset, sw, vocab)
        model = LdaModel(corpus=corpus, num_topics=n_topics,
                         id2word=vocab)

    elif model_type == 'word2vec':
        corpus = IterableDataset(dataset, sw, vocab, doc2bow=False)
        corpus.dictionary = vocab
        model = Word2Vec(sentences=corpus)
        print model.most_similar(positive=['kvinne', 'konge'], negative=['mann'], topn=2)
        print model.doesnt_match("oslo akershus regjerningen drammen".split())
    elif model_type == 'hdp':
        corpus = IterableDataset(dataset, sw, vocab)
        model = HdpModel(corpus=tfidf[corpus], id2word=vocab)
        print model.show_topics()

    print model
    model.save(model_fn)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    main()
########### sample usage
#
#--model-type=lda -d F:/projects/elasticsearch-enterprise-system/data/nowiki-20150901-pages-articles.xml.bz2 -l 100 --n-topics 10
#--model-type=lda -ds es  --n-topics 10 --index wiki --query "{\"query\":{\"match\": {\"_all\":\"kongo\"}}}"
#--model-type=word2vec -ds es   --index wiki
#--model-type=hdp -d F:/projects/elasticsearch-enterprise-system/data/nowiki-20150901-pages-articles.xml.bz2 -l 100 --n-topics 10