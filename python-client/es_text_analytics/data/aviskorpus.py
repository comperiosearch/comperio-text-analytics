# coding=utf-8
import logging
import os
import re
import unicodedata
from StringIO import StringIO
from gzip import GzipFile
from tarfile import TarFile
from zipfile import ZipFile

from bs4 import BeautifulSoup

from es_text_analytics.data.dataset import Dataset

AVISKORPUS_ARCHIVE_URL='http://www.nb.no/sbfil/tekst/norsk_aviskorpus.zip'

# Map of corpus sections, corresponding files inside the main archive and codes for the newspaper in
# each section. See http://www.nb.no/sprakbanken/show?serial=sbr-4&lang=nb for details.
CORPUS_SECTIONS = {
    '1': {'paths': ['1/19981013-20010307.gz',
                    '1/20010308-20030116.gz',
                    '1/20030116-20050403.gz'],
          'name': 'ti-aviser-1998-2005',
          'sources': ['aa', 'ap', 'bt', 'da', 'db',
                      'dn', 'fv', 'nl', 'sa', 'vg']},
    '2': {'paths': ['2/aa.tar.gz',
                    '2/ap.tar.gz',
                    '2/bt.tar.gz',
                    '2/da.tar.gz',
                    '2/db.tar.gz',
                    '2/dn.tar.gz',
                    '2/fv.tar.gz',
                    '2/nl.tar.gz',
                    '2/sa.tar.gz',
                    '2/vg.tar.gz'],
          'name': 'ti-aviser-2005-2011',
          'sources': ['aa', 'ap', 'bt', 'da', 'db',
                      'dn', 'fv', 'nl', 'sa', 'vg']},
    '3': {'paths': ['3/dt.tar.gz',
                    '3/fi.tar.gz',
                    '3/hd.tar.gz',
                    '3/ho.tar.gz',
                    '3/kk.tar.gz',
                    '3/na.tar.gz',
                    '3/sh.tar.gz',
                    '3/so.tar.gz',
                    '3/sp.tar.gz',
                    '3/vb.tar.gz',
                    '3/vt.tar.gz'],
          'name': 'andre-aviser',
          'sources': ['dt', 'fi', 'hd', 'ho', 'kk', 'na',
                      'sh', 'so', 'sp', 'vb', 'vt']}}


def match_or_none(pattern, string, flags=0):
    """
    Small wrapper for reqexes with one match group which may or may not match.

    Matches on whole string not just the beginning (ie. uses re.search).

    :param pattern: Regular expression with a single match group.
    :type pattern: unicode|str
    :param string: String to match against.
    :type string: unicode|str
    :param flags:
    :rtype : str|unicode|None
    :return: The match group string.
    """
    m = re.search(pattern, string, flags=flags)

    if m:
        if len(m.groups()) == 1:
            return m.group(1)

        return m.groups()


def section_1_header_line(line):
    """
    Detects and extracts url from section 1 header line.

    :param line: Line from section 1 data file.
    :type line: str|unicode
    :rtype : None|unicode|str
    :return: Return the url in the header or None if the passed string is not a section 1 header line.
    """
    m = re.search('<U #(http://.*)>', line)

    if m:
        return m.group(1)


def section_1_parser(fileobj):
    """
    Parser for section 1 data files.
    Returns a generator with dict instances with the article data.

    :param fileobj: A file like instance with section 1 formatted text.
    :rtype : generator
    """
    line = fileobj.readline()
    tokens = []
    doc = None

    while line:
        line = line.decode('latin1')
        line = line.strip()

        if line == '':
            pass
        elif section_1_header_line(line):
            # skip empty documents
            if tokens:
                doc['tokens'] = [unicodedata.normalize('NFC', unicode(token)) for token in tokens]
                doc['corpus_section'] = 1

                yield doc
                tokens = []

            url = section_1_header_line(line)
            fileobj.readline()
            source_code = match_or_none('^<B (\w\w)>$', fileobj.readline().strip())
            year = match_or_none('^<A (\d\d)>$', fileobj.readline().strip())
            pub_year = int(year) if year else None
            month = match_or_none('^<M (\d\d)>$', fileobj.readline().strip())
            pub_month = int(month) if month else None
            day = match_or_none('^<D (\d\d)>$', fileobj.readline().strip())
            pub_day = int(day) if day else None

            doc = {'url': url, 'source': source_code,
                   'pub_year': pub_year, 'pub_month': pub_month, 'pub_day': pub_day}
        else:
            # article content consists of tokens, one on each line
            tokens.append(line)

        line = fileobj.readline()

    # catch the last document
    if doc and tokens:
        doc['tokens'] = [unicodedata.normalize('NFC', unicode(token)) for token in tokens]
        doc['corpus_section'] = 1

        yield doc


