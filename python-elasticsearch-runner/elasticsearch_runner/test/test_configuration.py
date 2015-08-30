from StringIO import StringIO
from unittest import TestCase

import yaml

from elasticsearch_runner.configuration import generate_config, serialize_config

__author__ = 'alynum'


class TestConfiguration(TestCase):
    def test_generate_config(self):
        self.assertEqual({
            'marvel': {'agent': {'disabled'}},
            'index': {
                'number_of_shards': 1,
                'number_of_replicas': 0,
            },
            'http': {
                'cors': {
                    'enabled': True
                }
            },
            'cluster': {'name': 'ba'}},
            generate_config(cluster_name='ba'))

    def test_serialize_config(self):
        s = StringIO()
        c = generate_config(cluster_name='ba')
        serialize_config(s, c)
        s.seek(0)

        self.assertEqual(c, yaml.load(s))
