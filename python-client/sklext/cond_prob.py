import numpy
from numpy import array

from sklext.term_estimators import joint_estimator_point, marginal_estimator


def conditional_probabilities(X, y, ratio=False):
    p_t_c = joint_estimator_point(X, y, smoothing=True)
    p_t = marginal_estimator(X, smoothing=True)

    p_t.shape = 2,1

    m = p_t_c / p_t

    if ratio:
        p_c = marginal_estimator(y, smoothing=True)

        m = m / p_c

    return array(numpy.max(m, axis=1)).flatten()