from collections import namedtuple
import json
import logging
import os
import re
from shutil import copyfile, rmtree
from tempfile import mkdtemp
from time import sleep, clock
from urlparse import urlparse
from zipfile import ZipFile
from subprocess import Popen
import errno

from psutil import Process, NoSuchProcess
import requests

from elasticsearch_runner.configuration import serialize_config, generate_config, generate_cluster_name, package_path

"""
Class for starting, stopping and managing an Elasticsearch instance from within a Python process.

Intended for testing and other lightweight purposes with transient data.

TODO Faster Elasticsearch startup.
"""


ES_DEFAULT_VERSION = '1.7.2'

ES_URLS = {'1.7.2': 'https://download.elastic.co/elasticsearch/elasticsearch/elasticsearch-1.7.2.zip',
           '2.0.0-rc1': 'https://download.elasticsearch.org/elasticsearch/release/org/elasticsearch/distribution/zip/elasticsearch/2.0.0-rc1/elasticsearch-2.0.0-rc1.zip'}
ES_DEFAULT_URL_LOCATION = 'https://download.elastic.co/elasticsearch/elasticsearch/elasticsearch'

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
    Download the file pointed to by the url to the path specified .
    If the file is already present at the path it will not be downloaded and the path to this file
    is returned.

    :param url: url string pointing to the file
    :type url : str|unicode
    :param dest_path: path to location where the file will be stored locally
    :type dest_path : str|unicode
    :rtype : str|unicode
    :return: path to the downloaded file
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
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()

    return full_fn


def check_java():
    """
    Simple check for Java availability on the local system.

    :rtype : bool
    :return: True if Java available on the command line
    """
    return os.system('java -version') == 0


def process_exists(pid):
    """
    Check if there is a process with this PID.

    :param pid: Process ID
    :type pid: int
    :rtype : bool
    :return: True if the process exists, False otherwise
    """
    if os.name == 'nt':
        # TODO something more solid on windows?
        try:
            return Process(pid).status() == 'running'
        except NoSuchProcess:
            return False
    else:
        try:
            os.kill(pid, 0)
        except OSError:
            return False

        return True


def parse_es_log_header(log_file, limit=200):
    """
    Look at Elasticsearch log for startup messages containing system information. The log is read until the starting
    message is detected or the number of lines read exceed the limit.
    The log file must be open fir reading and at the desired position, ie. the end to read incoming log lines.

    :param log_file: open for reading file instance for the log file at the correct position
    :type log_file: FileIO
    :param limit: max lines to read before returning
    :type limit: int
    :rtype : (int|None, int|None)
    :return: A tuple with the Elasticsearch instance PID and REST endpoint port number, ie. (pid, port)
    """
    line = log_file.readline()
    server_pid = None
    es_port = None
    count = 0

    while count < limit:
        count += 1
        line = line.strip()

        if line == '':
            sleep(.1)

        m = re.search('pid\[(\d+)\]', line)
        if m:
            server_pid = int(m.group(1))

        m = re.search('\[http.*publish_address.*:(\d+)[\]\}|\}]', line)
        if m:
            es_port = int(m.group(1))

        if re.search('started', line):
            return server_pid, es_port

        line = log_file.readline()

    logging.warn('Read more than %d lines while parsing Elasticsearch log header. Giving up ...' % limit)

    return server_pid, es_port


# tuple holding information about the current Elasticsearch process
ElasticsearchState = namedtuple('ElasticsearchState', 'server_pid wrapper_pid port config_fn')


