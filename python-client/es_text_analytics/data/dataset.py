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
    self_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.abspath(os.path.join(self_path, '..', '..', '..'))


def default_dataset_path():
    """
    Returns the data default dataset location in the project directory.

    :rtype : str|unicode
    :return: the path to the default dataset location
    """
    return os.path.join(project_path(), 'data')
