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


def force_list(item):
    """
    Wrapped the passed argument in a list if it is not a list.

    :param item: Anything.
    :return: List wrapping any non list item passed.
    """
    if not isinstance(item, list):
        return [item]
    else:
        return item


def extract(tagged_tokens, keep_index=False):
    """
    Extracted NP chunks from a tagged sequence of tokens.

    This method uses a simple CFG over POS tags

    :param tagged_tokens: A sequence of token/tag pairs from the NNO or NOB tagger.
    :type tagged_tokens: list[(str|unicode, str|unicode)]
    :param keep_index: Return token index positions for chunks.
    :type keep_index: bool
    :rtype : list[str|unicode|list[str|unicode]|(str|unicode|list[str|unicode], int)]
    :return: A list of NP chunks as strings with the complete phrase. Chunks can be strings for single token chunks,
      list of strings for ultiple tokens or a chunk/index tuple if keep_index is set to true.
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
                match = force_list(t1[0]) + force_list(t2[0])
                pos = value
                # noinspection PyTypeChecker
                tagged_tokens.insert(x, (match, pos))
                break

    matches = []
    index = 0

    for t in tagged_tokens:
        if t[1] in ['SUBST', 'SUBST_PROP', 'SUBSTP']:
            if keep_index:
                value = (t[0], index)
            else:
                value = t[0]

            matches.append(value)

        if isinstance(t, list):
            index += len(t)
        else:
            index += 1

    return matches


class NONPExtractor(BaseNPExtractor):
    """
    Simple NP extractor similar to FastNPEXtractor in TextBlob.
    """
    def __init__(self, tagger=None, keep_index=False):
        """
        :param tagger: If initialized a tagger instance extract arguments will be processed with this tagger.
          Otherwise the extract method expects tagged input.
        :type tagger: None|textblob.base.BaseTagger
        :param keep_index: Return token index positions for chunks.
        :type keep_index: bool
        """
        self.tagger = tagger
        self.keep_index = keep_index

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

        return extract(tokens, keep_index=self.keep_index)
