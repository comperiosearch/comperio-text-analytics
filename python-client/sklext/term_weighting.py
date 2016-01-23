from scipy.sparse import spdiags
from sklearn.base import BaseEstimator, TransformerMixin

from sklext.mutual_information import mutual_information, pointwise_mutual_information


class TermWeightTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, method='mi'):
        self.method = method
        self._weights = None

    def fit(self, X, y):
        if self.method is 'mi':
            self._weights = mutual_information(X, y)
        elif self.method is 'pmi':
            self._weights = pointwise_mutual_information(X, y, normalize=False)
        elif self.method is 'npmi':
            self._weights = pointwise_mutual_information(X, y, normalize=True)

        return self

    def transform(self, X, y=None):
        p = len(self._weights)
        w_diag = spdiags(self._weights, 0, p, p)

        return X * w_diag
