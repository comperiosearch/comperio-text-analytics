import logging
from argparse import ArgumentParser
import re
import sys
import re
from gensim import corpora
from gensim.corpora import Dictionary
from gensim.models.lsimodel import LsiModel
from gensim.models.ldamodel import LdaModel
from gensim.models.word2vec import Word2Vec
from gensim.models.hdpmodel import HdpModel
from gensim.models.tfidfmodel import TfidfModel

from es_text_analytics.data.wikipedia import WikipediaDataset
from es_text_analytics.data.elasticsearch_dataset import ElasticsearchDataset
from nltk.corpus import stopwords


def fast_tokenize(str):
    return [x.lower() for x in re.findall('[^\W\d_]+', str, re.MULTILINE | re.UNICODE)]


def normalize_es(doc):
    return doc['_source']['article']


def normalize_wiki(doc):
      return doc['article.text']


def normalize_file(doc):
    return doc.split('\t')[1]


def get_tokenized(page, sw):
      return [token for token in fast_tokenize(page) if token not in sw and len(token) > 1]



import re
import string
import tarfile
import codecs
from es_text_analytics.data.dataset import Dataset
from elasticsearch.client import Elasticsearch
from elasticsearch.helpers import scan

"""
Elasticsearch as data source

"""


class FileDataset(Dataset):
    """
    Class encapsulating using a text file as datasource. Assumes file contains lines with documents.
    The formatting of the lines are up to you, but remember to extract what you need in the normalize_func
    """

    def __init__(self,  dump_fn, num_articles=None, normalize_func=None):
        super(FileDataset, self).__init__( normalize_func=normalize_func)
        self.dataset_fn = dump_fn


    def _iterator(self):
        with codecs.open(self.dataset_fn, 'r', encoding='utf-8') as f:
            for line in f:
                yield line




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
            doc = get_tokenized(page, self.stopwords)
            if self.doc2bow:
                yield self.vocabulary.doc2bow(doc)
            else:
                yield doc


