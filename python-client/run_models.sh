#!/bin/bash
wikifile=/data/no/nowiki-latest-pages-articles.xml.bz2
datadir=/data/no/
vocab=/data/no/nowiki_lsi_10.vocab
for n_topics in  100 200 400 1000 2000; do
	python bin/build-wiki-topicmodel.py --model-id nowiki --model-type lsi  -d  $wikifile --data-dir $datadir --vocab $vocab --n-topics $n_topics
done
exit 
for n_topics in  50 100 250 500 1000; do
	python bin/build-wiki-topicmodel.py --model-id nowiki --model-type lda  -d  $wikifile  --data-dir $datadir --vocab $vocab --n-topics $n_topics
done

 
for window in  50 100 250; do
	for size in 500 1000, do
		python bin/build-wiki-topicmodel.py --model-id nowiki --model-type word2vec --w2v-window $window --w2v-size $size -d  $wikifile  --data-dir $datadir --vocab $vocab
	done
done



