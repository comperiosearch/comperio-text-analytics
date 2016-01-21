import os

from sklearn import datasets
from sklearn.datasets import twenty_newsgroups

from es_text_analytics.data.dataset import Dataset

"""
The 20 Newsgroups dataset is a standardized dataset with Newsgroup messages.

http://qwone.com/~jason/20Newsgroups/
"""

NEWSGROUPS_ARCHIVE_URL = 'http://qwone.com/~jason/20Newsgroups/20news-18828.tar.gz'


def iterator(dataset_fn):
    """
    Provides an iterator of parsed documents from the 20 Newsgroups dataset.

    :param dataset_fn: Path to Newsgroups dataset archive file.
    :type dataset_fn: unicode|str
    :rtype : generator
    """
    ng = datasets.fetch_20newsgroups()

    for article, group, target, filename in zip(ng['data'], [ng['target_names'][x] for x in ng['target']],
                                                ng['target'], ng['filenames']):
        article = twenty_newsgroups.strip_newsgroup_header(article)
        article = twenty_newsgroups.strip_newsgroup_footer(article)
        article = twenty_newsgroups.strip_newsgroup_quoting(article)
        doc_id = os.path.basename(filename)

        yield {'doc_id': doc_id, 'article': article, 'group': group, 'target': target, 'filename': filename}


class NewsgroupsDataset(Dataset):
    """
    Class encapsulating the Newsgroups dataset and the information needed to retrieve and index it.

    Currently only downloads and index the dataset in Elasticsearch.
    """

    def __init__(self, index='newsgroups', doc_type='message', dataset_path=None):
        super(NewsgroupsDataset, self).__init__(index=index, doc_type=doc_type, dataset_path=dataset_path)


    def _iterator(self):
        return iterator(self.dataset_fn)
