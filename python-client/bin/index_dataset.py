import logging
from argparse import ArgumentParser
import sys

from elasticsearch.client import Elasticsearch

from es_text_analytics.data.aviskorpus import AviskorpusDataset
from es_text_analytics.data.ndt_dataset import NDTDataset
from es_text_analytics.data.newsgroups import NewsgroupsDataset

"""
Script for retrieving and indexing datasets.

Current datasets supported:
- 20 Newsgroups (newsgroups)
- Norsk Aviskorpus (aviskorpus), sections and sources can be specified with f.ex. -s 1|2-aa|vg|db
- Norwegian Dependency Treebank (ndt), sections and languages can be specified with f.ex -s newspaper|blog-nob
"""


def main():
    parser = ArgumentParser()
    parser.add_argument('-e', '--elasticsearch-server', default='localhost:9200')
    parser.add_argument('-d', '--dataset')
    parser.add_argument('-s', '--sections')
    opts = parser.parse_args()

    es_hosts = [opts.elasticsearch_server]
    dataset_name = opts.dataset
    dataset_sections = opts.sections

    es = Elasticsearch(hosts=es_hosts, timeout=120)

    if dataset_name == 'newsgroups':
        dataset = NewsgroupsDataset()
    elif dataset_name == 'aviskorpus':
        sections = None
        sources = None

        if dataset_sections:
            try:
                sections, sources = dataset_sections.split('-')
                sections = [int(s) for s in sections.split('|')]
                sources = [s for s in sources.split('|')]
            except Exception:
                logging.error('Malformed section specification "%s" ...' % dataset_sections)
                sys.exit(1)

        dataset = AviskorpusDataset(sections=sections, sources=sources)
    elif dataset_name == 'ndt':
        sections = None
        lang = None

        if dataset_sections:
            try:
                sections, lang = dataset_sections.split('-')
                sections = [int(s) for s in sections.split('|')]
                lang = [s for s in lang.split('|')]
            except Exception:
                logging.error('Malformed section specification "%s" ...' % dataset_sections)
                sys.exit(1)

        dataset = NDTDataset(lang=lang, sections=sections)
    else:
        logging.error('Unknown dataset %s ...' % dataset_name)
        sys.exit(1)

    dataset.install(es)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    main()
