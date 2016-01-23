from unittest import TestCase

from nose.tools import assert_true
from numpy import array
from numpy.ma.testutils import assert_array_approx_equal
from scipy.sparse import issparse
from scipy.sparse.csgraph._min_spanning_tree import csr_matrix

from sklext.term_weighting import TermWeightTransformer


class TestTermWeightTransformer(TestCase):
    def test_mi(self):
        X = array([[0, 1],
                   [1, 0],
                   [1, 1]])
        y = array([[0, 1],
                   [1, 0],
                   [1, 0]])

        transformer = TermWeightTransformer(method='mi')
        transformer.fit(X, y)

        assert_array_approx_equal(transformer._weights, [-0.37489, -0.605939], decimal=3)
        assert_array_approx_equal(transformer.transform(X), array([[0., -0.605939],
                                                                   [-0.37489, 0.],
                                                                   [-0.37489, -0.605939]]),
                                  decimal=3)

        transformer = TermWeightTransformer(method='mi')
        X = csr_matrix(X)
        y = csr_matrix(y)
        transformer.fit(X, y)
        newX = transformer.transform(X)

        assert_array_approx_equal(transformer._weights, [-0.37489, -0.605939], decimal=3)
        assert_true(issparse(newX))
        assert_array_approx_equal(newX.todense(), array([[0., -0.605939],
                                                         [-0.37489, 0.],
                                                         [-0.37489, -0.605939]]),
                                  decimal=3)

    def test_pmi(self):
        X = array([[0, 1],
                   [1, 0],
                   [1, 1]])
        y = array([[0, 1],
                   [1, 0],
                   [1, 0]])

        transformer = TermWeightTransformer(method='pmi')
        transformer.fit(X, y)

        assert_array_approx_equal(transformer._weights, [0.1178, 0.1178], decimal=3)
        assert_array_approx_equal(transformer.transform(X), array([[0., 0.1178],
                                                                   [0.1178, 0.],
                                                                   [0.1178, 0.1178]]),
                                  decimal=3)

        transformer = TermWeightTransformer(method='pmi')
        X = csr_matrix(X)
        y = csr_matrix(y)
        transformer.fit(X, y)
        newX = transformer.transform(X)

        assert_array_approx_equal(transformer._weights, [0.1178, 0.1178], decimal=3)
        assert_true(issparse(newX))
        assert_array_approx_equal(newX.todense(), array([[0., 0.1178],
                                                         [0.1178, 0.],
                                                         [0.1178, 0.1178]]),
                                  decimal=3)

    def test_npmi(self):
        X = array([[0, 1],
                   [1, 0],
                   [1, 1]])
        y = array([[0, 1],
                   [1, 0],
                   [1, 0]])

        transformer = TermWeightTransformer(method='npmi')
        transformer.fit(X, y)

        assert_array_approx_equal(transformer._weights, [0.1699, 0.0850], decimal=3)
        assert_array_approx_equal(transformer.transform(X), array([[0., 0.0850],
                                                                   [0.1700, 0.],
                                                                   [0.1700, 0.0850]]),
                                  decimal=3)

        transformer = TermWeightTransformer(method='npmi')
        X = csr_matrix(X)
        y = csr_matrix(y)
        transformer.fit(X, y)
        newX = transformer.transform(X)

        assert_array_approx_equal(transformer._weights, [0.1700, 0.0850], decimal=3)
        assert_true(issparse(newX))
        assert_array_approx_equal(newX.todense(), array([[0., 0.0850],
                                                         [0.1700, 0.],
                                                         [0.1700, 0.0850]]),
                                  decimal=3)
