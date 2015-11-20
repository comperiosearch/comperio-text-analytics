import logging
from argparse import ArgumentParser
import re
import sys
import re
import codecs
from gensim.corpora import Dictionary
from gensim.models.tfidfmodel import TfidfModel
from gensim import corpora

from es_text_analytics.data.wikipedia import WikipediaDataset
from es_text_analytics.data.elasticsearch_dataset import ElasticsearchDataset
from nltk.corpus import stopwords

from es_text_analytics.tagger import NOBTagger, install_hunpos
from es_text_analytics.lemmatizer import OrdbankLemmatizer

def fast_tokenize(str):
    return [x.lower() for x in re.findall('[^\W\d_]+', str, re.MULTILINE | re.UNICODE)]

def normalize_es(doc):
    return doc['_source']['article']


def normalize_wiki(doc):
    return doc['id'], doc['article.text']


def get_tokenized(page, sw):
    return [token for token in fast_tokenize(page) if token not in sw and len(token) > 1]


class IterableDataset(object):
    def __init__(self, args_dataset, stopwords, nobtag, lemmatizer):
        self.dataset = args_dataset
        self.tagger = nobtag
        self.lem = lemmatizer
        self.stopwords = stopwords

    def __len__(self):
        return sum(1 for _ in self.dataset)

    def __iter__(self):
        for page in self.dataset:
            tokens = get_tokenized(page[1], self.stopwords)
            sent = self.tagger.tag(tokens, tokenize=False)
            yield page[0], " ".join([self.lem.lemmatize(word, tag) for word, tag in sent]).lower()


# wikidata download https://dumps.wikimedia.org/nowiki/latest/nowiki-latest-pages-articles.xml.bz2
def main():
    parser = ArgumentParser(
        description='wrapper script for churning datasets of wiki or elasticsearch kind through gensim to produce topic models please see gensim documentation for more information')
    parser.add_argument('-ds', '--dataset', default='wiki', help='What kind of dataset to use. (wiki or es)')
    parser.add_argument('-d', '--dump-file', help='Wiki: bz2 dump file with wiki in it')
    parser.add_argument('-l', '--limit', help='Wiki: How many documents to extract from wiki')
    parser.add_argument('--model-id', default='model', help='Filename for created model.')
    parser.add_argument('-q', '--query', default=None, help='Elasticsearch: Query to use to fetch documents')
    parser.add_argument('--index', help='Elasticsearch: index to read from.')
    parser.add_argument('--doc_type', default='doc', help='Elasticsearch: data type in index.')
    parser.add_argument('--data-dir', default='.',  help='Directory to save the generated models and vocabularies into.')

    opts = parser.parse_args()

    dump_fn = opts.dump_file
    limit = int(opts.limit) if opts.limit else None

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
        logging.error(
            "Please be kind to at least specify the index you want to fetch from elasticsearch using the --index parameter")
        sys.exit(1)

    data_dir = opts.data_dir
    model_id = opts.model_id
    model_fn = '%s' % (model_id)
    if data_dir:
        model_fn = '%s%s' % (data_dir, model_fn)
    logging.info("Writing models to %s." % model_fn)

    if data_type == 'es':
        logging.info("Using data type %s with index %s, doc_type %s query %s" % (data_type, index, doc_type, query))
        dataset = ElasticsearchDataset(read_index=index, read_doc_type=doc_type, query=query,
                                       normalize_func=normalize_es)
    else:
        logging.info("Using data type %s with dump_file %s and limit %s" % (data_type, dump_fn, limit))
        dataset = WikipediaDataset(dump_fn=dump_fn, num_articles=limit, normalize_func=normalize_wiki)
    sw = set(stopwords.words('norwegian'))
    #install_hunpos()
    nobtag = NOBTagger()
    ord = OrdbankLemmatizer()

    corpus = IterableDataset(dataset, sw, nobtag, ord)
    with codecs.open(model_fn, mode='w', encoding='utf-8') as fn:
        for document in corpus:
            logging.info(document[0])
            fn.write(str(document[0]) + '\t' + document[1] + '\n')



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

