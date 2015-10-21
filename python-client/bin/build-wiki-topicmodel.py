import logging
from argparse import ArgumentParser
import sys

from gensim.corpora import Dictionary
from gensim.models.lsimodel import LsiModel
from gensim.models.ldamodel import LdaModel
from gensim.models.word2vec import Word2Vec

from es_text_analytics.data.wikipedia import WikipediaDataset
from es_text_analytics.data.elasticsearch_dataset import ElasticsearchDataset

from nltk.corpus import stopwords
import re


def fast_tokenize(str):
    return re.findall('[^\W\d_]+', str, re.MULTILINE | re.UNICODE)

def normalize_es(doc):
    return doc['_source']['article']

def normalize_wiki(doc):
    return doc['article.text']

def main():
    parser = ArgumentParser()
    parser.add_argument('-ds', '--dataset', default='wiki', help='What kind of dataset to use. wiki or es')
    parser.add_argument('-d', '--dump-file', help='Wiki: bz2 dump file with wiki in it')
    parser.add_argument('-l', '--limit', help='Wiki: How many documents to scrape from wiki')
    parser.add_argument('--model-id', default='model', help='Filename for created model.')
    parser.add_argument('--model-type', default='lsi', help='Model type (lsi or lda or word2vec).')
    parser.add_argument('--n-topics', default=10, help='Number of topics to model.')
    parser.add_argument('--context', default='document', help='Context (document or sentence).')
    parser.add_argument('-q', '--query', default=None, help='Elasticsearch: Query to use to fetch documents')
    parser.add_argument('--index', default='wiki', help='Elasticsearch: index to read from.')
    parser.add_argument('--doc_type', default='doc', help='Elasticsearch: data type in index.')

    opts = parser.parse_args()

    context = opts.context.lower()

    if context not in ['sentence', 'document']:
        logging.error("Invalid context %s" % context)
        parser.print_usage()
        exit(-1)
    logging.info("Using %s contexts." % context)

    model_type = opts.model_type.lower()
    if model_type not in ['lsi', 'lda', 'word2vec']:
        logging.error("Invalid model type %s" % model_type)
        parser.print_usage()
        exit(-1)

    logging.info("Using model type %s" % model_type)

    dump_fn = opts.dump_file
    limit = int(opts.limit)
    if not dump_fn and data_type in ['wiki']:
        logging.error('--dump-file required for wiki dataset')
        sys.exit(1)
    if not limit:
        limit = None

    query = opts.query
    index = opts.index
    doc_type = opts.doc_type

    data_type = opts.dataset.lower()
    if data_type not in ['es', 'wiki']:
        logging.error("Invalid dataset  type %s" % data_type)
        parser.print_usage()
        exit(-1)

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

    def get_corpus(arg_dataset):
        return (vocab.doc2bow(doc) for doc
                in ([token.lower() for token in fast_tokenize(page)
                     if token not in sw]
                    for page in arg_dataset))



    class MyCorpus(object):
        def __init__(self, args_dataset):
            self.dataset = args_dataset
        def __iter__(self):
            for page in self.dataset:
                yield (vocab.doc2bow(doc) for doc in ([token.lower() for token in fast_tokenize(page)  if token not in sw]))


    if model_type == 'lsi':
        model = LsiModel(corpus=get_corpus(dataset),
                         id2word=vocab)
    elif model_type == 'lda':
        coprus = MyCorpus(dataset)
        coprus.dictionary = vocab
        model = LdaModel(corpus=coprus,
                         id2word=vocab, passes=1)

    # elif model_type == 'word2vec':
    # model =

    print model
    model.save(model_fn)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    main()