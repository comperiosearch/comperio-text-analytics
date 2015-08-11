import logging
from argparse import ArgumentParser
import sys

from elasticsearch.client import Elasticsearch

from es_text_analytics.data.newsgroups import NewsgroupsDataset

"""
Script for retrieving and indexing datasets.

Current datasets supported:
- 20 Newsgroups
"""


def main():
    parser = ArgumentParser()
    parser.add_argument('-e', '--elasticsearch-server', default='localhost:9200')
    parser.add_argument('-d', '--dataset')
    opts = parser.parse_args()

    es_hosts = [opts.elasticsearch_server]
    dataset_name = opts.dataset

    es = Elasticsearch(hosts=es_hosts, timeout=120)

    if dataset_name == 'newsgroups':
        dataset = NewsgroupsDataset(es)
    else:
        logging.error('Unknown dataset %s ...' % dataset_name)
        sys.exit(1)

    dataset.install()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    main()
