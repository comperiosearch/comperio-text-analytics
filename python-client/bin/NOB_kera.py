__author__ = 'cvig'
from es_text_analytics.tagger import NOBTagger, install_hunpos
from es_text_analytics.np_extractor import NONPExtractor
from es_text_analytics.kera import extract_keywords
from nltk.tokenize import sent_tokenize
import re

def fast_tokenize(str):
    return [token.lower() for token in re.findall('[^\W\d_]+', re.sub('[\n-]', ' ', str), re.MULTILINE|re.UNICODE)]

class NOB_kera():
    def __init__(self):
        self.tagger = NOBTagger()
        self.chunker = NONPExtractor(tagger=self.tagger, keep_index=True)

    def extract_keywords(self, from_text):
        return extract_keywords(from_text, fast_tokenize, sent_tokenize, self.tagger, self.chunker)