# wikidata download https://dumps.wikimedia.org/nowiki/latest/nowiki-latest-pages-articles.xml.bz2
def main():
    parser = ArgumentParser(
        description='wrapper script for churning datasets of wiki or elasticsearch kind through gensim to produce topic models please see gensim documentation for more information')
    parser.add_argument('-ds', '--dataset', default='wiki', help='What kind of dataset to use. (wiki,es,file)')
    parser.add_argument('-d', '--dump-file', help='Wiki: bz2 dump file with wiki in it')
    parser.add_argument('-l', '--limit', help='Wiki: How many documents to extract from wiki')
    parser.add_argument('--model-id', default='model', help='Filename for created model.')
    parser.add_argument('--model-type', default='lsi', help='Model type (lsi, lda, word2vec, hdp, vocabulary).')
    parser.add_argument('--n-topics', default=10, help='Number of topics to model.')
    parser.add_argument('--n-passes', default=1, help='Number of passes for LDA  model.')
    parser.add_argument('--w2v-size', default=100, help='size of Word2Vec context.')
    parser.add_argument('--w2v-window',  default=5, help='window for Word2Vec.')
    parser.add_argument('-q', '--query', default=None, help='Elasticsearch: Query to use to fetch documents')
    parser.add_argument('--index', help='Elasticsearch: index to read from.')
    parser.add_argument('--doc_type', default='doc', help='Elasticsearch: data type in index.')
    parser.add_argument('--data-dir', help='Directory to save the generated models and vocabularies into.')
    parser.add_argument('--vocab',  help='Prebuilt Vocabulary file. Use this to avoid having to generate one.')

    opts = parser.parse_args()

    model_type = opts.model_type.lower()
    if model_type not in ['lsi', 'lda', 'word2vec', 'hdp', 'vocabulary']:
        logging.error("Invalid model type %s" % model_type)
        parser.print_usage()
        exit(-1)

    logging.info("Using model type %s" % model_type)

    dump_fn = opts.dump_file
    limit = int(opts.limit) if opts.limit else None

    data_type = opts.dataset.lower()
    if data_type not in ['es', 'wiki', 'file']:
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
        logging.error(
            "Please be kind to at least specify the index you want to fetch from elasticsearch using the --index parameter")
        sys.exit(1)

    n_topics = int(opts.n_topics)
    n_passes = int(opts.n_passes)
    logging.info("Using %d topics." % n_topics)
    data_dir = opts.data_dir
    model_id = opts.model_id
    model_fn = '%s_%s_%d' % (model_id, model_type, n_topics)
    if data_dir:
        model_fn = '%s/%s' % (data_dir, model_fn)
    if model_type == 'word2vec':
        w2v_size = int(opts.w2v_size)
        w2v_window = int(opts.w2v_window)
        model_fn = '%s_w_%s_s_%s' % (model_fn, w2v_window, w2v_size)
    logging.info("Writing models to %s." % model_fn)

    if data_type == 'es':
        logging.info("Using data type %s with index %s, doc_type %s query %s" % (data_type, index, doc_type, query))
        dataset = ElasticsearchDataset(read_index=index, read_doc_type=doc_type, query=query,
                                       normalize_func=normalize_es)
    elif data_type == 'wiki':
        logging.info("Using data type %s with dump_file %s and limit %s" % (data_type, dump_fn, limit))
        dataset = WikipediaDataset(dump_fn=dump_fn, num_articles=limit, normalize_func=normalize_wiki)
    elif data_type == 'file':
        logging.info("Using data type %s with dump_file %s and limit %s" % (data_type, dump_fn, limit))
        dataset = FileDataset(dump_fn=dump_fn, num_articles=limit, normalize_func=normalize_file)
    vocab_file = opts.vocab
    vocab = Dictionary()
    sw = set(stopwords.words('norwegian'))
    if not vocab_file or model_type == 'vocabulary':
        vocab.add_documents([get_tokenized(page, sw) for page in dataset])
        vocab.filter_extremes()
        vocab.compactify()
        vocab.save(model_fn + '.vocab')
    else:
        vocab = Dictionary.load(vocab_file)
    if model_type == 'vocabulary':
        return
    tfidf = TfidfModel(dictionary=vocab)
    if model_type == 'lsi':
        corpus = IterableDataset(dataset, sw, vocab)
        model = LsiModel(corpus=tfidf[corpus], num_topics=n_topics,
                         id2word=vocab)
    elif model_type == 'lda':
        corpus = IterableDataset(dataset, sw, vocab)
        model = LdaModel(corpus=tfidf[corpus], num_topics=n_topics, passes=n_passes,
                         id2word=vocab)

    elif model_type == 'word2vec':
        corpus = IterableDataset(dataset, sw, vocab, doc2bow=False)
        corpus.dictionary = vocab
        model = Word2Vec(sentences=corpus, window=w2v_window, size=w2v_size)
    elif model_type == 'hdp':
        corpus = IterableDataset(dataset, sw, vocab)
        model = HdpModel(corpus=tfidf[corpus], id2word=vocab)

    logging.info(model)
    model.save(model_fn)


if __name__ == '__main__':
    logformat = '%(asctime)s %(name)-12s: %(message)s'
    logging.basicConfig(level=logging.INFO, format=logformat, filename='wiki-topicmodel.log' )
    console = logging.StreamHandler()
    formatter = logging.Formatter(logformat)
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    main()

    # ########## sample usage
    #
    #--model-type=lda -d F:/projects/elasticsearch-enterprise-system/data/nowiki-20150901-pages-articles.xml.bz2 -l 100 --n-topics 10
    #--model-type=lda -ds es  --n-topics 10 --index wiki --query "{\"query\":{\"match\": {\"_all\":\"kongo\"}}}"
    #--model-type=word2vec -ds es   --index wiki --w2v_window=7 --w2v_size=75
    #--model-type=hdp -d F:/projects/elasticsearch-enterprise-system/data/nowiki-20150901-pages-articles.xml.bz2 -l 100 --n-topics 10
    #--model-type=lda -ds file  --n-topics 10 -d f:/projects/comperio-text-analytics/models/dump
