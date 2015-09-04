# coding=utf-8
import codecs
import os

from es_text_analytics.data.dataset import project_path
from es_text_analytics.tagger import FEATURES_MAP


# Norwegian lemmatizer based on Norsk Ordbank, http://www.edd.uio.no/prosjekt/ordbanken/data/index.html or
# http://www.nb.no/sprakbanken/show?serial=sbr-5&lang=nb
#
# Norsk Ordbank is not freely available but must be obtained from one of the urls above.

ORDBANK_BM_DEFAULT_PATH = os.path.join(project_path(), 'data', 'ordbank_bm')
FULLFORM_BM_FN = 'fullform_bm.txt'

FULLFORM_FIELDS = ['word_id', 'lemma', 'fullform', 'morph_descr', 'paradigm_code', 'paradigm_entry']


def parse_fullform_file(f, feat_norm='simple'):
    """
    Parses the fullform data file in Norsk Ordbank and returns dicts indexed on the fullform and lemma respectively.

    All fullforms are lowercased.
    Morphological information is normalized to POS tags.

    :param f: file instance for reading the fullform Norsk Ordbank data file.
    :param feat_norm: Type of POS tag to normalize morphological information. Must correspond to POS tagger tagset
      if doing contextual lemmatization.
    :type feat_norm: str|unicode
    :rtype : (dict, dict)
    :return: The fullform and lemma indexes to the file entries.
    """
    fullform_index = {}
    lemma_index = {}

    for line in f:
        line = line.strip()
        # published Ordbank files are latin-1 encoded
        line = line.decode('latin1')

        if line == '' or line[0] == '*':
            continue

        tokens = line.split('\t')

        entry = dict(zip(FULLFORM_FIELDS, tokens))

        entry['fullform'] = entry['fullform'].lower()

        entry['word_id'] = int(entry['word_id'])
        entry['paradigm_entry'] = int(entry['paradigm_entry'])

        # extract pos and features fro mthe morphological field and normalize pos
        morph_parts = entry['morph_descr'].split()
        entry['ndt_pos'] = morph_parts[0]
        entry['ndt_feats'] = '|'.join(morph_parts[1:])
        entry['pos'] = FEATURES_MAP[feat_norm](entry['fullform'], entry['ndt_pos'], entry['ndt_feats'])

        fullform_index[entry['fullform']] = fullform_index.get(entry['fullform'], []) + [entry]
        lemma_index[entry['lemma']] = lemma_index.get(entry['lemma'], []) + [entry]

    return fullform_index, lemma_index


class OrdbankLemmatizer(object):
    """
    Class implementing a simple lemmatizer for Bokmål based on Norsk Ordbank

    Uses "simple" POS tags for contextual disambiguation by default.
    """
    def __init__(self, ordbank_path=None, contextual=False, feat_norm='simple'):
        """
        :param ordbank_path: Path to Norsk Ordbank Bokmål datafiles. Uses the default location of absent.
        :param feat_norm: POS tag type to use for contextual disambiguation. Only "simple" currently supported.
        :type feat_norm: str|unicode
        """
        super(OrdbankLemmatizer, self).__init__()

        if not ordbank_path:
            ordbank_path = ORDBANK_BM_DEFAULT_PATH

        with codecs.open(os.path.join(ordbank_path, FULLFORM_BM_FN)) as f:
            self.fullform_index, self.lemma_index = parse_fullform_file(f, feat_norm=feat_norm)

    def lemmatize(self, word, pos=None):
        """
        Lemmatize the word using the POS tag context if passed.

        :param word: Word to lemmatize.
        :type word: str|unicode
        :param pos: Optional POS tag for disambiguation.
        :type pos: str|unicode
        :rtype : str|unicode
        :return: Lemma for passed word.
        """
        # all matching is done on lowercase
        word = word.lower()

        if pos:
            # lookup candidates and eliminate those with mismatching POS tag
            candidates = [cand for cand in self.fullform_index.get(word, []) if cand['pos'] == pos]
        else:
            candidates = self.fullform_index.get(word)

        if candidates:
            # if there are several candidates we choose the last one
            # if the candidates are POS tag disambiguated our experience shows that further disambigous
            # entries has the "more reasonable" lemmas listed last
            return candidates[-1]['lemma']
        else:
            # default strategy for failing matches is to do nothing
            return word
