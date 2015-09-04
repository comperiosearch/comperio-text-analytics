# Comperio text analytics

ElasticSearch based text analytics.

Implementation of:

* Single document significant terms - [Trello board](https://trello.com/c/nrO8QIp9)
* Classification - [Trello board](https://trello.com/c/PU7XqsTi)
* Sentiment analysis - [Trello board](https://trello.com/c/C8H5fBcJ)

## Norwegian linguistics support for text analytics

There is currently partial experimental support for some linguistic analysis of Norwegian Bokmål. This
support depends on the following resources:

* Norwegian Dependency Treebank (NDT) (freely available, permissive licensing).
* Norsk Ordbank (available on request, GPL or commercial licensing).

Norsk Ordbank must be obtained separately and unzipped in the data directory for it to be used automatically
by linguistic processing components.

### Tokenizer

Currently a simple application of the UAX29 standard for Unicode tokenization. Will be expanded to handle hyphens
in accordance with Norwegian norms.

```python
tokenizer = NOTokenizer()
tokenizer.tokenize(u'Vi er konsulenter, med fokus på søk!')

[u'Vi',
 u'er',
 u'konsulenter',
 u',',
 u'med',
 u'fokus',
 u'på',
 u'søk',
 u'!']
```

### Part of speech annotation

Adds part of speech descriptions. THe default annotation is a very simplified version of the one used by Norsk Ordbank
and NDT.

```python
tagger = NOBTagger()
tagger.tag(u'Vi spiste lunsj ute i det fine været.')

[(u'Vi', 'PRON_PERS'),
 (u'spiste', 'VERB'),
 (u'lunsj', 'SUBST'),
 (u'ute', 'PREP'),
 (u'i', 'PREP'),
 (u'det', 'DET'),
 (u'fine', 'ADJ'),
 (u'været', 'SUBST'),
 (u'.', 'PUNKT')]
```

Evaluation of the tagger precision is forthcoming, but users should expect a reasonable error rate given the
limited trraining data available.

### Lemmatization

Based on Norsk Ordbank. It is possible to pass the part of speech tag in order to disambiguate words which can
have more than one lemma form.

```python
sent = tagger.tag(u'Vi er godt forberedt.')
[(word, lem.lemmatize(word, tag)) for word, tag in sent]

[(u'Vi', u'vi'),
 (u'er', u'være'),
 (u'godt', u'god'),
 (u'forberedt', u'forberedt'),
 (u'.', u'.')]
```

### Decompounder

Simple heuristics based decompounder based on the word forms in Norsk Ordbank. This can overgenerate so it should
primarily be used on wellformed text.

```python
dec = NOBDecompounder()
dec.decompound(u'lampekostbatteri'), dec.decompound(u'søkekonsulenter')

[u'lampe', u'kost', u'batteri'], [u'søke', u'konsulenter']
```

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
