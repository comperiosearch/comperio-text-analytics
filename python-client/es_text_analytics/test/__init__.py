from elasticsearch_runner.runner import ElasticsearchRunner

es_runner = ElasticsearchRunner()


def setup():
    es_runner.install()
    es_runner.run()
    es_runner.wait_for_green()


def teardown():
    if es_runner and es_runner.is_running():
        es_runner.stop()
