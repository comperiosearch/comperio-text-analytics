import logging
from argparse import ArgumentParser
import sys

from gensim.corpora import Dictionary
from textblob import TextBlob

from es_text_analytics.data import newsgroups
from es_text_analytics.data.dataset import download_file, default_dataset_path

"""
Generates wordcounts from a dataset.

Stores the counts in a Gensim Dictionary text file with id, word and count as tab separated fields.
"""


def preprocess(doc):
    return [w.lower() for w in TextBlob(doc['msg']).words]


def main():
    parser = ArgumentParser()
    parser.add_argument('-d', '--dataset')
    parser.add_argument('-p', '--dataset-path', default=default_dataset_path())
    parser.add_argument('-o', '--output')
    opts = parser.parse_args()

    dataset_name = opts.dataset
    dataset_path = opts.dataset_path
    out_fn = opts.output

    if not out_fn:
        logging.error('--output argument required ...')
        parser.print_usage()
        sys.exit(1)

    if not dataset_name:
        logging.error('--dataset argument required ...')
        parser.print_usage()
        sys.exit(1)

    if dataset_name == 'newsgroups':
        corpus = (preprocess(doc) for doc
                  in newsgroups.iterator(download_file(newsgroups.NEWSGROUPS_ARCHIVE_URL, dataset_path)))
    else:
        logging.error('Unknown dataset %s ...' % dataset_name)
        sys.exit(1)

    d = Dictionary(corpus)
    d.save_as_text(out_fn, sort_by_word=False)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
