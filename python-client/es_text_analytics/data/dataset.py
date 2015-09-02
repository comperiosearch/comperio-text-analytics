from abc import abstractmethod
from abc import ABCMeta
import logging
import os
from urlparse import urlparse

from elasticsearch.client import IndicesClient
import requests

BULK_REQUEST_SIZE = 100

CONLL_U_FIELDS = ['index', 'form', 'lemma', 'cpostag', 'postag', 'feats',
                  'head', 'deprel', 'deps', 'misc']


def fn_from_url(url):
    """
    Extract the final part of an url in order to get the filename of a downloaded url.

    :param url: url string
    :type url : str|unicode
    :rtype : str|unicode
    :return: url filename part
    """
    parse = urlparse(url)

    return os.path.basename(parse.path)


def download_file(url, dest_path):
    """
    Download the file pointed to by the url to the path specified or the defult dataset location.
    If the dfile is already present at the path it will not be downloaded and the path to this file
    is returned.

    :param url: url string pointing to the file
    :type url : str|unicode
    :param dest_path: path to location where the file will be stored locally
    :type dest_path : str|unicode
    :rtype : str|unicode
    :return: path to the downloaded dataset
    """
    if not os.path.exists(dest_path):
        os.makedirs(dest_path)

    fn = fn_from_url(url)
    full_fn = os.path.join(dest_path, fn)

    if os.path.exists(full_fn):
        logging.info('Dataset archive %s already exists in %s ...' % (fn, dest_path))
    else:
        r = requests.get(url, stream=True)
        with open(full_fn, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()

    return full_fn


def project_path():
    """
    Returns the path to the root project directory.

    :rtype : str|unicode
    :return: The root project path as a string.
    """
    self_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.abspath(os.path.join(self_path, '..', '..', '..'))


def default_dataset_path():
    """
    Returns the data default dataset location in the project directory.

    :rtype : str|unicode
    :return: the path to the default dataset location
    """
    return os.path.join(project_path(), 'data')


def parse_conll(fileobj, field_indices=None):
    """
    Parse a CONLL formatted dependency treebank file. Supports the CONLL-U format
    with UTF-8 encoding.

    :param fileobj: A file like instance with CONLL formatted text.
    :rtype : generator
    """
    sentence = []

    for line in fileobj:
        line = line.decode('utf-8')
        line = line.strip()

        if line == '':
            if sentence:
                yield sentence

            sentence = []

            continue

        row = line.split(u'\t')
        row[0] = int(row[0])

        if field_indices:
            row = [row[i] for i in field_indices]

        sentence.append(row)

    if sentence:
        yield sentence


class Dataset:
    """
    Base class for self-installable and self-indexable datasets.

    Contains base methods for downloading the dataset and creating Elasticsearch index based on it.
    """
    __metaclass__ = ABCMeta

    def __init__(self, index=None, doc_type=None, dataset_path=None, dataset_fn=None,
                 normalize_func=None):
        """
        Initialize the instance with optional Elasticsearch index information.

        :param index: Elasticsearch index where the dataset will be stored if indexed.
        :type index: str|unicode
        :param doc_type:
        :type doc_type: str|unicode
        :param dataset_path: location where dataset wiil be downloaded. If None the default location is used.
        :type dataset_path: None|str|unicode
        :param dataset_fn: Location of the dataset. If this argument is used the file specified will be used and
          the archive will not be downloaded automatically if not present.
        :type dataset_fn: None|str|unicode
        :param normalize_func: Function to normalize corpus documemt format. Default will create a dict with a field
          that contains the full document text. Exact format is corpus dependent.
        :type normalize_func: function|None
        """
        self.es_index = index
        self.es_doc_type = doc_type
        self.dataset_fn = dataset_fn
        self.archive_fn = None
        self.normalize_func = normalize_func

        self.dataset_path = dataset_path

        if not dataset_path:
            self.dataset_path = default_dataset_path()

    @abstractmethod
    def _iterator(self):
        """
        Subclasses should implement this method returning a generator yielding
        dicts with the document data.
        """
        raise NotImplementedError

    def __iter__(self):
        if not self.dataset_fn:
            raise ValueError()

        for doc in self._iterator():
            try:
                if self.normalize_func:
                    doc = self.normalize_func(doc)
            except Exception:
                logging.error('Unable to normalize doc ...')

            yield doc

    def index(self, es):
        """
        Index the dataset in the given index with archive in the dataset location.

        :param es: Elasticsearch client instance
        :type es: elasticsearch.client.Elasticsearch
        :rtype : elasticsearch.client.Elasticsearch
        :return: :raise ValueError:
        """
        docs = []
        count = 0

        for doc in self:
            docs += [{'index': {'_index': self.es_index, '_type': self.es_doc_type}}, doc]
            count += 1

            if len(docs) % (2 * BULK_REQUEST_SIZE) == 0:
                es.bulk(index=self.es_index, doc_type=self.es_doc_type, body=docs)
                logging.info('Added %d documents ...' % count)
                docs = []

        if docs:
            es.bulk(index=self.es_index, doc_type=self.es_doc_type, body=docs)
            logging.info('Added %d documents ...' % count)

        return self

    def delete_index(self, es):
        """
        Delete the dataset index.

        :param es: Elasticsearch client instance
        :type es: elasticsearch.client.Elasticsearch
        :rtype : NewsgroupsDataset
        """
        ic = IndicesClient(es)
        ic.delete(index=self.es_index, ignore=[400, 404])

        return self

    def install(self, es=None):
        """
        Install and optionally index the dataset.
        WARNING: Deletes the index before installing.

        :param es: Pass an Elasticsearch client instance to index the dataset.
        :type es: None|elasticsearch.client.Elasticsearch
        :rtype : Dataset
        """
        if self.dataset_fn:
            logging.warn('Dataset initialized directly or already installed ...')
            return self
        else:
            self.dataset_fn = download_file(self.archive_fn, dest_path=self.dataset_path)

        if es:
            logging.info("Creating Elasticsearch index %s ..." % self.index)
            self.delete_index(es)
            self.index(es)

        return self
