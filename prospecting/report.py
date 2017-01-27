

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab

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
