import logging
from argparse import ArgumentParser
import re
import sys

from gensim.corpora import Dictionary
from gensim.models.lsimodel import LsiModel
from nltk.corpus import stopwords

from es_text_analytics.data.wikipedia import WikipediaDataset


def fast_tokenize(str):
    return re.findall('[^\W\d_]+', str, re.MULTILINE|re.UNICODE)


def main():
    parser = ArgumentParser()
    parser.add_argument('-d', '--dump-file')
    parser.add_argument('-l', '--limit')

    opts = parser.parse_args()

    dump_fn = opts.dump_file
    limit = int(opts.limit) if opts.limit else None

    if not dump_fn:
        logging.error('--dump-file required')
        sys.exit(1)

    if limit:
        logging.info('processing %d articles' % limit)

    dataset = WikipediaDataset(dump_fn=dump_fn, num_articles=limit)

    vocab = Dictionary()

    sw = set(stopwords.words('norwegian'))

    vocab.add_documents(([token.lower() for token in fast_tokenize(page['article.text'])
                          if token not in sw]
                         for page in dataset))
    vocab.filter_extremes()
    vocab.compactify()

    print vocab

    model = LsiModel(corpus=(vocab.doc2bow(doc) for doc
                             in ([token.lower() for token in fast_tokenize(page['article.text'])
                                  if token not in sw]
                                 for page in dataset)),
                     id2word=vocab)

    print model
    print model.show_topics()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    main()