# coding=iso-8859-1
from StringIO import StringIO
from unittest import TestCase

from es_text_analytics.data.aviskorpus import section_1_header_line, section_1_parser, section_2_header_line, \
    section_2_parser, section_3_parser

SECTION_1_SAMPLE_1 = """
<U #http://odin.dep.no/fd/prm/1998/k4/981013.html>
|
<B OD>
<A 98>
<M 10>
<D 13>
Pressemelding
Nr
.
064/98
Dato
:
13
oktober
1998
<U #http://odin.dep.no/fid/prm/1998/k4/981016.html>
|
<B OD>
<A 98>
<M 10>
<D 16>
Pressemelding
Nr
.
55/98
Dato
16
.
oktober
1998
"""

SECTION_1_SAMPLE_2 = """
<U #http://www.adressa.no/artikkel.awml?artikkelref=907584799>
|
<B AA>
<A 98>
<M >
<D 10>
Ap
:
"""

SECTION_2_SAMPLE = """
##U #http://www.adressa.no/kultur/musikk/anmeldelser/article1015398.ece>
##B AA>
##A 08>
##M 01>
##D 22>
Publisert 22.01.2008 - 08:30 |  Endret: 22.01.2008 - 09:01  ¶
The Margarets:  TWENTY YEARS ERASED  ¶
Blass pop ¶
##U #http://www.adressa.no/nyheter/innenriks/article1015179.ece>
##B AA>
##A 08>
##M 01>
##D 21>
Publisert 21.01.2008 - 18:45 |  Endret: 21.01.2008 - 21:11  ¶
Gigantutslipp fra StatoilHydro:  ¶
Svært skuffet miljøvernminister¶
"""

SECTION_3_SAMPLE_1 = """
<?xml version="1.0" encoding="ISO-8859-1"?>
<!DOCTYPE document SYSTEM "http://gandalf.aksis.uib.no/aviskorpus/avis2.dtd">
<document>
<header>
<attribute name="file" value="KK/nob/2011/09/01/20110901-59238.xml"/>
<attribute name="url" value="http://www.klassekampen.no/artikler/59238/article/item/null 690 4 20 4234"/>
<attribute name="source" value="KK"/>
<attribute name="date" value="2011-09-01"/>
<attribute name="author" value="Olav Østrem"/>
<attribute name="gender" value="M"/>
<attribute name="class1" value=""/>
<attribute name="class2" value=""/>
<attribute name="language" value="nob"/>
</header>
<body>
<div type="title" level="1">Velgerne avgjør kinosalg</div>
<div type="ingress">Venstresida i Bergen frykter for kinotilbudet og byens internasjonale filmfestival etter at de borgerlige har vedtatt å delprivatisere byens kino.</div>
<div type="author">Av Olav Østrem</div>
<div type="date">Torsdag 1. september, 2011</div>
<div type="caption">PÅ VEI TIL MARKEDET: Bergen Kino vurderes solgt for å gi penger i kommunekassa. Her fra Konsertpaleet under Den Store Kinodagen 2010. FOTO: Harald Sejersted, BERGEN KINO</div>
<div type="text">
<p>Også BIFF i fare</p>
<p>Savner Warloe</p>
</div></body></document>
"""

