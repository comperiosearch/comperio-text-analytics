from collections import Counter
from operator import itemgetter

from nltk import BigramAssocMeasures, BigramCollocationFinder


# TODO A wrapper class could encapsulate default configurations.


def extract_keywords(string, tokenizer, sent_tokenizer, tagger, extractor, proper_noun_tag='SUBST_PROP'):
    """
    Implements KERA keyword extraction algorithm.

    See: https://www.ida.org/~/media/Corporate/Files/Publications/IDA_Documents/ITSD/ida-document-ns-d-4931.pdf

    Basic implementation of the procedure described in the paper.
    Probably needs some refinements in order to be more broadly effective.

    :param string: Document to analyze.
    :type string: str|unicode
    :param tokenizer: Function that returns a token segmentation as an iterable of strings given a string..
    :type tokenizer: (str|unicode) -> list[str|unicode]
    :param sent_tokenizer: Function that returns a sentence segmentation as an iterable of strings given a string.
    :type sent_tokenizer: (str|unicode) -> list[str|unicode]
    :param tagger: TextBlob compatible POS tagger. Must accept untokenized sentences.
    :type tagger: textblob.base.BaseTagger
    :param extractor: TextBlob compatible noun phrase extractor. Must accept untokenized sentences and use the same
      POS tagger which is passed as the tagger parameter.
    :type extractor: textblob.base.BaseNPExtractor
    :param proper_noun_tag: POS tag indicating proper nouns.
    :type proper_noun_tag: str|unicode
    :return: List of keyword/score tuples. Keyword may be a string or tuple of strings.
    :rtype : list[(str|unicode|(str|unicode)), float]
    """
    # find bigram collocations
    bigram_measures = BigramAssocMeasures()
    finder = BigramCollocationFinder.from_words(tokenizer(string))
    collocations = finder.score_ngrams(bigram_measures.likelihood_ratio)[0:50]

    # find noun phrases
    phrases = [extractor.extract(s) for s in sent_tokenizer(string)]
    phrases = [item for sublist in phrases for item in sublist]

    # find proper noun tokens, collect total/frequency for weighting/normalization
    sents = [tagger.tag(s) for s in sent_tokenizer(string)]
    sents = [item for sublist in sents for item in sublist]

    proper_nouns = []

    np_doc_len = 0

    for i, (token, tag) in enumerate(sents):
        np_doc_len += 1

        if tag == proper_noun_tag:
            proper_nouns.append((token, i))

    # find noun phrase/collocation overlap
    phrase_strings = [' '.join(x[0]).lower() for x in phrases if isinstance(x[0], list)]
    collocations = [c for c in collocations if ' '.join(c[0]) in phrase_strings]

    ranks = []

    # calculate combined index score and normalized collocation score for collocations
    coll_score_total = sum([x[1] for x in collocations])
    coll_doc_len = len(tokenizer(string))

    for coll, coll_score in collocations:
        idx = phrases[phrase_strings.index(' '.join(coll))][1]

        alpha = coll_score / coll_score_total
        beta = 1 - (float(idx) / coll_doc_len)

        score = 2 * alpha * beta / (alpha + beta)

        ranks.append((coll, score))

    # calculate combined index score and normalized term frequency score for proper nouns
    np_strings = [x[0] for x in proper_nouns]
    np_counts = Counter(np_strings)
    np_total = len(proper_nouns)

    # only use normalize over the same number of proper nouns as collocations in order to keep
    # the scores roughly comparable.
    # TODO There are rarely more proper names than collocations. Handle this too.
    for np, count in sorted(np_counts.items(), key=itemgetter(1), reverse=True)[0:len(collocations)]:
        idx = proper_nouns[np_strings.index(np)][1]

        alpha = float(count) / np_total
        beta = 1 - (float(idx) / np_doc_len)

        score = 2 * alpha * beta / (alpha + beta)

        ranks.append((np, score))

    # return list of keywords and scores sorted by score
    return sorted(ranks, key=itemgetter(1), reverse=True)
