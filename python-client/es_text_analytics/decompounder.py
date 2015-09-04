# coding=utf-8
from numpy import argmin

from es_text_analytics.lemmatizer import OrdbankLemmatizer, ORDBANK_BM_DEFAULT_PATH


"""
Simple decompounder that matches parts of words to fullform entries in Norsk Ordbank.

TODO: Better match. Maybe match lemmas with fixed spacing characters. This should yield less overgeneration.
TODO: Only match allowed POS tag sequences in a compound word. For example adjectives must be prepositioned
  and so on.
TODO: Annotate compound entries in Norsk Ordbank. This would yield better size disambiguation heuristics and
  avoid keeping compound forms that are listed on Norsk Ordbank.
TODO: Return POS tags for internal word components.
"""

# allowed POS tags that can form compounds
COMPOUND_POS_MAP = {
    'simple': ['SUBST', 'ADV', 'ADV', 'VERB']
}

# The decompounder searches for fullform matches from the beginning of the string creates a tree
# of match combinations for each initial match. This is implemented in decompound() and decompund_inner().
#
# The resulting trees are flattened to lists of word forms that the compoun can be split into. This is
# implemented in flatten() and flatten_inner().
#
# Fullform matches can be filtered on length (very short words are probably not "proper" words) and POS tag
# (compounds are for example not productively formed from closed word classes in Norwegian). This is implemented
# in fullform_index_match().
#
# NOTE: Not optimized. Can probably be made a lot more efficient.

def fullform_index_match(string, fullform_index, pos_match_field=None, pos_format='simple'):
    """
    Partial string matching to fullform index. See main comment.

    :param string: Partial word that is being decompounded.
    :type string: str|unicode
    :param fullform_index: Fullform index to Norsk Ordbank entries.
    :type fullform_index: dict[str|unicode, list[dict]]
    :param pos_match_field: Field in fullform index entry to match POS tag to.
    :type pos_match_field: None|str|unicode
    :param pos_format: POS tag type, must correspond to POS tag field in fullform index.
    :type pos_format: str|unicode
    :rtype : bool
    :return: True if matching entry within constraints is found in index.
    """
    if pos_match_field:
        return [match for match in fullform_index.get(string, [])
                if match[pos_match_field] in COMPOUND_POS_MAP[pos_format]]
    else:
        return string in fullform_index


def decompound_inner(word, fullform_index, start=0, min_match=2, pos_match_field=None, pos_format='simple'):
    """
    Decompound tree builder. See main comment.

    :param word: Word that is being decompounded.
    :type word: str|unicode
    :param fullform_index: Fullform index to Norsk Ordbank entries.
    :type fullform_index: dict[str|unicode, list[dict]]
    :param start: Decompound from this position in the word.
    :type start: int|long
    :param min_match: Minimum string length to match.
    :type min_match: int|long
    :param pos_match_field: Field in fullform index entry to match POS tag to.
    :type pos_match_field: None|str|unicode
    :param pos_format: POS tag type, must correspond to POS tag field in fullform index.
    :type pos_format: str|unicode
    :rtype : list[str|unicode|list]
    :return: List based tree structure of partial matches.
    """
    compounds = []
    for i in range(start+1, len(word) + 1):
        if fullform_index_match(word[start:i], fullform_index, pos_format=pos_format, pos_match_field=pos_match_field) \
                and i - start > min_match:
            # recursively collect sequential matches
            compounds.append([word[start:i]] +
                             decompound_inner(word, fullform_index, start=i, min_match=min_match,
                                              pos_match_field=pos_match_field, pos_format=pos_format))

    return compounds


def flatten_inner(compound_tree):
    """
    Flatten single tree structure with fullform mathes for a compound word. See main comment.

    :param compound_tree: List based tree structure of partial matches.
    :type compound_tree: list[str|unicode|list]
    :rtype : list[list[str|unicode]]
    :return: List of partial matches for each branch of the passed tree.
    """
    results = []

    # recursive base case, leaf of tree
    if len(compound_tree) == 1:
        return [[compound_tree[0]]]

    head = compound_tree[0]

    # recursively traverse each branch
    for rest in compound_tree[1:]:
        results += [[head] + tail for tail in flatten_inner(rest)]

    return results


def flatten(compound_forest):
    """
    Flatten a list of compund match trees. See main comment.

    :param compound_forest: List of list based tree structures with partial fullform matches.
    :type compound_forest: list[list[str|unicode|list]]
    :rtype : list[list[str|unicode]]
    :return: List of partial matches for each branch of eaxh tree of the passed list of trees.
    """
    result = []

    for tree in compound_forest:
        result += flatten_inner(tree)

    return result


def decompound(word, fullform_index, min_match=2, pos_match_field=None, pos_format='simple'):
    """
    Main decompounder entry point. See main comment.

    Filters out compound word decompositions that does not exactly match the passed word

    :param word: Word that is being decompounded.
    :type word: str|unicode
    :param fullform_index: Use this fullform index during decompounding. Must conform to the structure
      used by the OrdbankLemmatizer class.
    :type fullform_index: dict[str|unicode, list[dict]]
    :param min_match: Minimum string length to match.
    :type min_match: int|long
    :param pos_match_field: Field in fullform index entry to match POS tag to.
    :type pos_match_field: None|str|unicode
    :param pos_format: POS tag type, must correspond to POS tag field in fullform index.
    :type pos_format: str|unicode
    :rtype : list[list[str|unicode]]
    :return: List of compound word decompositions into substrings.
    """
    candidates = flatten(decompound_inner(word, fullform_index, min_match=min_match,
                                          pos_format=pos_format, pos_match_field=pos_match_field))

    return [c for c in candidates if sum([len(p) for p in c]) == len(word)]


class NOBDecompounder(object):
    """
    Class implementing a simple decompounding strategy for Norwegian Bokmål using the
    Norsk Ordbank lexical database.

    The decompounder uses heuristics and word matching to find and disambiguate
    decompounding candidates.
    """
    def __init__(self, fullform_index=None, min_match=2, pos_format='simple'):
        """
        :param fullform_index: Use this fullform index during decompounding. Must conform to the structure
          used by the OrdbankLemmatizer class.
        :type fullform_index: dict[str|unicode, list[dict]]
        :param min_match: Minimum length of subword that will be matched.
        :type min_match: int|long
        :param pos_format: POS tag type used for disambiguation. Must match fullform index content.
        :type pos_format: str|unicode
        """
        super(NOBDecompounder, self).__init__()

        self.min_match = min_match
        self.pos_format = pos_format
        self.fullform_index = fullform_index

        if not self.fullform_index:
            self.fullform_index = OrdbankLemmatizer(ORDBANK_BM_DEFAULT_PATH, feat_norm=self.pos_format).fullform_index

    def decompound(self, word):
        """
        Decompose the passed compound word if possible.

        :param word: Word to decompound.
        :type word: str|unicode
        :rtype : None|list[string|unicode]
        :return: A list of words that compose the compound word or None if no decomposition is found.
        """
        candidates = decompound(word.lower(), self.fullform_index, min_match=self.min_match,
                                pos_match_field='pos', pos_format=self.pos_format)

        if not candidates:
            return None
        else:
            # if there are several candidates we will pick the one with the simplest decomposition, ie. the
            # one with the fewest elements.
            # if there are still several candidates argmin implicitly chooses the first one since this should
            #  usually have the longest last component with the current matching strategy
            return candidates[argmin([len(c) for c in candidates])]
