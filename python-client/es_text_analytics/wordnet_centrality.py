from operator import itemgetter

import networkx as nx

"""
Experimental concept mining technique.

Takes a weighted list of terms and returns the central WordNet Synsets for those terms.

terms = [(u'gruppe', 1.0308515122783903), (u'skarabider', 1.0283549292633594), (u'utbredelse', 1.0255859517307202),
         (u'slekt', 1.02428182204782), (u'h\xf8re', 1.0236714839113259), (u'oldenborre', 1.0212900521382506),
         (u'art', 1.0206984849354699), (u'leve', 1.0181363254554074), (u'scarabaeoidea', 1.0178225609839886),
         (u'melolonthinae', 1.0137513034441485), (u'stor', 1.010924267580678),
         (u'underfamilie', 1.010754657594739), (u'sm\xe5', 1.0095704409677608), (u'underart', 1.0092106422118465),
         (u'millimeter', 1.009166357579949), (u'dekkvinge', 1.0077143382226799), (u'afrika', 1.0073806489590316),
         (u'pronotum', 1.0065698471665749), (u'gullbasse', 1.0065362930098589), (u'amerika', 1.0062859498858436),
         (u'parasittveps', 1.0060005533568113), (u'parasitt', 1.0060), (u'veps', 1.0060), (u'australia', 1.0058669303831191),
         (u'finnes', 1.0057317293824628),
         (u'gammaridea', 1.0056893049779934), (u'lang', 1.00559787835873), (u'familie', 1.0054340556687946),
         (u'parasitoide', 1.0053805526619595), (u'gjerne', 1.00537793821737), (u'taksonomisk', 1.005285633510592),
         (u'jorda', 1.005110740380347), (u's\xf8r', 1.0049040009707946), (u'asia', 1.0047862880057254),
         (u'panamerikansk', 1.0046940558397519), (u'svart', 1.0046021508509742), (u'inndeling', 1.0045280362592695),
         (u'omfatte', 1.0045210803669595), (u'cm', 1.004380770050699), (u'cetoniinae', 1.0042811151167377),
         (u'kjent', 1.0042292429979698), (u'praktskarabide', 1.0042044116189903), (u'\xe9n', 1.0041848737627979),
         (u'rutelinae', 1.0041419789388988), (u'ganske', 1.0039716523273752), (u'lys', 1.0036022222516647)]

c = ConceptClassifier()
c.concepts(terms)

[(u'*ROOT*', 0.6080213703117321),
...
 (u'social_group', 0.06255333412324249),
 (u'collection', 0.06117590141836287),
 (u'cognition', 0.050449579778215264),
 (u'position', 0.050446927402192525),
 (u'h\xf8re', 0.04431870710158872),
 (u'kin', 0.02783831781626138),
 (u'gruppe', 0.02340480985900115),
 (u'content', 0.022421702867730226),
 (u'direction', 0.022415540534822163),
 (u'genealogy', 0.012455836088714487),
 (u'idea', 0.009964750496621828),
 (u'compass_point', 0.009950798727198123),
 (u'lineage', 0.005723405829441778),
 (u'concept', 0.0044278959856953815),
 (u'cardinal_compass_point', 0.004396465865842209),
 (u'family', 0.002965638904359013),
 (u'category', 0.0019660280031428582),
 (u'south', 0.0018952926436456173),
 (u'slekt', 0.0011273697128777484),
 (u'familie', 0.0011066250305903473),
 (u'kind', 0.0008694833352302178),
 (u's\xf8r', 0.0007068536091788623),
 (u'type', 0.0003767580775104511),
 (u'art', 0.00014272125955615077)]

plt.figure(3,figsize=(12,12))
nx.draw(c.g, with_labels=True, font_size=8)

"""


def _create_subgraph(paths, root):
    g = nx.Graph()

    for ss_path in paths:
        for ss1, ss2 in zip(ss_path, ss_path[1:]):
            ss1_name = ss1[0]
            weight = ss1[1]
            ss2_name = ss2[0]

            g.add_node(ss1_name)
            g.add_node(ss2_name)
            g.add_edge(ss1_name, ss2_name, {'w': weight})

            if ss2_name == root:
                break

    return g


def _path_root(paths):
    path_root = None

    for ss_level in zip(*[reversed(p) for p in paths]):
        names = [x[0] for x in ss_level]

        if len(set(names)) == 1:
            path_root = names[0]

    return path_root


class ConceptFinder(object):
    def __init__(self, lang='nob'):
        super(ConceptFinder, self).__init__()

        from nltk.corpus import wordnet as wordnet

        self.lang = lang
        self.wordnet = wordnet
        self.graph = None

    def concepts(self, terms):
        paths = self._synset_paths(terms)
        root = _path_root(paths).split('.')[0]
        self.graph = _create_subgraph(paths, root)

        return sorted(nx.eigenvector_centrality_numpy(self.graph, weight='w').items(),
                      key=lambda x: x[1], reverse=True)

    def _top_synset(self, term):
        ss = self.wordnet.synsets(term)

        if len(ss) >= 1:
            return ss[0]

        return None

    def _synset_paths(self, terms):
        paths = []

        for term, score, ss in [(term, score, self.wordnet.synsets(term, lang=self.lang)) for term, score in terms]:
            if len(ss) >= 1:
                paths.append([(term, score)] + [(x[0].name().split('.')[0], 1.0)
                                                for x in sorted(ss[0]._shortest_hypernym_paths(True).items(),
                                                                key=itemgetter(1))])

        return paths
