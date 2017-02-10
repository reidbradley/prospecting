
import os
import time
from collections import OrderedDict
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
from matplotlib.backends.backend_pdf import PdfPages

# report
from sklearn.metrics import confusion_matrix          # (y_true, y_pred[, ...])
#from sklearn.metrics import classification_report     # (y_true, y_pred)
from sklearn.metrics import precision_score           # (y_true, y_pred[, ...])
from sklearn.metrics import recall_score              # (y_true, y_pred[, ...])
from sklearn.metrics import accuracy_score            # (y_true, y_pred[, ...])
from sklearn.metrics import f1_score                  # (y_true, y_pred[, labels, ...])
from sklearn.metrics import roc_auc_score             # (y_true, y_score[, ...])
#from sklearn.metrics import auc                       # (x, y[, reorder])
#from sklearn.metrics import roc_curve                 # (y_true, y_score[, ...])

import logging
log = logging.getLogger('prospecting.report')


def create_description(dataframe):
    log.info('Creating description for {0}'.format(dataframe.__name__))
    tmp_df = pd.DataFrame(dataframe.describe(include='all').transpose())
    # --------------
    # create column for 'column_name' and reset index
    if 'column_name' not in tmp_df.columns:
        tmp_df.insert(0, 'column_name', tmp_df.index)
        tmp_df.reset_index(drop=True, inplace=True)
        log.info('Success! "column_name" added to description at column position [0]')
    else:
        log.info('Column_name has already been added')
    # --------------
    # create column for dtype
    if 'dtype' not in tmp_df.columns:
        tmp_df.insert(1, 'dtype',
                      [str(dataframe[col].dtype)for col in tmp_df['column_name']]
                      )
        log.info('Success! "dtype" added to description at column position [1]')
    else:
        log.info('Column "dtype" has already been added')
    # --------------
    # add 'missing_count' column
    if 'missing_count' not in tmp_df.columns:
        tmp_df.insert(2, 'missing_count',
                      #[str(dataframe.shape[0]-dataframe[col].count()) for col in tmp_df['column_name']]
                      [(dataframe.shape[0] - dataframe[col].count()) for col in tmp_df['column_name']]
                      )
        log.info('Success! "missing_count" added to description at column position [4]')
    else:
        log.info('Column "missing_count" has already been added')

    for col in tmp_df.columns:
        tmp_df[col] = tmp_df[col].astype(str)

    log.info('Description created for {0}'.format(dataframe.__name__))
    return tmp_df


def plot_distribution(x, num_bins=20, normed=1, log=False):
    mu = x.mean()
    sigma = x.std()
    fig, ax = plt.subplots()
    n, bins, patches = ax.hist(x, num_bins, normed=normed, log=log)
    y = mlab.normpdf(bins, mu, sigma)
    ax.plot(bins, y, '-')
    ax.set_xlabel(x.name)
    ax.set_ylabel('Probability density')
    ax.set_title('Histogram of ' + x.name + ':\n$\mu=' + str(mu) + '$, $\sigma=' + str(sigma) + '$')
    fig.tight_layout()
    plt.show()


def boxplot(x, labels=None):
    fig, ax = plt.subplots()
    ax.boxplot(x, labels=labels, showmeans=True, meanline=True)
    ax.set_title('showmeans=True,\nmeanline=True')
    fig.tight_layout()
    plt.show()


def cv_results_to_df(modelsession, gsclf):
    df_cv_results = pd.DataFrame.from_dict(gsclf.cv_results_)
    objectcols = df_cv_results.select_dtypes(include=['object']).columns
    df_cv_results[objectcols] = df_cv_results.select_dtypes(include=['object']).astype('str')
    col_list = [col for col in df_cv_results.columns.tolist() if not col.startswith('param_')]
    rank_score = [col for col in col_list if col.startswith('rank_test')]
    params_col = [col for col in col_list if col.startswith('params')]
    fit_time_cols = [col for col in col_list if col.endswith('fit_time')]
    score_time_cols = [col for col in col_list if col.endswith('score_time')]
    train_score_cols = [col for col in col_list if not col.startswith('split') and
                        not col.startswith('rank') and
                        col.endswith('train_score')]
    test_score_cols = [col for col in col_list if not col.startswith('split') and
                       not col.startswith('rank') and
                       col.endswith('test_score')]
    split_cols = [col for col in col_list if col.startswith('split')]
    column_order = (rank_score +
                    params_col +
                    fit_time_cols +
                    score_time_cols +
                    train_score_cols +
                    test_score_cols +
                    split_cols
                    )
    df_cv_results = df_cv_results[column_order]
    df_cv_results.insert(0, 'session_id', modelsession.session_id)
    df_cv_results.insert(1, 'timestamp', gsclf.model_start_time)
    df_cv_results.insert(8, 'scoring_type', gsclf.score_type)
    return (df_cv_results)


