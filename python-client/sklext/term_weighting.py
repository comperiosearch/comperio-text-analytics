from scipy.sparse import spdiags
from sklearn.base import BaseEstimator, TransformerMixin

from sklext.mutual_information import mutual_information


class TermWeightTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, method='mi'):
        self.method = method
        self._weights = None

    def fit(self, X, y):
        self._weights = mutual_information(X, y)

        return self

    def transform(self, X, y=None):
        p = len(self._weights)
        w_diag = spdiags(self._weights, 0, p, p)

        return X * w_diag