from textblob.base import BaseNPExtractor

"""
Minimal NP chunker for Norwegian adapted from the TextBlob FastNPExtractor.

Compatible with the TextBlob API.
"""

CFG = {
    ('SUBST_PROP', 'SUBST_PROP'): 'SUBST_PROP',
    ('SUBST', 'SUBST'): 'SUBSTP',
    ('SUBSTP', 'SUBST'): 'SUBSTP',
    ('ADJ', 'ADJ'): 'ADJ',
    ('ADJ', 'SUBST'): 'SUBSTP',
    }

def extract(tagged_tokens):
    """
    Extracted NP chunks from a tagged sequence of tokens.

    This method uses a simple CFG over POS tags

    :param tagged_tokens: A sequence of token/tag pairs from the NNO or NOB tagger.
    :type tagged_tokens: list[(str|unicode, str|unicode)]
    :rtype : list[str|unicode]
    :return: A list of NP chunks as strings with the complete phrase.
    """
    merge = True
    while merge:
        merge = False
        for x in range(0, len(tagged_tokens) - 1):
            t1 = tagged_tokens[x]
            t2 = tagged_tokens[x + 1]
            key = t1[1], t2[1]
            value = CFG.get(key, '')

            if value:
                merge = True
                tagged_tokens.pop(x)
                tagged_tokens.pop(x)
                match = '%s %s' % (t1[0], t2[0])
                pos = value
                tagged_tokens.insert(x, (match, pos))
                break

    matches = [t[0] for t in tagged_tokens if t[1] in ['SUBST', 'SUBST_PROP', 'SUBSTP']]

    return matches


class NONPExtractor(BaseNPExtractor):
    """
    Simple NP extractor similar to FastNPEXtractor in TextBlob.
    """
    def __init__(self, tagger=None):
        """
        :param tagger: If initialized a tagger instance extract arguments will be processed with this tagger.
          Otherwise the extract method expects tagged input.
        :type tagger: None|textblob.base.BaseTagger
        """
        self.tagger = tagger

    def extract(self, tokens):
        """
        Extract NP chunks from passed tokens.

        :param tokens: Tokens as untagged string or pretagged list of token/tag pairs according to tagger configuration.
        :type tokens: str|list[(str|unicode, str|unicode)]
        :rtype : list[str|unicode]
        :return:
        """
        if self.tagger:
            tokens = self.tagger.tag(tokens)

        return extract(tokens)