def section_2_header_line(line):
    """
    Detects and extracts url from section 2 header line.

    :param line: Line from section 2 data file.
    :type line: str|unicode
    :rtype : None|unicode|str
    :return: Return the url in the header or None if the passed string is not a section 1 header line.
    """
    m = re.search('##U #(http://.*)>', line)

    if m:
        return m.group(1)


def section_2_parser(fileobj):
    """
    Parser for section 2 data files.
    Returns a generator with dict instances with the article data.

    :param fileobj: A file like instance with section 2 formatted text.
    :rtype : generator
    """
    line = fileobj.readline()
    text = ''
    doc = None

    while line:
        line = line.decode('latin1')
        line = line.strip()

        if line == '' or line == '|':
            pass
        elif section_2_header_line(line):
            # skip articles with no content
            if text and doc:
                # content consists of text lines with header sections delimited by | characters and
                # sentences delimited by paragraph characters
                text = text.replace(u'¶', u'|')
                doc['sentences'] = [unicodedata.normalize('NFC', unicode(sent.strip()))
                                    for sent in text.split(u'|') if sent.strip() != '']
                doc['corpus_section'] = 2

                yield doc
                text = ''

            url = section_2_header_line(line)
            source_code = match_or_none('^##B (\w\w)>$', fileobj.readline().strip())
            year = match_or_none('^##A (\d\d)>$', fileobj.readline().strip())
            pub_year = int(year) if year else None
            month = match_or_none('^##M (\d\d)>$', fileobj.readline().strip())
            pub_month = int(month) if month else None
            day = match_or_none('^##D (\d\d)>$', fileobj.readline().strip())
            pub_day = int(day) if day else None

            doc = {'url': url, 'source': source_code,
                   'pub_year': pub_year, 'pub_month': pub_month, 'pub_day': pub_day}
        else:
            text += line

        line = fileobj.readline()

    # yield the last document in the file
    if doc and text:
        text = text.replace(u'¶', u'|')
        doc['sentences'] = [unicodedata.normalize('NFC', unicode(sent.strip()))
                            for sent in text.split(u'|') if sent.strip() != '']
        doc['corpus_section'] = 2
        yield doc


def section_3_parser(fileobj):
    """
    Parser for section 3 data files.
    Returns a dict instance with the article data.

    :param fileobj: A file like instance with section 2 formatted text.
    :rtype : dict
    """
    xml_doc = BeautifulSoup(fileobj)

    # each article is in a separate XML file. We pick out metadata from attribute tags and div
    # tags with the type attribute. The content is in a div tag with the text attribute.
    metadata = dict([(a['name'], unicodedata.normalize('NFC', unicode(a['value']).strip()))
                     for a in xml_doc.find_all('attribute')])
    text = [unicodedata.normalize('NFC', unicode(t.text).strip())
            for t in xml_doc.find('div', type='text').find_all('p')]

    doc = dict([(t.attrs['type'], unicodedata.normalize('NFC', unicode(t.text).strip())) for t in xml_doc.find_all('div')
                if 'type' in t.attrs and t.attrs['type'] != 'text'])
    doc['text'] = [t for t in text if t != '']
    doc['metadata'] = metadata
    doc['corpus_section'] = 3

    return doc


