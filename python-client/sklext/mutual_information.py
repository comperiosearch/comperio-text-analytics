from math import log

from numpy import array, sum, zeros, newaxis
from scipy.sparse import issparse


def indicator_estimator(X, axis=0):
    N = X.shape[axis]

    if issparse(X):
        p = array((X > 0).sum(axis=axis)).flatten() / float(N)
    else:
        p = array(sum(X > 0, axis=axis)).flatten() / float(N)

    return p


def mutual_information(X, y):
    num_terms = X.shape[1]
    num_classes = y.shape[1]

    p_c = indicator_estimator(y)
    p_t = indicator_estimator(X)

    if issparse(y):
        N_c = y.sum(axis=0)
    else:
        N_c = sum(y, axis=0)

    p_nt_c = zeros((num_terms, num_classes))

    p_t_c = 1*(X > 0).T.dot(y)

    if issparse(p_t_c):
        p_t_c = p_t_c.todense()

    for i in xrange(num_terms):
        p_nt_c[i,:] = N_c - p_t_c[i,:]

    tot = array(sum(p_t_c + p_nt_c, axis=1)).flatten()
    p_t_c = p_t_c / tot[:,newaxis]
    p_nt_c = p_nt_c / tot[:,newaxis]

    ig = zeros((num_terms))

    for i in xrange(num_terms):
        for j in xrange(num_classes):
            if (p_t[i]*p_c[j]) > 0 and p_t_c[i, j] > 0:
                ig[i] += p_t_c[i, j] * log(p_t_c[i, j]/(p_t[i]*p_c[j]))
            if (1 - (p_t[i])*p_c[j]) > 0 and p_nt_c[i, j] > 0:
                ig[i] += p_nt_c[i, j] * log(p_nt_c[i, j]/((1 - p_t[i])*p_c[j]))

    return ig

