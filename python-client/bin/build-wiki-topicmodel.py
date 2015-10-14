import logging
from argparse import ArgumentParser
import sys

from gensim.corpora import Dictionary

from gensim.models.lsimodel import LsiModel

from es_text_analytics.data.wikipedia import WikipediaDataset
from es_text_analytics.tokenizer import NOTokenizer


def main():
    parser = ArgumentParser()
    parser.add_argument('-d', '--dump-file')

    opts = parser.parse_args()

    dump_fn = opts.dump_file

    if not dump_fn:
        logging.error('--dump-file required')
        sys.exit(1)

    dataset = WikipediaDataset(dump_fn=dump_fn, num_articles=100)

    tokenizer = NOTokenizer()
    vocab = Dictionary()

    vocab.add_documents(([token.lower() for token in tokenizer.tokenize(page['article.text'])
                          if token.isalpha()]
                         for page in dataset))
    vocab.filter_extremes()
    vocab.compactify()

    print vocab

    model = LsiModel(corpus=(vocab.doc2bow([token.lower() for token in tokenizer.tokenize(page['article.text'])
                                            if token.isalpha()])
                             for page in dataset),
                     id2word=vocab)

    print model


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    main()