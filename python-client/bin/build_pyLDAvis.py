from gensim.corpora import Dictionary
from gensim.models.ldamodel import LdaModel
import gensim
from gensim import corpora
import pyLDAvis.gensim


def main():
    file = 'f:/projects/elasticsearch-enterprise-system/data/topic_models/nowiki_v2_3pass_lda_250'
    mod = LdaModel.load(file)
    dict = 'f:/projects/elasticsearch-enterprise-system/data/topic_models/voc_vocabulary_0.vocab'
    vocab = Dictionary.load(dict)
    corpfile = 'f:/projects/comperio-text-analytics/models/topicmodel/mojo_lda_100.corp'
    corpus = gensim.corpora.MmCorpus(corpfile)

    print mod.show_topic(0)
    print mod.id2word
    mod.id2word = vocab

    print mod.show_topic(0)

    pydavis = pyLDAvis.gensim.prepare(mod, corpus, vocab)
    pyLDAvis.save_html(pydavis, 'pydavis_250_v2_3passes.html')
    pyLDAvis.show(pydavis)



if __name__ == '__main__':
    main()
