# Comperio text analytics [![Build Status](https://travis-ci.org/comperiosearch/comperio-text-analytics.svg?branch=master)](https://travis-ci.org/comperiosearch/comperio-text-analytics)

ElasticSearch based text analytics.

Implementation of:

* Single document significant terms - [Trello board](https://trello.com/c/nrO8QIp9) (private)
* Classification - [Trello board](https://trello.com/c/PU7XqsTi) (private)
* Sentiment analysis - [Trello board](https://trello.com/c/C8H5fBcJ) (private)

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

## Vagrant development server

In order to set up up a Vagrant development server run:

```
vagrant up
fab vagrant provision_server
```


#Installation notes

To use the tagger, decompounder and lemmatizer you will need to download Norsk ordbank.
You can download it by registering at [http://www.edd.uio.no/prosjekt/ordbanken/](http://www.edd.uio.no/prosjekt/ordbanken/)

You will need to build models for the tagger, by running:

    from es_text_analytics.tagger import install_hunpos
    install_hunpos()
    comperio-text-analytics\python-client\bin\build-all-models.bat


