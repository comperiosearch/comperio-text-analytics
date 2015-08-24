# Comperio text analytics

ElasticSearch based text analytics.

Implementation of:

* Single document significant terms - [Trello board](https://trello.com/c/nrO8QIp9)
* Classification - [Trello board](https://trello.com/c/PU7XqsTi)
* Sentiment analysis - [Trello board](https://trello.com/c/C8H5fBcJ)

## Elasticsearch test runner

The python-elasticsearch-runner contains a standalone Python runner for Elasticsearch. This is intended
for transient and lightweight usage such as small integration tests.

The runner takes about 10 sec. to start so it should be a part of at least module level setup/teardown in
order to minimize test run time.

The following code sets up the runner instance at module level with nosetests if placed in __init__.py:

```python
from elasticsearch_runner.runner import ElasticsearchRunner

es_runner = ElasticsearchRunner()

def setup():
    es_runner.install()
    es_runner.run()
    es_runner.wait_for_green()

def teardown():
    if es_runner and es_runner.is_running():
        es_runner.stop()
```

The runner instance can then be queried for the port number when connecting:

```python
es = Elasticsearch(hosts=['localhost:%d' % es_runner.es_state.port])
```

## Vagrant development server

In order to set up up a Vagrant development server run:

```
vagrant up
fab vagrant provision_server
```
