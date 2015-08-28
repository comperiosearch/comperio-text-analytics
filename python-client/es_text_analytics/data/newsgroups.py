import re
import string
import tarfile

from es_text_analytics.data.dataset import Dataset

"""
The 20 Newsgroups dataset is a standardized dataset with Newsgroup messages.

http://qwone.com/~jason/20Newsgroups/
"""

NEWSGROUPS_ARCHIVE_URL = 'http://qwone.com/~jason/20Newsgroups/20news-18828.tar.gz'


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


def iterator(dataset_fn):
    """
    Provides an iterator of parsed documents from the 20 Newsgroups dataset.

    :param dataset_fn: Path to Newsgroups dataset archive file.
    :type dataset_fn: unicode|str
    :rtype : generator
    """
    with tarfile.open(dataset_fn, 'r:gz') as f:
        for member in f:
            if member.isfile():
                _, group, doc_id = member.path.split('/')

                m_f = f.extractfile(member)
                # extract content and remove unprintable characteres such as ascii control sequences
                # TODO regex is probably more efficient than filter
                msg = filter(string.printable.__contains__, m_f.read())
                m_f.close()

                doc = parse(msg)
                doc['group'] = group
                doc['doc_id'] = doc_id


                yield doc


class NewsgroupsDataset(Dataset):
    """
    Class encapsulating the Newsgroups dataset and the information needed to retrieve and index it.

    Currently only downloads and index the dataset in Elasticsearch.
    """

    def __init__(self, index='newsgroups', doc_type='message', dataset_path=None):
        super(NewsgroupsDataset, self).__init__(index=index, doc_type=doc_type, dataset_path=dataset_path)

        self.archive_fn = NEWSGROUPS_ARCHIVE_URL

    def _iterator(self):
        return iterator(self.dataset_fn)
