import os
from unittest import TestCase

from pandas import json
import requests

from elasticsearch_runner.runner import ElasticsearchRunner, process_exists


class TestElasticsearchRunner(TestCase):

    def __init__(self, methodName='runTest'):
        super(TestElasticsearchRunner, self).__init__(methodName)
        self.runner = None
        self.runner2 = None

    def tearDown(self):
        super(TestElasticsearchRunner, self).tearDown()

        if self.runner and self.runner.is_running():
            self.runner.stop()

        if self.runner2 and self.runner2.is_running():
            self.runner2.stop()

    def test_run(self):
        self.runner = ElasticsearchRunner()
        self.runner.install()
        self.runner.run()
        self.runner.wait_for_green()

        self.assertTrue(self.runner.is_running())

        health_resp = requests.get('http://localhost:%d/_cluster/health' % self.runner.es_state.port)
        self.assertEqual(200, health_resp.status_code)
        health_data = json.loads(health_resp.text)
        self.assertEqual(health_data['status'], 'green')

        server_pid = self.runner.es_state.server_pid

        self.runner.stop()

        self.assertFalse(process_exists(server_pid))
        self.assertFalse(self.runner.is_running())
        self.assertIsNone(self.runner.es_state)

    def test_run_multiple(self):
        self.runner = ElasticsearchRunner()
        self.runner.install()
        self.runner.run()
        self.runner.wait_for_green()

        self.assertTrue(self.runner.is_running())

        self.runner2 = ElasticsearchRunner()
        self.runner2.install()
        self.runner2.run()
        self.runner2.wait_for_green()

        self.assertTrue(self.runner2.is_running())

        health_resp = requests.get('http://localhost:%d/_cluster/health' % self.runner.es_state.port)
        self.assertEqual(200, health_resp.status_code)
        health_data = json.loads(health_resp.text)
        self.assertEqual(health_data['status'], 'green')

        health_resp = requests.get('http://localhost:%d/_cluster/health' % self.runner2.es_state.port)
        self.assertEqual(200, health_resp.status_code)
        health_data = json.loads(health_resp.text)
        self.assertEqual(health_data['status'], 'green')

        server_pid = self.runner.es_state.server_pid

        self.runner.stop()

        self.assertFalse(process_exists(server_pid))
        self.assertFalse(self.runner.is_running())
        self.assertIsNone(self.runner.es_state)

        server_pid = self.runner2.es_state.server_pid

        self.runner2.stop()

        self.assertFalse(process_exists(server_pid))
        self.assertFalse(self.runner2.is_running())
        self.assertIsNone(self.runner2.es_state)

    def test_es_wrapper_call(self):
        runner = ElasticsearchRunner(install_path='fakepath')

        self.assertEqual(runner._es_wrapper_call('nt'),
                         [os.path.sep.join(['fakepath', 'elasticsearch-1.7.1', 'bin', 'elasticsearch.bat'])])
        self.assertEqual(runner._es_wrapper_call('posix'),
                         ['/bin/sh', os.path.sep.join(['fakepath', 'elasticsearch-1.7.1', 'bin', 'elasticsearch'])])
