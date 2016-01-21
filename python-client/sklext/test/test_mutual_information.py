from unittest import TestCase

from numpy import array
from numpy.ma.testutils import assert_array_approx_equal
from scipy.sparse.csr import csr_matrix

from sklext.mutual_information import mutual_information


class TestMutualInformation(TestCase):
    def test_mutual_information(self):
        X = array([[0, 1],
                   [1, 0],
                   [1, 1]])
        y = array([[0, 1],
                   [1, 0],
                   [1, 0]])

        assert_array_approx_equal(mutual_information(X, y), [0.6365, 0.1744], decimal=3)
        assert_array_approx_equal(mutual_information(csr_matrix(X), csr_matrix(y)), [0.6365, 0.1744], decimal=3)
