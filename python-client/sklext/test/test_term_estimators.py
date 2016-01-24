from unittest import TestCase

from numpy import array
from numpy.ma.testutils import assert_array_approx_equal
from scipy.sparse import csr_matrix

from sklext.term_estimators import joint_estimator_point, joint_estimator_full


class TestTermEstimators(TestCase):
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