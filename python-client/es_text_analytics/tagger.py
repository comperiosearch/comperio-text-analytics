import logging
import os
import re
from tarfile import TarFile
from zipfile import ZipFile
import sys
from subprocess import Popen, PIPE

from nltk.tag.hunpos import HunposTagger

from textblob.base import BaseTagger

from es_text_analytics.data.dataset import project_path, download_file
from es_text_analytics.tokenizer import NOTokenizer



# TextBlob compatible part-of-speech tagger for Norwegian.

# default HunPos model loation
NO_TAGGER_DEFAULT_MODEL_FN = os.path.join(project_path(), 'models', 'no-tagger-default-model')

HUNPOS_URL_MAP = {
    'linux2': 'https://hunpos.googlecode.com/files/hunpos-1.0-linux.tgz',
    'darwin': 'https://hunpos.googlecode.com/files/hunpos-1.0-macosx.tgz',
    'win32': 'https://hunpos.googlecode.com/files/hunpos-1.0-win.zip'
}

HUNPOS_SUBDIR_MAP = {
    'win32': 'hunpos-1.0-win',
    'darwin': 'hunpos-1.0-macosx',
    'linux': 'hunpos-1.0-linux'
}


def obt_to_universal_tag(form, pos, feats):
    """
    Maps OBT POS tags and features as found in the NDT to universal POS tags as described in
    http://universaldependencies.github.io/docs/u/pos/index.html

    The mapping is not complete or completely precises because of discrepancies between the OBT/NDT
    annotation and this tagset. For example:

    - AUX is not annotated in NDT and would need a wordlist to extract properly.
    - NUM is done mostly heuristically since NDT does nt encode numbers. Ideally numbers and similar
      entities should be normalized before tagging.

    :param form: NDT word form.
    :type form: str|unicode
    :param pos: OBT pos tag.
    :type pos: str|unicode
    :param feats: OBT features encoded as | separated string as in NDT.
    :type feats: str|unicode
    :rtype : str|unicode
    :return: Normalized universal POS tag.
    """
    feats = feats.split('|')

    if re.search('\d', form):
        return 'NUM'

    if pos == 'adj':
        return 'ADJ'
    if pos == 'adv':
        return 'ADV'
    if pos == 'konj':
        return 'CONJ'
    if pos == 'det' and ('<romertall>' in feats or '<romartal>' in feats):
        return 'NUM'
    if pos == 'det':
        return 'DET'
    if pos == 'interj':
        return 'INTJ'
    # we'll include dates among the proper nouns
    if pos == 'subst' and ('prop' in feats or '<tittel>' in feats or 'fork' in feats or '<dato>' in feats):
        return 'PROPN'
    if pos == 'subst' and 'symb' in feats:
        return 'SYM'
    if pos == 'subst':
        return 'NOUN'
    if pos == 'pron':
        return 'PRON'
    if pos in ['clb', '<anf>', '<komma>', '<parentes-beg>', '<parentes-slutt>', '<strek>']:
        return 'PUNCT'
    if pos == 'sbu':
        return 'SCONJ'
    if pos == 'symb':
        return 'SYM'
    if pos in ['inf-merke', 'verb']:
        return 'VERB'
    if pos == 'prep':
        return 'ADP'

    return 'X'


def obt_to_simple(form, pos, feats):
    """
    Mapping from OBT to a simple POS tag set including a small set of basic features into the tag.

    - Heuristically extracts number tag.
    - Normalizes punctuation to single tag.
    - Includes pronoun type.
    - Normalizes proper noun tags and features.
    - includes passive feature on verbs.

    :param form: NDT word form.
    :type form: str|unicode
    :param pos: OBT pos tag.
    :type pos: str|unicode
    :param feats: OBT features encoded as | separated string as in NDT.
    :type feats: str|unicode
    :rtype : str|unicode
    :return: Normalized POS tag.
    """
    feats = feats.split('|')

    if re.search('\d', form):
        return 'NUM'

    if pos == 'det' and ('<romertall>' in feats or '<romartal>' in feats):
        return 'NUM'

    if pos in ['clb', '<anf>', '<komma>', '<parentes-beg>', '<parentes-slutt>', '<strek>']:
        return 'PUNKT'

    if pos == 'pron':
        for feat in ['sp', 'pers', 'poss', 'refl']:
            if feat in feats:
                 return ('%s_%s' % (pos, feat)).upper()

    if pos == 'subst':
        if 'sym' in feats:
            return 'SYMB'

        # include dates
        for feat in ['prop', '<tittel>', 'fork', '<dato>']:
            if feat in feats:
                return 'SUBST_PROP'

    if pos == 'verb' and 'pass' in feats:
        return 'VERB_PASS'

    return pos.upper()


