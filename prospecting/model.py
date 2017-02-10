
import os
import uuid
import time

#import numpy as np
import pandas as pd
from prospecting import (utils, report)

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler  # normal distribution
from sklearn.preprocessing import MinMaxScaler  # scales data to [0, 1]
#from sklearn.preprocessing import MaxAbsScaler  # scales data to [-1, 1]; for data already centered at zero, or sparse data
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV

from sklearn.metrics import confusion_matrix

import logging
log = logging.getLogger('prospecting.model')


class ModelSession:

    def __init__(self, dataset, testsize=0.3, randstate=0, stdscaler=True, mmscaler=True, pcasets=True):
        """Initialize ModelSession class

        Args:
            dataset (list):  List of strings representing which X training set to use (named train set must exist as part of an initialized ModelSession class), ex: ['X_train', 'X_train_std']
            testsize (float): Percentage of dataset to use for value of test_size in train_test_split
            randstate (int):   Random state to use
            stdscaler (bool):   Flag to control if StandardScaler() training set should be fit
            mmscaler (bool):   Flag to control if MinMaxScaler() training set should be fit
            pcasets (bool):   Flag to control if PCA() sets should be created

        """
        self.session_id = generate_session_id()
        self.dataset_name = os.path.splitext(os.path.basename(dataset))[0]
        self.dataset = utils.unpckl(os.path.basename(dataset))
        self.X = self.dataset.iloc[:, 1:].values
        self.y = self.dataset.iloc[:, 0].values
        self.test_size = testsize
        self.rand_state = randstate
        self.stdscaler = stdscaler
        self.mmscaler = mmscaler
        self.pcasets = pcasets
        self.splits()
        if self.stdscaler is True:
            self.std_scaler()
        if self.mmscaler is True:
            self.minmax_scaler()
        if self.pcasets is True:
            self.pca_sets()

    def splits(self):
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(self.X,
                                                                                self.y,
                                                                                test_size=self.test_size,
                                                                                random_state=self.rand_state)

    def std_scaler(self):
        stdsc = StandardScaler()
        self.X_train_std = stdsc.fit_transform(self.X_train)
        self.X_test_std = stdsc.fit(self.X_test)

    def minmax_scaler(self):
        mms = MinMaxScaler()
        self.X_train_mms = mms.fit_transform(self.X_train)
        self.X_test_mms = mms.fit(self.X_test)

    def pca_sets(self):
        self.pca = PCA()
        self.pca.train_set = 'X_train'
        self.pca.fit(self.X_train)
        self.X_pca = self.pca.transform(self.X_train)
        if self.stdscaler is True:
            self.pca_std = PCA()
            self.pca_std.train_set = 'X_train_std'
            self.pca_std.fit(self.X_train_std)
            self.X_pca_std = self.pca_std.transform(self.X_train_std)
        if self.mmscaler is True:
            self.pca_mms = PCA()
            self.pca_mms.train_set = 'X_train_mms'
            self.pca_mms.fit(self.X_train_mms)
            self.X_pca_mms = self.pca_mms.transform(self.X_train_mms)

#-------------------------


def generate_session_id():
    return (uuid.uuid4().hex)


def grid_search(modelsession, modelconfig):
    for config in modelconfig:
        for ds in config['datasets']:
            if hasattr(modelsession, ds):
                timestamp = time.time()
                xtrain = getattr(modelsession, ds)
                ytrain = modelsession.y_train
                pipesteps = config['pipesteps']
                params = config['params']
                scoring = getattr(config, 'scoring', 'roc_auc')
                njobs = getattr(config, 'n_jobs', 3)
                clfpipeline = Pipeline(pipesteps)
                gs = GridSearchCV(clfpipeline, param_grid=params, scoring=scoring, n_jobs=njobs, verbose=1)
                gs.model_start_time = timestamp
                gs.fit_start_time = time.time()
                gs.fit(xtrain, ytrain)
                gs.end_time = time.time()
                gs.tunedparams = params
                gs.score_type = scoring
                gs.training_set = ds
                report.add_cv_results_to_ss(modelsession, gs)

                gs_y_pred = gs.predict(modelsession.X_test)
                if hasattr(gs, "predict_proba"):
                    gs_y_proba = gs.predict_proba(modelsession.X_test)[:, 1]
                else:
                    gs_y_proba = gs.decision_function(modelsession.X_test)
                log.info('Confusion matrix:\n{0}'.format(confusion_matrix(modelsession.y_test, gs_y_pred)))
                report.session_report(modelsession, gs, modelsession.y_test, gs_y_pred, gs_y_proba)
