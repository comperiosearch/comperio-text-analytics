from itertools import izip

import numpy
from numpy import array, sum, zeros
from scipy.sparse import issparse


def add_smoothing(m, amount=10 ** -12):
    m = m.astype(numpy.float)
    m[m == 0] = amount

    return m


def marginal_estimator(X, axis=0, smoothing=False):
    N = X.shape[axis]

    if issparse(X):
        counts = array((X > 0).sum(axis=axis))
    else:
        counts = array(sum(X > 0, axis=axis))

    if smoothing:
        add_smoothing(counts)

    p = counts.flatten() / float(N)

    return p


def joint_estimator_point(X, y, smoothing=False):
    counts = X.T.dot(y)

    if issparse(counts):
        counts = array(counts.todense())

    if smoothing:
        counts = add_smoothing(counts)

    return counts / numpy.sum(counts, dtype=numpy.float)


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

        counts[0][t_mask, c_mask] += 1
        counts[1][t_mask, ~c_mask] += 1
        counts[2][~t_mask, c_mask] += 1
        counts[3][~t_mask, ~c_mask] += 1

    if smoothing:
        counts = [add_smoothing(m) for m in counts]

    total = numpy.sum([numpy.sum(m) for m in counts], dtype=numpy.float)

    return [m / total for m in counts]


def joint_estimator_full(X, y, smoothing=False):
    if issparse(X) or issparse(y):
        return joint_estimator_full_sparse(X, y, smoothing=smoothing)

    counts = [xx.T.dot(yy) for xx, yy in zip([X, X, 1 - X, 1 - X], [y, 1 - y, y, 1 - y])]

    if smoothing:
        counts = [add_smoothing(m) for m in counts]

    total = numpy.sum([numpy.sum(m) for m in counts], dtype=numpy.float)

    return [m / total for m in counts]