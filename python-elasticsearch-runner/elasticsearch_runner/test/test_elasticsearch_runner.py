import os
import io
from unittest import TestCase

from pandas import json
import requests

from elasticsearch_runner.runner import ElasticsearchRunner, process_exists, parse_es_log_header


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
        #NB! beware that if the environment variable 'elasticsearch-runner-install-path' is set this test will fail
        runner = ElasticsearchRunner(install_path='fakepath')
        self.assertEqual(runner._es_wrapper_call('nt'),
                         [os.path.sep.join(['fakepath', runner.version_folder, 'bin', 'elasticsearch.bat'])])
        self.assertEqual(runner._es_wrapper_call('posix'),
                         ['/bin/sh', os.path.sep.join(['fakepath', runner.version_folder, 'bin', 'elasticsearch'])])

    def test_run_version2(self):
        es_version = '2.0.0-rc1'
        self.runner = ElasticsearchRunner(version=es_version)
        self.runner.install()
        self.runner.run()
        self.runner.wait_for_green()

        self.assertTrue(self.runner.is_running())

        health_resp = requests.get('http://localhost:%d/_cluster/health' % self.runner.es_state.port)
        self.assertEqual(200, health_resp.status_code)
        health_data = json.loads(health_resp.text)
        self.assertEqual(health_data['status'], 'green')
        status = requests.get('http://localhost:%d' % self.runner.es_state.port)
        status_data = json.loads(status.text)
        self.assertEqual(status_data['version']['number'], es_version)
        server_pid = self.runner.es_state.server_pid

        self.runner.stop()

        self.assertFalse(process_exists(server_pid))
        self.assertFalse(self.runner.is_running())
        self.assertIsNone(self.runner.es_state)

    def test_run_version15(self):
        es_version = '1.5.2'
        self.runner = ElasticsearchRunner(version=es_version)
        self.runner.install()
        self.runner.run()
        self.runner.wait_for_green()

        self.assertTrue(self.runner.is_running())

        health_resp = requests.get('http://localhost:%d/_cluster/health' % self.runner.es_state.port)
        self.assertEqual(200, health_resp.status_code)
        health_data = json.loads(health_resp.text)
        self.assertEqual(health_data['status'], 'green')
        status = requests.get('http://localhost:%d' % self.runner.es_state.port)
        status_data = json.loads(status.text)
        self.assertEqual(status_data['version']['number'], es_version)
        server_pid = self.runner.es_state.server_pid

        self.runner.stop()

        self.assertFalse(process_exists(server_pid))
        self.assertFalse(self.runner.is_running())
        self.assertIsNone(self.runner.es_state)



    def test_parse_log_header_esv2_format(self):
        testStream = io.StringIO()
        testStream.write(u'[2015-10-08 11:21:02,427][INFO ][node                     ] [Hero] version[2.0.0-rc1], pid[208], build[4757962/2015-10-01T10:06:08Z]\n')
        testStream.write(u'[2015-10-08 11:21:09,025][INFO ][http                     ] [Hero] publish_address {127.0.0.1:9200}, bound_addresses {127.0.0.1:9200}, {[::1]:9200}\n')
        testStream.write(u'[2015-10-08 11:04:15,784][INFO ][node                     ] [Hero] started\n')
        testStream.seek(0)
        server_pid, es_port = parse_es_log_header(testStream)
        self.assertEqual(server_pid, 208)
        self.assertEqual(es_port, 9200)

    def test_parse_log_header_esv1_format(self):
        testStream = io.StringIO()
        testStream.write(u'[2015-10-08 11:04:09,252][INFO ][node                     ] [Astronomer] version[1.7.2], pid[8248], build[e43676b/2015-09-14T09:49:53Z]\n')
        testStream.write(u'[2015-10-08 11:04:15,784][INFO ][http                     ] [Astronomer] bound_address {inet[/0:0:0:0:0:0:0:0:9200]}, publish_address {inet[/10.0.80.134:9200]}\n')
        testStream.write(u'[2015-10-08 11:04:15,784][INFO ][node                     ] [Astronomer] started\n')
        testStream.seek(0)
        server_pid, es_port = parse_es_log_header(testStream)
        self.assertEqual(server_pid, 8248)
        self.assertEqual(es_port, 9200)
