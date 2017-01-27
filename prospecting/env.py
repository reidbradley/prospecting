
import os

PROJECTNAME = os.environ['PROJECTNAME']
PROJECTDIR = os.environ['PROJECTDIR']
CODEDIR = os.environ['CODEDIR']
NOTEBOOKDIR = os.environ['NOTEBOOKDIR']
CREDSDIR = os.environ['CREDSDIR']
DATADIR = os.environ['DATADIR']

CLIENT_SECRET_FILE = 'client_secret.json'
SOURCE_FILE = 'data.csv'
SOURCE_CSV = os.path.join(DATADIR, SOURCE_FILE)

NOAUTH_LOCAL_WEBSERVER = True

TMPDIR = os.environ['TMPDIR']
LOG_FILENAME = 'prospecting.log'
LOG_FILENAME_DEBUG = 'debug.log'
LOG_FILE = os.path.join(TMPDIR, LOG_FILENAME)
LOG_FILE_DEBUG = os.path.join(TMPDIR, LOG_FILENAME_DEBUG)