SECTION_3_SAMPLE_2 = """
<?xml version="1.0" encoding="ISO-8859-1"?>
<!DOCTYPE document SYSTEM "http://gandalf.aksis.uib.no/aviskorpus/avis2.dtd">
<document>
<header>
<attribute name="file" value="SP/nob/2009/01/03/20090103-28041638.xml"/>
<attribute name="url" value="http://www.smp.no/article/20090103/NYHETER/28041638 114 57 69 1203 ## %%"/>
<attribute name="source" value="SP"/>
<attribute name="date" value="2009-01-03 03:45"/>
<attribute name="author" value=""/>
<attribute name="gender" value="U"/>
<attribute name="class1" value="nyheter"/>
<attribute name="class2" value="nyheter"/>
<attribute name="language" value="nob"/>
</header>
<body>
<div type="title" level="1">Måketips!</div>
<div type="ingress">Selv om det er vinter, er det ikke sikkert det er snø ute. Men når den kommer, og du må fram med måkebrettet, er det godt å vite hvordan du skal bruke det uten å risikere å ødelegge ryggen din. Og for de som er av en litt bedagelig natur er det også greit med en påminner om hvor mye snø taket tåler før du MÅ opp av sofaen for å måke.</div>
<div type="author"></div>
<div type="date">Publisert lørdag 03. januar 2009 kl. 03:45.</div>
<div type="caption"><p><div style="backgrounD:#ffcc00;"><object classid="clsid:d27cdb6e-ae6d-11cf-96b8-444553540000" codebase="http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=9,0,0,0" width="468" height="300" id="FLA00030Snømåking" align="middle"> <param name="allowScriptAccess" value="sameDomain" /> <param name="allowFullScreen" value="false" /> <param name="movie" value="http://mediacontent.sm.publicus.com/pdf/SM3953081230.SWF" /><param name="quality" value="high" /><param name="bgcolor" value="#ffffff" /> <embed src="http://mediacontent.sm.publicus.com/pdf/SM3953081230.SWF" quality="high" bgcolor="#ffffff" width="468" height="300" name="FLA00030Snømåking" align="middle" allowScriptAccess="sameDomain" allowFullScreen="false" type="application/x-shockwave-flash" pluginspage="http://www.macromedia.com/go/getflashplayer" /> </object></div></p></div>
<div type="text">
<p></p>
<p></p>
<p></p>
<p></p>
</div></body></document>
"""

