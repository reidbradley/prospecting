

import sys
import os
import pickle
import httplib2
import time
from functools import wraps
import pandas as pd
from prospecting.env import (LOG_FILE,
                             LOG_FILE_DEBUG,
                             TMPDIR,
                             DATADIR
                             )
import logging
log = logging.getLogger('prospecting.utils')


log_config_dict = {
    'version': 1,
    'formatters': {
        'simple': {
            'class': 'logging.Formatter',
            'format': '%(name)-12s: %(levelname)-8s %(message)s'
        },
        'default': {
            'class': 'logging.Formatter',
            'format': '%(asctime)s %(name)-20s %(levelname)-8s %(message)s'
        },
        'detailed': {
            'class': 'logging.Formatter',
            'format': '%(asctime)s %(name)-15s %(levelname)-8s %(processName)-10s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'stream': 'ext://sys.stdout',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE,
            'mode': 'a',
            'maxBytes': 1048576,
            'backupCount': 5,
            'formatter': 'default',
        },
        'debug': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_DEBUG,
            'mode': 'a',
            'maxBytes': 1048576,
            'backupCount': 5,
            'formatter': 'detailed',
        },
    },
    'loggers': {
        'prospecting.api': {
            'handlers': ['console', 'file']
        },
        'prospecting.process': {
            'handlers': ['console', 'file']
        },
        'prospecting.model': {
            'handlers': ['console', 'file']
        },
        'prospecting.report': {
            'handlers': ['console', 'file']
        },
        'prospecting.utils': {
            'handlers': ['console', 'file']
        },
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['debug']
    },
}
# nginx
# jupyter notebook


def fn_timer(function):
    @wraps(function)
    def function_timer(*args, **kwargs):
        t0 = time.time()
        result = function(*args, **kwargs)
        t1 = time.time()
        log.info("Total time running {0}: {1} seconds".format(function.func_name, str(t1 - t0)))
        return result
    return function_timer


class parse_log_to_json(object):
    def __init__(self, msg, **kwargs):
        self.msg = msg
        self.kwargs = kwargs

    def __str__(self):
        return '{0} with {1}'.format(self.msg, self.kwargs)


def syspathcheck():
    print(sys.path)
    return


def sysversioncheck():
    print('sys.version: ', sys.version)
    print('sys.version_info: ', sys.version_info)
    print('sys.platform: ', sys.platform)
    return


def enum(*args):
    enums = dict(zip(args, range(len(args))))
    return type('Enum', (), enums)


def print_logfiles():
    logfiles = [f for f in os.listdir(TMPDIR) if '.log' in f]
    for filename in logfiles:
        print(filename)


def download(url):
    h = httplib2.Http()
    resp, content = h.request(url, 'GET')
    return (resp, content)


def pickle_dump(obj, filepath):
    with open(filepath, 'wb') as pckl:
        pickle.dump(obj, pckl, pickle.HIGHEST_PROTOCOL)


def pickle_load(filepath):
    with open(filepath, 'rb') as pckl:
        unpckld = pickle.load(pckl)
    return unpckld


def pckl(obj, nameforfile):
    try:
        n_rows = obj.shape[0]
        n_cols = obj.shape[1]
        pickle_path = os.path.join(DATADIR, (nameforfile + "_" + str(n_rows) + "_" + str(n_cols) + ".p"))
    except:
        pickle_path = os.path.join(DATADIR, (nameforfile + ".p"))
    finally:
        # TODO create new file version if file exists
        if os.path.isfile(pickle_path):
            #os.remove(self.credential_path)
            pass
        obj.to_pickle(pickle_path)
        log.info("Pickled object to: {0}".format(pickle_path))


def unpckl(file, path=DATADIR):
    pickle_path = os.path.join(path, file)
    if os.path.isfile(pickle_path):
        unpickled_object = pd.read_pickle(pickle_path)
        unpickled_object.__name__ = file
    else:
        log.info("Pickle file does not exist, returning None")
        unpickled_object = None
    return (unpickled_object)
