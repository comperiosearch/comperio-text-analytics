from math import log, e

import numpy
from numpy import array, zeros

from sklext.term_estimators import marginal_estimator, joint_estimator_point, joint_estimator_full


def mutual_information(X, y):
    num_terms = X.shape[1]
    num_classes = y.shape[1]

    p_c = marginal_estimator(y, smoothing=True)
    p_t = marginal_estimator(X, smoothing=True)

    p_t_c = joint_estimator_full(X, y, smoothing=True)

    ig = zeros((num_terms))

    for i in xrange(num_terms):
        for j in xrange(num_classes):
            ig[i] += p_t_c[0][i, j] * log(p_t_c[0][i, j] / (p_t[i] * p_c[j]))
            ig[i] += p_t_c[1][i, j] * log(p_t_c[1][i, j] / (p_t[i] * (1 - p_c[j])))
            ig[i] += p_t_c[2][i, j] * log(p_t_c[2][i, j] / ((1 - p_t[i]) * p_c[j]))
            ig[i] += p_t_c[3][i, j] * log(p_t_c[3][i, j] / ((1 - p_t[i]) * (1 - p_c[j])))

    return ig


def pointwise_mutual_information(X, y, normalize=False, k_weight=None, positive=None):
    p_c = marginal_estimator(y, smoothing=True)
    p_t = marginal_estimator(X, smoothing=True)

    p_t.shape = 2, 1
    p_c.shape = 1, 2

    p_t_c = joint_estimator_point(X, y, smoothing=True)

    if k_weight:
        p_t_c = p_t_c**k_weight

    m = numpy.log(array(p_t_c) / (p_t * p_c))

    if normalize:
        m = m / -numpy.log(p_t_c)

    if positive is 'cutoff':
        m[m < .0] = .0

    if positive is 'exp':
        m = e**m

    return array(numpy.max(m, axis=1)).flatten()