def add_cv_results_to_ss(modelsession, gsclf):
    df_cv_results = cv_results_to_df(modelsession, gsclf)
    if hasattr(modelsession.ss.sheets['cv_results'], 'columns'):
        log.info('Appending df_cv_results to cv_results tab in spreadsheet.')
        modelsession.ss.append(df_cv_results, 'cv_results')
    else:
        log.info('Updating cv_results tab in spreadsheet with df_cv_results.')
        modelsession.ss.update(df_cv_results, 'cv_results')


def session_report(modelsession, clf, ytrue, ypred, yprobs):
    report_start_timestamp = time.time()
    y_true_count = ytrue.sum()
    y_pred_count = ypred.sum()
    tpr, fpr, fnr, tnr = confusion_matrix(ytrue, ypred).flatten()
    rocauc_score = roc_auc_score(ytrue, yprobs)
    acc_score = accuracy_score(ytrue, ypred)
    prec_score = precision_score(ytrue, ypred)
    rec_score = recall_score(ytrue, ypred)
    f1 = f1_score(ytrue, ypred)
    if not hasattr(clf, "score_type"):
        clf.score_type = "N/A"
    if hasattr(clf, "best_estimator_"):
        pipe_steps = {i: (t) for i, t in enumerate([(t[0], type(t[1])) for t in clf.best_estimator_.steps])}
        pipeline = "_".join([pipe_steps[step][0] for step in pipe_steps])
        best_score = "{:0.4f}".format(clf.best_score_)
        best_params_full = {str(param_k): str(param_v) for param_k, param_v in sorted(clf.best_estimator_.get_params().items())}
        tunedparams = clf.tunedparams
        best_parameters = {str(param_name): str(best_params_full[param_name]) for param_name in sorted(tunedparams.keys())}
    else:
        pipe_steps = None
        pipeline = [name for name, model in modelsession.lookup_model_types.items() if model == str(type(clf))][0]
        best_score = None
        best_params_full = clf.get_params()
        best_parameters = None

    sessionreport = [('session_id', [modelsession.session_id]),
                     ('timestamp', [clf.model_start_time]),
                     ('dataset', [modelsession.dataset_name]),
                     ('n_rows', [modelsession.dataset.shape[0]]),
                     ('n_cols', [modelsession.dataset.shape[1]]),
                     ('test_size', [modelsession.test_size]),
                     ('X_train_shape', [str(modelsession.X_train.shape)]),
                     ('X_test_shape', [str(modelsession.X_test.shape)]),
                     ('y_train_shape', [str(modelsession.y_train.shape)]),
                     ('y_test_shape', [str(modelsession.y_test.shape)]),
                     ('fit_time', [((clf.end_time - clf.fit_start_time) / 60)]),
                     ('training_set', [(clf.training_set)]),
                     ('pipeline', [(pipeline)]),
                     ('y_true_count', [y_true_count]),
                     ('y_pred_count', [y_pred_count]),
                     ('tpr', [tpr]),
                     ('fpr', [fpr]),
                     ('fnr', [fnr]),
                     ('tnr', [tnr]),
                     ('roc_auc_score', [rocauc_score]),
                     ('accuracy_score', [acc_score]),
                     ('precision_score', [prec_score]),
                     ('recall_score', [rec_score]),
                     ('f1_score', [f1]),
                     ('scoring_type', [clf.score_type]),
                     ('best_score', [float(best_score)]),
                     ('best_params_tuned', [str(best_parameters)]),
                     ('best_params_all', [str(best_params_full)]),
                     ('pipe_steps', [str(pipe_steps)]),
                     ]
    df_session_report = pd.DataFrame.from_dict(OrderedDict(sessionreport))
    modelsession.ss.append(df_session_report, 'session_report')
    log.info("Report complete in {0} seconds".format((time.time() - report_start_timestamp)))
    return(df_session_report)