class ElasticsearchRunner:
    """
    Runs a basic single node Elasticsearch instance for testing or other lightweight purposes.
    """

    def __init__(self, install_path=None, transient=False, version=None):
        """
        :param install_path: The path where the Elasticsearch software package and data storage will be kept.
        If no install path set, installs into APPDATA (windows)or  HOME/.elasticsearch_runner (other)
        Install_path can be provided as the environment variable 'elasticsearch-runner-install-path'
        If environment variable provided it will override install_path parameter
        :type install_path: str|unicode
        :param transient: Not implemented.
        :type transient: bool
        """
        if os.getenv('elasticsearch-runner-install-path'):
            install_path = os.getenv('elasticsearch-runner-install-path')

        if install_path:
            self.install_path = install_path
        else:
            if os.name == 'nt':
                self.install_path = os.path.join(os.getenv("APPDATA"), 'elasticsearch_runner', 'embedded-es')
            else:
                self.install_path = os.path.join(os.getenv("HOME"), '.elasticsearch_runner', 'embedded-es')
        if version:
            self.version = version
        else:
            self.version = ES_DEFAULT_VERSION
        self.version_folder = "elasticsearch-%s" % self.version
        self.transient = transient
        self.es_state = None
        self.es_config = None

        if not check_java():
            logging.error('Java not installed. Elasticsearch won\'t be able to run ...')

    def install(self):
        """
        Download and install the Elasticsearch software in the install path. If already downloaded or installed
        those steps are skipped.

        :rtype : ElasticsearchRunner
        :return: The instance called on.
        """
        if self.version in ES_URLS:
            es_archive_fn = download_file(ES_URLS[self.version], self.install_path)
        else:
            download_url = "%s-%s.zip" %  (ES_DEFAULT_URL_LOCATION, self.version)
            es_archive_fn = download_file(download_url, self.install_path)

        if not os.path.exists(os.path.join(self.install_path, self.version_folder)):
            with ZipFile(es_archive_fn, "r") as z:
                z.extractall(self.install_path)

        # insert basic config file
        copyfile(os.path.join(package_path(), 'resources', 'embedded_elasticsearch.yml'),
                 os.path.join(self.install_path, self.version_folder, 'config', 'elasticsearch.yml'))

        return self

    def run(self):
        """
        Start the elasticsearch server. Running REST port and PID is stored in the es_state field.

        :rtype : ElasticsearchRunner
        :return: The instance called on.
        """
        if self.is_running():
            logging.warn('Elasticsearch already running ...')
        else:
            # generate and insert Elasticsearch configuration file with transient data and log paths
            cluster_name = generate_cluster_name()
            data_path = mkdtemp(prefix='%s-data-' % cluster_name, dir=self.install_path)

            self.es_config = generate_config(cluster_name=cluster_name, data_path=data_path)
            config_fn = os.path.join(self.install_path, self.version_folder, 'config',
                                     'elasticsearch-%s.yml' % cluster_name)

            with open(config_fn, 'w') as f:
                serialize_config(f, self.es_config)

            # create the log file if it doesn't exist yet. We need to open it and seek to to the end before
            # sniffing out the configuration info from the log.
            es_log_dir = os.path.join(self.install_path, self.version_folder, 'logs')
            es_log_fn = os.path.join(es_log_dir, '%s.log' % cluster_name)

            try:
                os.makedirs(es_log_dir)
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    raise

            open(es_log_fn, 'a').close()

            es_log_f = open(es_log_fn, 'r')
            es_log_f.seek(0, 2)

            wrapper_proc = Popen(self._es_wrapper_call(os.name) + ['-Des.config=%s' % config_fn])

            # watch the log
            server_pid, es_port = parse_es_log_header(es_log_f)

            if not server_pid:
                logging.error('Server PID not detected ...')

            if not es_port:
                logging.error('Server http port not detected ...')

            self.es_state = ElasticsearchState(wrapper_pid=wrapper_proc.pid,
                                               server_pid=server_pid,
                                               port=es_port,
                                               config_fn=config_fn)
        return self

    def _es_wrapper_call(self, os_name):
        """
        :param os_name: OS identifier as returned by os.name
        :type os_name: str|unicode
        :rtype : list[str|unicode]
        :return:
        """
        if os_name == 'nt':
            es_bin = [os.path.join(self.install_path, self.version_folder, 'bin', 'elasticsearch.bat')]
        else:
            es_bin = ['/bin/sh', os.path.join(self.install_path, self.version_folder, 'bin', 'elasticsearch')]

        return es_bin

    def stop(self):
        """
        Stop the Elasticsearch server.

        :rtype : ElasticsearchRunner
        :return: The instance called on.
        """
        if self.is_running():
            server_proc = Process(self.es_state.server_pid)
            server_proc.terminate()
            server_proc.wait()

            if process_exists(self.es_state.server_pid):
                logging.warn('Failed to stop Elasticsearch server process PID %d ...' % self.es_state.server_pid)

            # delete transient directories
            if 'path' in self.es_config:
                if 'log' in self.es_config['path']:
                    log_path = self.es_config['path']['log']
                    logging.info('Removing transient log path %s ...' % log_path)
                    rmtree(log_path)

                if 'data' in self.es_config['path']:
                    data_path = self.es_config['path']['data']
                    logging.info('Removing transient data path %s ...' % data_path)
                    rmtree(data_path)

            # delete temporary config file
            if os.path.exists(self.es_state.config_fn):
                logging.info('Removing transient configuration file %s ...' % self.es_state.config_fn)
                os.remove(self.es_state.config_fn)

            self.es_state = None
            self.es_config = None
        else:
            logging.warn('Elasticsearch is not running ...')

        return self

    def is_running(self):
        """
        Checks if the instance has a running server process and that thhe process exists.

        :rtype : bool
        :return: True if the servier is running, False if not.
        """
        state = self.es_state

        return state and process_exists(state.server_pid)

    def wait_for_green(self, timeout=1.):
        """
        Check if cluster status is green and wait for it to become green if it's not.
        Run after starting the runner to ensure that the Elasticsearch instance is ready.

        :param timeout: The time to wait for green cluster response in seconds.
        :type timeout: int|long|float
        :rtype : ElasticsearchRunner
        :return:
        """
        if not self.es_state:
            logging.warn('Elasticsearch runner is not started ...')
            return self

        if self.es_state.port is None:
            logging.warn('Elasticsearch runner not properly started ...')
            return self
        
        end_time = clock() + timeout
        health_resp = requests.get('http://localhost:%d/_cluster/health' % self.es_state.port)
        health_data = json.loads(health_resp.text)

        while health_data['status'] != 'green':
            if clock() > end_time:
                logging.error('Elasticsearch cluster failed to turn green in %f seconds, current status is %s ...' %
                              (timeout, health_data['status']))

                return self

            health_resp = requests.get('http://localhost:%d/_cluster/health' % self.es_state.port)
            health_data = json.loads(health_resp.text)

        return self
