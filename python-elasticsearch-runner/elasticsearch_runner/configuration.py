import os
from random import randint

import yaml


def generate_config(cluster_name=None, log_path=None, data_path=None):
    """
    Generates basic Elasticsearch configuration for setting up the runner.

    :param cluster_name: Set as cluster.name option.
    :type cluster_name: str|unicode
    :param log_path: Set as path.log option.
    :type log_path: str|unicode
    :param data_path: Set as path.data option.
    :type data_path str|unicode
    :rtype : dict
    :return: Elasticsearch configuration as dict.
    """
    config = {
        'marvel': {'agent': {'disabled'}},
        'index': {
            'number_of_shards': 1,
            'number_of_replicas': 0,
        },
        'http': {
            'cors': {
                'enabled': True
            }
        }
    }

    if not cluster_name:
        cluster_name = generate_cluster_name()

    config['cluster'] = {'name': cluster_name}

    if log_path or data_path:
        path = {}

        if log_path:
            path['log'] = log_path

        if data_path:
            path['data'] = data_path

        config['path'] = path

    return config


def generate_cluster_name(prefix='elasticsearch_runner'):
    """
    Generates a cluster name with a prefix and a random number.

    :param prefix: Cluster name prefix.
    :rtype : str|unicode
    :return: cluster name string

    TODO make this collision safe
    """
    cluster_name = '%s_%7d' % (prefix, randint(1, 9999999))

    return cluster_name


def serialize_config(stream, config):
    """
    Serialize Elasticsearch configuration dict to YAML formatted file.

    :param stream: Stream to write YAML configuration to.
    :param config: Elasticsearch configuration as dict.
    :type config: dict
    :rtype : dict
    :return: The passed configuration dict.
    """
    yaml.dump(config, stream=stream)

    return config


def package_path():
    """
    Returns the path to the root of the package directory.

    :rtype : str|unicode
    :return: The root project path as a string.
    """
    self_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.abspath(os.path.join(self_path, '..'))