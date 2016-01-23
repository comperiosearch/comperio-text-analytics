from itertools import izip
from math import log

import numpy
from numpy import array, sum, zeros, newaxis
from scipy.sparse import issparse


def add_smoothing(m, amount=10**-12):
    m = m.astype(numpy.float)
    m[m == 0] = amount

    return m

def indicator_estimator(X, axis=0):
    N = X.shape[axis]

    if issparse(X):
        p = array((X > 0).sum(axis=axis)).flatten() / float(N)
    else:
        p = array(sum(X > 0, axis=axis)).flatten() / float(N)

    p[p == 0] = 10**-12

    return p


def joint_estimator(X, y):
    num_terms = X.shape[1]
    num_classes = y.shape[1]

    if issparse(y):
        N_c = y.sum(axis=0)
    else:
        N_c = sum(y, axis=0)

    p_t_c = 1 * (X > 0).T.dot(y)

    if issparse(p_t_c):
        p_t_c = p_t_c.todense()

    p_nt_c = zeros((num_terms, num_classes))

    for i in xrange(num_terms):
        p_nt_c[i,:] = N_c - p_t_c[i,:]

    tot = array(sum(p_t_c + p_nt_c, axis=1)).flatten()
    p_t_c = p_t_c / tot[:,newaxis]
    p_nt_c = p_nt_c / tot[:,newaxis]

    p_t_c[p_t_c == 0] = 10**-12
    p_nt_c[p_nt_c == 0] = 10**-12

    return p_t_c, p_nt_c


def joint_estimator_point(X, y, smoothing=False):
    counts = X.T.dot(y)

    if issparse(counts):
        counts = array(counts.todense())

    if smoothing:
        counts = add_smoothing(counts)

    return counts/numpy.sum(counts, dtype=numpy.float)


def joint_estimator_full_sparse(X, y, smoothing=False):
    _, t = X.shape
    _, c = y.shape

    X = X.tolil()
    y = y.tolil()

    counts = [zeros((t, c)), zeros((t, c)), zeros((t, c)), zeros((t, c))]

    for t_idx, c_idx in izip(X.rows, y.rows):
        t_mask = zeros(t, dtype=numpy.bool)
        t_mask[t_idx] = True
        c_mask = zeros(c, dtype=numpy.bool)
        c_mask[c_idx] = True

        counts[0][t_mask,c_mask] += 1
        counts[1][t_mask,~c_mask] += 1
        counts[2][~t_mask,c_mask] += 1
        counts[3][~t_mask,~c_mask] += 1

    if smoothing:
        counts = [add_smoothing(m) for m in counts]

    total = numpy.sum([numpy.sum(m) for m in counts], dtype=numpy.float)

    return [m/total for m in counts]


def joint_estimator_full(X, y, smoothing=False):
    if issparse(X) or issparse(y):
        return joint_estimator_full_sparse(X, y, smoothing=smoothing)

    counts = [xx.T.dot(yy) for xx, yy in zip([X, X, 1-X, 1-X], [y, 1-y, y, 1-y])]

    if smoothing:
        counts = [add_smoothing(m) for m in counts]

    total = numpy.sum([numpy.sum(m) for m in counts], dtype=numpy.float)

    return [m/total for m in counts]


def mutual_information(X, y):
    num_terms = X.shape[1]
    num_classes = y.shape[1]

    p_c = indicator_estimator(y)
    p_t = indicator_estimator(X)

    p_t_c = joint_estimator_full(X, y, smoothing=True)

    ig = zeros((num_terms))

    for i in xrange(num_terms):
        for j in xrange(num_classes):
            ig[i] += p_t_c[0][i, j] * log(p_t_c[0][i, j]/(p_t[i]*p_c[j]))
            ig[i] += p_t_c[1][i, j] * log(p_t_c[1][i, j]/(p_t[i]*(1- p_c[j])))
            ig[i] += p_t_c[2][i, j] * log(p_t_c[2][i, j]/((1 - p_t[i])*p_c[j]))
            ig[i] += p_t_c[3][i, j] * log(p_t_c[3][i, j]/((1 - p_t[i])*(1- p_c[j])))

    return ig


def pointwise_mutual_information(X, y, normalize=False):
    p_c = indicator_estimator(y)
    p_t = indicator_estimator(X)

    p_t.shape = 2, 1
    p_c.shape = 1, 2

    p_t_c = joint_estimator_point(X, y, smoothing=True)

    m = numpy.log(array(p_t_c) / (p_t * p_c))

    if normalize:
        m = m / -numpy.log(p_t_c)

    return array(numpy.max(m, axis=1)).flatten()
