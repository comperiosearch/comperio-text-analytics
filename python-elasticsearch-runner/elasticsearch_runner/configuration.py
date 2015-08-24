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
        'marvel': {'agent': {'enabled'}},
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
        cluster_name = 'elasticsearch_runner_%7d' % randint(1, 9999999)
    config['cluster'] = {'name': cluster_name}

    if log_path or data_path:
        path = {}

        if log_path:
            path['log'] = log_path

        if data_path:
            path['data'] = data_path

        config['path'] = path

    return config


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