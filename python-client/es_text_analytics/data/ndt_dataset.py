# coding=utf-8
import logging
from operator import itemgetter
import os
from tarfile import TarFile

from es_text_analytics.data.dataset import Dataset, parse_conll, CONLL_U_FIELDS

NDT_ARCHIVE_URL='http://www.nb.no/sbfil/tekst/20140328_NDT_1-01.tar.gz'


def filelist(lang=None, sections=None):
    """
    Generate a list of filenames corresponding to languages (Nynorsk and Bokmål)
     and source sections in the Treebank. Default is to include all lsnguages
     and sections.

    :param lang:
    :type lang: str|unicode|None
    :param sections:
    :type sections: list[str|unicode]|None
    :rtype : list[str|unicode]
    :return: list of filenames corresponding to the specified Treebank content.
    """
    files = []

    if not sections:
        sections = ['ndt_1-0']
    else:
        sections = ['%s_ndt_1-0' % s for s in sections]

    if not lang:
        lang = ['nob', 'nno']
    else:
        lang = [lang]

    for s in sections:
        for l in lang:
            files.append('%s_%s.conll' % (s, l))

    return files


def iterator(dataset_fn, sections=None, lang=None, field_indices=None):
    """
    Provides an iterator of CONLL formatted sentences from NDT.

    :param dataset_fn: Path to Newsgroups dataset archive file.
    :type dataset_fn: unicode|str
    :param sections:
    :type sections: list[str|unicode]|None
    :param lang:
    :type lang: list[str|unicode]|None
    :rtype : generator
    """
    files = filelist(lang=lang, sections=sections)

    with TarFile.open(dataset_fn, 'r:gz') as f:
        for member in f:
            if member.isfile() and os.path.basename(member.name) in files:
                logging.info('parsing %s ...' % member.name)
                m_f = f.extractfile(member)

                for sentence in parse_conll(m_f, field_indices=field_indices):
                    yield sentence

                m_f.close()


def normalize(doc):
    """
    Normalize a treebank sentence to a string with the token forms.

    :param doc: Parsed CONLL sentence.
    :type doc: list[list]
    :rtype : dict[str|unicode, str|unicode]
    :return: A document dict with the normalized sentence in the 'content' key.
    """
    return {'content': u' '.join(map(itemgetter(1), doc))}


class NDTDataset(Dataset):
    """
    Class encapsulating the Norwegian Dependency Treebank. Uses the main CONLL data files.
    See http://www.nb.no/sprakbanken/show?serial=sbr-10&lang=nb for details.
    """


    def __init__(self, index='ndt', doc_type='sentence', dataset_path=None,
                 dataset_fn=None, lang=None, sections=None, fields=None,
                 normalize_func=normalize):
        """
        Default includes all sections, languages and fields.

        :param sections: Sections to include (blog, newspaper, partliament, report).
        :type sections: list[str|unicode]|None
        :param lang: Languages to include (nno, nob).
        :type lang: list[str|unicode]|None
        :param fields: Columns to include (index, form, lemma, cpostag, postag, feats, head, deprel, deps, misc).
        :type fields: list[str|unicode]|None
        """
        super(NDTDataset, self).__init__(index=index, doc_type=doc_type, dataset_path=dataset_path,
                                         dataset_fn=dataset_fn, normalize_func=normalize_func)

        self.archive_fn = NDT_ARCHIVE_URL
        self.field_indices = None
        self.fields = CONLL_U_FIELDS

        if fields:
            self.fields = fields
            self.field_indices = [CONLL_U_FIELDS.index(f) for f in fields]

        self.sections = sections
        self.lang = lang

    def _iterator(self):
        return iterator(self.dataset_fn, sections=self.sections,
                        lang=self.lang, field_indices=self.field_indices)