def plot_pca_expvar_to_pdf(modelsession, directory, filename='pca_explained_variance.pdf'):
    # pass in list of pca's, as well as dataset name so modelsession is not required
    log.info('Creating PDF of PCA explained variance plots...')
    file_path = os.path.join(directory, filename)
    pp = PdfPages(file_path)
    plot_pca_expvar(modelsession.pca, modelsession.dataset_name, expvar=1, ratio=1)
    plot_pca_expvar(modelsession.pca_std, modelsession.dataset_name, expvar=1, ratio=1)
    plot_pca_expvar(modelsession.pca_mms, modelsession.dataset_name, expvar=1, ratio=1)
    pp.savefig()
    plt.close()
    plot_pca_expvar(modelsession.pca, modelsession.dataset_name, expvar=1, ratio=0)
    plot_pca_expvar(modelsession.pca_std, modelsession.dataset_name, expvar=1, ratio=0)
    plot_pca_expvar(modelsession.pca_mms, modelsession.dataset_name, expvar=1, ratio=0)
    pp.savefig()
    plt.close()
    plot_pca_expvar(modelsession.pca, modelsession.dataset_name, expvar=0, ratio=1)
    plot_pca_expvar(modelsession.pca_std, modelsession.dataset_name, expvar=0, ratio=1)
    plot_pca_expvar(modelsession.pca_mms, modelsession.dataset_name, expvar=0, ratio=1)
    pp.savefig()
    plt.close()
    pp.close()
    log.info('PDF saved to: {0}'.format(file_path))


def plot_pca_expvar(pca, dataset, expvar=1, ratio=1):
    dataset_name = os.path.splitext(os.path.basename(dataset))[0]
    with plt.style.context('ggplot'):
        if expvar is 1 and ratio is 1:
            plt.figure(1, figsize=(10, 6))
            plt.plot(pca.explained_variance_, linewidth=2, label=str(pca.train_set))
            plt.plot(pca.explained_variance_ratio_.cumsum() * 100, linewidth=1, label=(str(pca.train_set)) + " cume")
            plt.suptitle('PCA Explained Variance', fontsize=18)
            plt.title('Dataset: ' + (str(dataset_name)), y=1.01, fontsize=10, loc='right')
            plt.ylabel('Explained variance')
            plt.xlabel('Principal Components')
            plt.legend(loc='best')
            plt.tight_layout(rect=[0, 0, 1, 0.95])
        elif expvar is 1:
            plt.figure(1, figsize=(10, 6))
            plt.plot(pca.explained_variance_, linewidth=2, label=str(pca.train_set))
            plt.suptitle('pca.explained_variance_', fontsize=18)
            plt.title('Dataset: ' + (str(dataset_name)), y=1.01, fontsize=10, loc='right')
            plt.ylabel('Explained variance')
            plt.xlabel('Principal Components')
            plt.legend(loc='best')
            plt.tight_layout(rect=[0, 0, 1, 0.95])
        elif ratio is 1:
            plt.figure(1, figsize=(10, 6))
            plt.plot(pca.explained_variance_ratio_.cumsum() * 100, linewidth=1, label=(str(pca.train_set)) + " cume")
            plt.suptitle('pca.explained_variance_ratio_.cumsum()*100', fontsize=18)
            plt.title('Dataset: ' + (str(dataset_name)), y=1.01, fontsize=10, loc='right')
            plt.ylabel('Explained variance Ratio')
            plt.xlabel('Principal Components')
            plt.legend(loc='best')
            plt.tight_layout(rect=[0, 0, 1, 0.95])
        else:
            log.warning("Neither expvar or ratio were set. No PCA plot created.")
