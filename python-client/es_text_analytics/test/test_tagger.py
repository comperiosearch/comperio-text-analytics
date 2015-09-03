# coding=utf-8
import os
from unittest import TestCase

from es_text_analytics.tagger import obt_to_universal_tag, parse_hunpos_train_output, NOBTagger
from es_text_analytics.tagger import NNO_TAGGER_DEFAULT_MODEL_FN, NNOTagger, NOB_TAGGER_DEFAULT_MODEL_FN

HUNPUS_OUTPUT_SAMPLE = """
reading training corpus
compiling probabilities
constructing suffix guesser
saving the model
Traning corpus:
614375 tokens
37620 sentences
21 different tag

Guesser trained with
71042 lowercase
40359 uppercase tokens
theta = 0.0728040512355
"""

class TestTaggerHelpers(TestCase):
  def test_obt_to_universal_tag(self):
    self.assertEqual('VERB', obt_to_universal_tag('skildre', 'verb', 'inf'))
    self.assertEqual('PRON', obt_to_universal_tag('det', 'pron', u'pers|3|nøyt|eint'))
    self.assertEqual('PUNCT', obt_to_universal_tag(',', '<komma>', '_'))

  def test_parse_hunpos_train_output(self):
      self.assertEqual({'tokens': 614375,
                        'sentences': 37620,
                        'tag_card': 21,
                        'n_lower': 71042,
                        'n_upper': 40359,
                        'theta': 0.0728040512355,
                        'errors': []},
                       parse_hunpos_train_output(HUNPUS_OUTPUT_SAMPLE))


class TestNOBTagger(TestCase):
    def test_tag(self):
        if os.path.exists(NOB_TAGGER_DEFAULT_MODEL_FN):
            tagger = NOBTagger()
            self.assertEqual([(u'Dette', 'PRON_PERS'),
                              (u'er', 'VERB'),
                              (u'vårt', 'DET'),
                              (u'hus', 'SUBST'),
                              (u'.', 'PUNKT')],
                             tagger.tag(u'Dette er vårt hus.'))
        else:
            self.skipTest('NOBTagger default model not found in %s' % NOB_TAGGER_DEFAULT_MODEL_FN)


class TestNNOTagger(TestCase):
    def test_tag(self):
        if os.path.exists(NNO_TAGGER_DEFAULT_MODEL_FN):
            tagger = NNOTagger()
            self.assertEqual([(u'Røyndommen', 'SUBST'),
                              (u'rammar', 'VERB'),
                              (u'alle', 'DET'),
                              (u'.', 'PUNKT')],
                             tagger.tag(u'Røyndommen rammar alle.'))
        else:
            self.skipTest('NNOTagger default model not found in %s' % NNO_TAGGER_DEFAULT_MODEL_FN)
