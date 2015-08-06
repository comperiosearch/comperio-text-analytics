import logging
import re
import string
import tarfile

from elasticsearch.client.indices import IndicesClient

from es_text_analytics.data.dataset import download_file, default_dataset_path

"""
The 20 Newsgroups dataset is a standardized dataset with Newsgroup messages.

http://qwone.com/~jason/20Newsgroups/
"""

NEWSGROUPS_ARCHIVE_URL = 'http://qwone.com/~jason/20Newsgroups/20news-18828.tar.gz'
BULK_REQUEST_SIZE = 100


def match_header_line(line):
    """
    Match a header line and potentially return the header info.

    :param line: line from Newsgroup message
    :type line : str|unicode
    :rtype : None|(str|unicode,str|unicode)
    :return: None or header key and value as a tuple
    """
    m = re.match('^(From|Subject): (.*)', line)

    if m:
        return m.group(1).lower(), m.group(2)
    else:
        return None


def parse(msg):
    """
    Parses a Newsgroup message into  a dict with header fields/values (from, subject), the message (msg) and a
    separate signature (sig) if detected.
    The unparsed message is also stored in the raw field.

    :type msg : str|unicode
    :rtype : dict
    :param msg: Newsgroup message string
    :return: A dict with parsed document contents.
    """
    doc = {'raw': msg}
    lines = msg.split('\n')

    m = match_header_line(lines[0])
    while m:
        key, val = m
        doc[key] = val
        lines.pop(0)
        m = match_header_line(lines[0])

    try:
        sig_idx = lines[::-1].index('--')

        doc['msg'] = '\n'.join(lines[:-(sig_idx + 1)])
        doc['sig'] = '\n'.join(lines[-sig_idx:])
    except ValueError:
        doc['msg'] = '\n'.join(lines)

    return doc


class NewsgroupsDataset:
    """
    Class encapsulating the Newsgroups dataset and the information needed to retrieve and index it.

    Currently only downloads and index the dataset in Elasticsearch.
    """

    def __init__(self, es, index='newsgroups', doc_type='message', dataset_path=None):
        """
        Initialize the instance with Elasticsearch server and index information.

        :param es: Elasticsearch client instance
        :type es: elasticsearch.client.Elasticsearch
        :param index: Elasticsearch index where the dataset will be stored
        :type index: str|unicode
        :param doc_type:
        :type doc_type: str|unicode
        :param dataset_path: location where dataset wiil be downloaded. If None the default location is used.
        :type dataset_path: None|str|unicode
        """
        self.es = es
        self.es_index = index
        self.es_doc_type = doc_type
        self.dataset_fn = None

        if not dataset_path:
            self.dataset_path = default_dataset_path()
        else:
            self.dataset_path = dataset_path

    def install(self):
        """
        Install and index the dataset.
        WARNING: Deletes the index before installing.

        :rtype : None
        """
        self.delete_index()
        self.dataset_fn = download_file(NEWSGROUPS_ARCHIVE_URL, dest_path=self.dataset_path)
        self.index()

    def index(self):
        """
        Index the dataset in the given index with archive in the dataset location.

        :rtype : elasticsearch.client.Elasticsearch
        :return: :raise ValueError:
        """
        if not self.dataset_fn:
            raise ValueError

        docs = []
        count = 0

        with tarfile.open(self.dataset_fn, 'r:gz') as f:
            for member in f:
                if member.isfile():
                    _, group, doc_id = member.path.split('/')

                    m_f = f.extractfile(member)
                    # extract content and remove unprintable characteres such as ascii control sequences
                    # TODO regex is probablt more efficient than filter
                    msg = filter(string.printable.__contains__, m_f.read())
                    m_f.close()

                    doc = parse(msg)

                    docs += [{'index': {'_index': self.es_index, '_type': self.es_doc_type}}, doc]
                    count += 1

                    if len(docs) % (2 * BULK_REQUEST_SIZE) == 0:
                        self.es.bulk(index=self.es_index, doc_type=self.es_doc_type, body=docs)
                        logging.info('Added %d documents ...' % count)
                        docs = []

        if docs:
            self.es.bulk(index=self.index, doc_type=self.es_doc_type, body=docs)
            logging.info('Added %d documents ...' % count)

        return self.es

    def delete_index(self):
        """
        Delete the dataset index.

        :rtype : None
        """
        ic = IndicesClient(self.es)
        ic.delete(index=self.es_index, ignore=[400, 404])
