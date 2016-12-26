#!/usr/bin/env python
# -*- coding: utf-8 -*-


from sklearn.base import BaseEstimator, TransformerMixin
class ItemSelector(BaseEstimator, TransformerMixin):
    #__module__ = os.path.splitext(os.path.basename(__file__))[0]
    def __init__(self, key):
        self.key = key

    def fit(self, x, y=None):
        return self

    def transform(self, data_dict):
        return data_dict[self.key]
    
class Scalers(BaseEstimator, TransformerMixin):
    #__module__ = os.path.splitext(os.path.basename(__file__))[0]
    def __init__(self):
        self

    def fit(self, X, y=None):
        return self

    def transform(self,X):
        return X.reshape(-1,1)