# maps feature normalization identifiers to the functions
FEATURES_MAP = {'universal': obt_to_universal_tag,
                'simple': obt_to_simple,
                # removes all features and includes just the bare POS tag
                'no-feats': lambda form, pos, feats: pos,
                # includes all features execpt blank ones
                'all-feats': lambda form, pos, feats: '%s_%s' % (pos, '_'.join([f for f in feats.split('|') if f != '_']))}


def install_hunpos():
    """
    Downloads and install system appropriate HunPos bunaries in the default location.

    :rtype : None
    """
    models_dir = os.path.join(project_path(), 'models')

    hunpos_archive_fn = download_file(HUNPOS_URL_MAP[sys.platform], models_dir)

    if sys.platform == 'win32':
        with ZipFile(hunpos_archive_fn) as f:
            f.extractall(models_dir)
    else:
        with TarFile(hunpos_archive_fn) as f:
            f.extractall(models_dir)

    os.remove(hunpos_archive_fn)


def hunpos_path():
    """
    Returns the system specifiuc default install directory for HunPos binaries.

    :rtype : str|unicode
    :return:
    """
    return os.path.join(project_path(), 'models', HUNPOS_SUBDIR_MAP[sys.platform])


def hunpos_tag_bin():
    """
    Path to system specific hunpos-tag binary.

    :rtype : str|unicode
    :return:
    """
    if sys.platform == 'win32':
        return os.path.join(hunpos_path(), 'hunpos-tag.exe')
    else:
        return os.path.join(hunpos_path(), 'hunpos-tag')


def hunpos_train_bin():
    """
    Path to system specific hunpos-train binary.

    :rtype : str|unicode
    :return:
    """
    if sys.platform == 'win32':
        return os.path.join(hunpos_path(), 'hunpos-train.exe')
    else:
        return os.path.join(hunpos_path(), 'hunpos-train')


def parse_hunpos_train_output(output):
    """
    Parses hunpos-train output and collects the reported statistics.

    Includes:
    - error messages (errors)
    - # of sentences and # of tokens (sentences, tokens)
    - # of uppercase and lowercase tokens (n_upper, n_lower)
    - # of different POS tags (tag_card)

    :param output: String with newline separated output from hunpos-train
    :rtype : dict
    :return: Dict with statistics reported by hunpos-train.
    """
    stats = {'errors': []}

    for line in output.split('\n'):
        line = line.strip()

        m = re.match('(\d+) tokens', line)
        if m:
            stats['tokens'] = int(m.group(1))

        m = re.match('(\d+) sentences', line)
        if m:
            stats['sentences'] = int(m.group(1))

        m = re.match('(\d+) different tag', line)
        if m:
            stats['tag_card'] = int(m.group(1))

        m = re.match('(\d+) lowercase', line)
        if m:
            stats['n_lower'] = int(m.group(1))

        m = re.match('(\d+) uppercase tokens', line)
        if m:
            stats['n_upper'] = int(m.group(1))

        m = re.match('theta = (\d\.\d+)', line)
        if m:
            stats['theta'] = float(m.group(1))

        # the error format is not documented so this will suffice for now
        m = re.search('error', line, re.IGNORECASE)
        if m:
            stats['errors'] += line

    return stats


def train_hunpos_model(seq, model_fn):
    """
    Trains a HunPos POS tagger on the sentences passed as seq using the external hunpos-train binary.

    Models use UTF-8 encoding.

    :param seq: Iterator with sentences. Sentences are iterators with word form/pos tag tuples.
    :param model_fn: File where the resulting model will be stored.
    :type model_fn: str|unicode
    :rtype : dict
    :return: Reported statistics printed by hunpos-train
    """

    # We'll be doind it simple here.
    # Just write all the data to stdin and catch potential errors on stderr afterwards.
    train_proc = Popen([hunpos_train_bin(), model_fn], stdin=PIPE, stderr=PIPE)

    for sent in seq:
        for form, tag in sent:
            line = b'%s\t%s\n' % (form, tag)
            line = line.encode('utf-8')
            train_proc.stdin.write(line)

        train_proc.stdin.write('\n')

    train_proc.stdin.close()

    # parse the output
    # hunpos-trai reports results and errors on stderr
    stats = parse_hunpos_train_output(train_proc.stderr.read())

    train_proc.wait()

    # check if the stats reports any errors
    if len(stats['errors']) != 0:
        logging.error('HunPos failed with error messages ...')

        for error in stats['errors']:
            logging.error(error)

    return stats


class NOTagger (BaseTagger, object):
    """
    TextBlob compatible POS tagger class based on the NLTK HunPos wrapper.
    """
    def __init__(self, model_fn=None):
        self.tokenizer = NOTokenizer()
        self.tagger = HunposTagger(NO_TAGGER_DEFAULT_MODEL_FN,
                                   hunpos_tag_bin(), encoding='utf-8')

    def tag(self, text, tokenize=True):
        if tokenize:
            text = self.tokenizer.tokenize(text)

        return self.tagger.tag(text)