class TestAviskorpusHelpers(TestCase):
    def test_section_1_header_line(self):
        self.assertEqual('http://odin.dep.no/fid/prm/1998/k4/981016.html',
                         section_1_header_line('<U #http://odin.dep.no/fid/prm/1998/k4/981016.html>'))
        self.assertIsNone(section_1_header_line('Fiskeridepartementet'))
        self.assertIsNone(section_1_header_line('<A 98>'))

    def test_section_1_parser(self):
        result = list(section_1_parser(StringIO(SECTION_1_SAMPLE_1)))
        self.assertEqual(2, len(result))
        self.assertEqual('http://odin.dep.no/fd/prm/1998/k4/981013.html', result[0]['url'])
        self.assertEqual('OD', result[0]['source'])
        self.assertEqual(98, result[0]['pub_year'])
        self.assertEqual(10, result[0]['pub_month'])
        self.assertEqual(13, result[0]['pub_day'])
        self.assertEqual(1, result[0]['corpus_section'])
        self.assertEqual(['Pressemelding', 'Nr', '.', '064/98', 'Dato', ':', '13', 'oktober', '1998'],
                         result[0]['tokens'])

        self.assertEqual('http://odin.dep.no/fid/prm/1998/k4/981016.html', result[1]['url'])
        self.assertEqual('OD', result[1]['source'])
        self.assertEqual(98, result[1]['pub_year'])
        self.assertEqual(10, result[1]['pub_month'])
        self.assertEqual(16, result[1]['pub_day'])
        self.assertEqual(1, result[1]['corpus_section'])
        self.assertEqual(['Pressemelding', 'Nr', '.', '55/98', 'Dato', '16', '.', 'oktober', '1998'],
                         result[1]['tokens'])

    def test_section_1_parser_missing_meta(self):
        result = list(section_1_parser(StringIO(SECTION_1_SAMPLE_2)))
        self.assertEqual(1, len(result))
        self.assertEqual('http://www.adressa.no/artikkel.awml?artikkelref=907584799', result[0]['url'])
        self.assertEqual('AA', result[0]['source'])
        self.assertEqual(98, result[0]['pub_year'])
        self.assertEqual(None, result[0]['pub_month'])
        self.assertEqual(10, result[0]['pub_day'])
        self.assertEqual(1, result[0]['corpus_section'])
        self.assertEqual(['Ap', ':'], result[0]['tokens'])

    def test_section_2_header_line(self):
        self.assertEqual('http://fotball.adressa.no/afrika/article98614.ece',
                         section_2_header_line('##U #http://fotball.adressa.no/afrika/article98614.ece>'))
        self.assertIsNone(section_2_header_line('##B AA>'))
        self.assertIsNone(section_2_header_line('for  at i fotball er alt mulig.  ¶'))

    def test_section_2_parser(self):
        result = list(section_2_parser(StringIO(SECTION_2_SAMPLE)))
        self.assertEqual(2, len(result))

        self.assertEqual('http://www.adressa.no/kultur/musikk/anmeldelser/article1015398.ece', result[0]['url'])
        self.assertEqual('AA', result[0]['source'])
        self.assertEqual(8, result[0]['pub_year'])
        self.assertEqual(1, result[0]['pub_month'])
        self.assertEqual(22, result[0]['pub_day'])
        self.assertEqual(2, result[0]['corpus_section'])
        self.assertEqual(['Publisert 22.01.2008 - 08:30', 'Endret: 22.01.2008 - 09:01',
                          'The Margarets:  TWENTY YEARS ERASED', 'Blass pop'],
                         result[0]['sentences'])

        self.assertEqual('http://www.adressa.no/nyheter/innenriks/article1015179.ece', result[1]['url'])
        self.assertEqual('AA', result[1]['source'])
        self.assertEqual(8, result[1]['pub_year'])
        self.assertEqual(1, result[1]['pub_month'])
        self.assertEqual(21, result[1]['pub_day'])
        self.assertEqual(2, result[1]['corpus_section'])
        self.assertEqual(['Publisert 21.01.2008 - 18:45', 'Endret: 21.01.2008 - 21:11',
                          'Gigantutslipp fra StatoilHydro:', u'Svært skuffet miljøvernminister'],
                         result[1]['sentences'])

    def test_section_3_parser(self):
        result = section_3_parser(StringIO(SECTION_3_SAMPLE_1))

        self.assertEqual('KK/nob/2011/09/01/20110901-59238.xml', result['metadata']['file'])
        self.assertEqual('http://www.klassekampen.no/artikler/59238/article/item/null 690 4 20 4234',
                         result['metadata']['url'])
        self.assertEqual('KK', result['metadata']['source'])
        self.assertEqual('2011-09-01', result['metadata']['date'])
        self.assertEqual(u"Olav Østrem", result['metadata']['author'])
        self.assertEqual('M', result['metadata']['gender'])
        self.assertEqual('', result['metadata']['class1'])
        self.assertEqual('', result['metadata']['class2'])
        self.assertEqual('nob', result['metadata']['language'])
        self.assertEqual(u'Velgerne avgjør kinosalg', result['title'])
        self.assertEqual(u'Venstresida i Bergen frykter for kinotilbudet og byens internasjonale filmfestival etter at de borgerlige har vedtatt å delprivatisere byens kino.',
                         result['ingress'])
        self.assertEqual(u"Av Olav Østrem", result['author'])
        self.assertEqual('Torsdag 1. september, 2011', result['date'])
        self.assertEqual(u'PÅ VEI TIL MARKEDET: Bergen Kino vurderes solgt for å gi penger i kommunekassa. Her fra Konsertpaleet under Den Store Kinodagen 2010. FOTO: Harald Sejersted, BERGEN KINO',
                         result['caption'])
        self.assertEqual(3, result['corpus_section'])
        self.assertEqual([u'Også BIFF i fare', u'Savner Warloe'], result['text'])

        result = section_3_parser(StringIO(SECTION_3_SAMPLE_2))

        self.assertEqual('SP/nob/2009/01/03/20090103-28041638.xml', result['metadata']['file'])
        self.assertEqual('http://www.smp.no/article/20090103/NYHETER/28041638 114 57 69 1203 ## %%',
                         result['metadata']['url'])
        self.assertEqual('SP', result['metadata']['source'])
        self.assertEqual('2009-01-03 03:45', result['metadata']['date'])
        self.assertEqual('', result['metadata']['author'])
        self.assertEqual('U', result['metadata']['gender'])
        self.assertEqual('nyheter', result['metadata']['class1'])
        self.assertEqual('nyheter', result['metadata']['class2'])
        self.assertEqual('nob', result['metadata']['language'])
        self.assertEqual(u'Måketips!', result['title'])
        self.assertEqual(u'Selv om det er vinter, er det ikke sikkert det er snø ute. Men når den kommer, og du må fram med måkebrettet, er det godt å vite hvordan du skal bruke det uten å risikere å ødelegge ryggen din. Og for de som er av en litt bedagelig natur er det også greit med en påminner om hvor mye snø taket tåler før du MÅ opp av sofaen for å måke.',
                         result['ingress'])
        self.assertEqual('', result['author'])
        self.assertEqual(u'Publisert lørdag 03. januar 2009 kl. 03:45.', result['date'])
        self.assertEqual('', result['caption'])
        self.assertEqual(3, result['corpus_section'])
        self.assertEqual([], result['text'])