def iterator(dataset_fn, sections=None, sources=None):
    """
    Generator that yields all the documents in the korpus.
    The generator can return only specific newspaper or sections if specified in
    the arguments,

    :param dataset_fn: Dataset archive file. None uses default location.
    :type dataset_fn: str|unicode|None
    :param sections: Sections to include. The default None yields all sections.
    :type sections: list[int|long]|None
    :param sources: Newspaper sources to include. The default None yields all sources.
    :type sources: list[str|unicode]|None
    :rtype : generator
    """
    count = 0

    with ZipFile(dataset_fn) as zf:
        # corpus content files are compressed and archived in various ways inside the corpus zip archive.
        if not sections or 1 in sections:
            for fn in CORPUS_SECTIONS['1']['paths']:
                logging.info('Reading %s ...' % fn)

                with GzipFile(fileobj=StringIO(zf.read(fn))) as iz:
                    try:
                        for doc in section_1_parser(iz):
                            if sources is None or doc['source'] in sources:
                                yield doc
                                count += 1

                                if count != 0 and count % 1000 == 0:
                                    logging.info("Read %d files ..." % count)
                    except Exception:
                        logging.error("Parse failure while reading %s ..." % fn)

        if not sections or 2 in sections:
            for fn in CORPUS_SECTIONS['2']['paths']:
                if sources and not os.path.basename(fn).split('.')[0] in sources:
                    continue

                logging.info('Reading %s ...' % fn)

                # TarFile with compression doesn't work inside a ZipFile
                # Uncompress to a StringIO object and hand that to TarFile
                with GzipFile(fileobj=StringIO(zf.read(fn))) as iz:
                    with TarFile(fileobj=iz) as tf:
                        for member in tf.getmembers():

                            if member.isfile():
                                tif = tf.extractfile(member)

                                try:
                                    for doc in section_2_parser(tif):
                                        yield doc
                                        count += 1

                                        if count != 0 and count % 1000 == 0:
                                            logging.info("Read %d files ..." % count)
                                except Exception:
                                    logging.error("Parse failure while reading %s ..." % fn)

                                tif.close()

        if not sections or 3 in sections:
            for fn in CORPUS_SECTIONS['3']['paths']:
                if sources and not os.path.basename(fn).split('.')[0] in sources:
                    continue

                logging.info('Reading %s ...' % fn)

                # Same tar.gz inside zip problem as with section 2
                with GzipFile(fileobj=StringIO(zf.read(fn))) as iz:
                    with TarFile(fileobj=iz) as tf:
                        for member in tf.getmembers():
                            if member.isfile():
                                tif = tf.extractfile(member)

                                if os.path.splitext(member.name)[1] != '.xml':
                                    continue

                                try:
                                    doc = section_3_parser(tif)

                                    yield doc
                                    count += 1

                                except Exception:
                                    logging.error("Unable to parse file %s ..." % member.name)

                                if count != 0 and count % 1000 == 0:
                                    logging.info("Read %d files ..." % count)

                                tif.close()


def normalize(doc):
    """
    Normalizes content from the Aviskorpus to a single string with the article text in a separate 'text' field.

    :param doc: Parsed document from the corpus.
    :type doc: dict
    :rtype : dict
    :return: The passed document dict with normalized 'text' field added.
    :raise ValueError: If the section_id field is malformed
    """
    section_id = doc['corpus_section']

    if section_id == 1:
        doc['text'] = ' '.join(doc['tokens'])
    elif section_id == 2:
        doc['text'] = '\n'.join(doc['sentences'])
    elif section_id == 3:
        doc['raw'] = doc['text']
        doc['text'] = '\n\n'.join(doc['text'])

        if ('metadata' in doc) and ('source' in doc['metadata']):
            doc['source'] = doc['metadata']['source']
    else:
        raise ValueError('Unknown section id %d in document ...' % section_id)

    return doc


class AviskorpusDataset(Dataset):
    """
    Class encapsulating Norsk Aviskorpus, a large corpus of Norwegian newspaper articles.

    See http://www.nb.no/sprakbanken/show?serial=sbr-4&lang=nb for details.
    """
    def __init__(self, index='aviskorpus', doc_type='article', dataset_path=None,
                 sections=None, sources=None, dataset_fn=None):
        super(AviskorpusDataset, self).__init__(index=index, doc_type=doc_type, dataset_path=dataset_path,
                                                dataset_fn=dataset_fn)

        self.archive_fn = AVISKORPUS_ARCHIVE_URL
        
        self.sections = sections
        self.sources = sources
        self.normalize_func = normalize

    def _iterator(self):
        return iterator(self.dataset_fn, sections=self.sections, sources=self.sources)
