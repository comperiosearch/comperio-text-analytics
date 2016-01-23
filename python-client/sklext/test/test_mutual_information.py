from unittest import TestCase

from numpy import array
from numpy.ma.testutils import assert_array_approx_equal
from scipy.sparse.csr import csr_matrix

from sklext.mutual_information import mutual_information, pointwise_mutual_information, joint_estimator_point, \
    joint_estimator_full


class TestMutualInformation(TestCase):
    def test_mutual_information(self):
        X = array([[0, 1],
                   [1, 0],
                   [1, 1]])
        y = array([[0, 1],
                   [1, 0],
                   [1, 0]])

        assert_array_approx_equal(mutual_information(X, y), [-0.37489, -0.605939], decimal=3)
        assert_array_approx_equal(mutual_information(csr_matrix(X), csr_matrix(y)), [-0.37489, -0.605939], decimal=3)

    def test_pointwise_mutual_information(self):
        X = array([[0, 1],
                   [1, 0],
                   [1, 1]])
        y = array([[0, 1],
                   [1, 0],
                   [1, 0]])

        assert_array_approx_equal(pointwise_mutual_information(X, y), [0.1178, 0.1178], decimal=3)
        assert_array_approx_equal(pointwise_mutual_information(csr_matrix(X), csr_matrix(y)),
                                  [0.1178, 0.1178], decimal=3)

    def test_joint_estmator_point(self):
        X = array([[0, 1],
                   [1, 0],
                   [1, 1]])
        y = array([[0, 1],
                   [1, 0],
                   [1, 0]])

        assert_array_approx_equal(joint_estimator_point(X, y), [[.5, 0], [.25, .25]])
        assert_array_approx_equal(joint_estimator_point(csr_matrix(X), csr_matrix(y)), [[.5, 0], [.25, .25]])

    def test_joint_estimator_full(self):
        X = array([[0, 1],
                   [1, 0],
                   [1, 1]])
        y = array([[0, 1],
                   [1, 0],
                   [1, 0]])

        assert_array_approx_equal(joint_estimator_full(X, y),
                                  [[[.1667, .0], [.0833, .0833]],
                                   [[.0 , .1667], [.0833, .0833]],
                                   [[.0 , .0833], [.0833, .0]],
                                   [[.0833, .0], [.0, .0833]]],
                                  decimal=3)
        assert_array_approx_equal(joint_estimator_full(csr_matrix(X), csr_matrix(y)),
                                  [[[.1667, .0], [.0833, .0833]],
                                   [[.0 , .1667], [.0833, .0833]],
                                   [[.0 , .0833], [.0833, .0]],
                                   [[.0833, .0], [.0, .0833]]],
                                  decimal=3)