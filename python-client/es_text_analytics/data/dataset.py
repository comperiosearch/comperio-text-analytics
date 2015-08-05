import logging
import os
from urlparse import urlparse

import requests


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


def download_dataset(url, dataset_path=None):
    """
    Download the dataset pointed to by the url to the dataset path specified or the defult dataset location.
    If the dataset is already present at the dataset path it will not be downloaded and the path to this dataset
    is returned.

    :param url: url string pointing to the dataset
    :type url : str|unicode
    :param dataset_path: path to location where the dataset will be stored locally
    :type dataset_path : str|unicode
    :rtype : str|unicode
    :return: path to the downloaded dataset
    """
    if not dataset_path:
        dataset_path = default_dataset_path()

    if not os.path.exists(dataset_path):
        os.makedirs(dataset_path)

    dataset_fn = fn_from_url(url)
    dataset_full_fn = os.path.join(dataset_path, dataset_fn)

    if os.path.exists(dataset_full_fn):
        logging.info('Dataset archive %s already exists in %s ...' % (dataset_fn, dataset_path))
    else:
        r = requests.get(url, stream=True)
        with open(dataset_full_fn, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()

    return dataset_full_fn


def default_dataset_path():
    """
    Returns the data default dataset location in the project directory.

    :rtype : str|unicode
    :return: the path to the default dataset location
    """
    self_path = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.abspath(os.path.join(self_path, '..', '..', '..', 'data'))

    return dataset_path
