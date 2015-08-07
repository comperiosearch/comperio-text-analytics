from elasticsearch_runner.elasticsearch_runner import ElasticsearchRunner

es_runner = ElasticsearchRunner()


def setup():
    es_runner.install()
    es_runner.run()


def teardown():
    if es_runner and es_runner.is_running():
        es_runner.stop()
