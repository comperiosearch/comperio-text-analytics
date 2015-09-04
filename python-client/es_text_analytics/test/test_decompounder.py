from unittest import TestCase

from es_text_analytics.decompounder import NOBDecompounder, decompound_inner, flatten_inner, flatten


class TestNOBDecompounder(TestCase):
    def setUp(self):
        super(TestNOBDecompounder, self).setUp()

        self.fullform_index = {'ba': [{'pos': 'SUBST'}], 'bork': [{'pos': 'SUBST'}],
                               'borkbork': [{'pos': 'SUBST'}], 'boing': [{'pos': 'PRON'}]}


    def test_decompound(self):
        decompounder = NOBDecompounder(fullform_index=self.fullform_index, min_match=1)
        self.assertEqual(['ba', 'bork'], decompounder.decompound('babork'))
        self.assertEqual(['ba', 'borkbork'], decompounder.decompound('baborkbork'))
        self.assertEqual(['ba', 'ba'], decompounder.decompound('BaBa'))
        self.assertEqual(None, decompounder.decompound('BaBaa'))

    def test_decompound_no_prons(self):
        decompounder = NOBDecompounder(fullform_index=self.fullform_index, min_match=1)

        self.assertEqual(None, decompounder.decompound('baboing'))


class TestDecompounderHelpers(TestCase):
    def setUp(self):
        super(TestDecompounderHelpers, self).setUp()

        self.fullform_index = {'ba': [{'pos': 'SUBST'}], 'bork': [{'pos': 'SUBST'}], 'borkbork': [{'pos': 'SUBST'}]}

    def test_decompund_inner(self):
        self.assertEqual([['ba', ['ba']]], decompound_inner('baba', self.fullform_index, start=0, min_match=1))
        self.assertEqual([['ba']], decompound_inner('baba', self.fullform_index, start=2, min_match=1))
        self.assertEqual([], decompound_inner('baba', self.fullform_index, start=1, min_match=1))

    def test_flatten_inner(self):
        self.assertEqual([['ba', 'ba']], flatten_inner(['ba', ['ba']]))
        self.assertEqual([['ba']], flatten_inner(['ba']))
        self.assertEqual([['ba', 'ba'], ['ba', 'foo']], flatten_inner(['ba', ['ba'], ['foo']]))

    def test_flatten(self):
        self.assertEqual([['ba', 'ba'], ['ba'], ['ba', 'ba'], ['ba', 'foo']],
                         flatten([['ba', ['ba']], ['ba'], ['ba', ['ba'], ['foo']]]))