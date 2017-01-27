# Copyright (c) Jupyter Development Team.
# Modified by Reid Bradley
#from jupyter_core.paths import jupyter_data_dir
import subprocess
import os
import errno
import stat

CERT_FILE = os.path.join(os.getenv('CERTSDIR'), 'fullchain.pem')
KEY_FILE = os.path.join(os.getenv('CERTSDIR'), 'privkey.pem')
CERT_PLUS_KEY_FILE = os.path.join(os.getenv('CERTSDIR'), 'notebook.pem')

c = get_config()
c.NotebookApp.ip = '*'
c.NotebookApp.port = 8888
c.NotebookApp.open_browser = False

# Set a certificate if USE_HTTPS is set to any value
if 'USE_HTTPS' in os.environ:
    if os.environ['USE_HTTPS'] in 'true':
        CERT_AND_KEY_FILES_EXIST = (os.path.isfile(CERT_FILE) and os.path.isfile(KEY_FILE))
        if CERT_AND_KEY_FILES_EXIST:
            c.NotebookApp.certfile = CERT_FILE
            c.NotebookApp.keyfile = KEY_FILE
        else:
            if not os.path.isfile(CERT_PLUS_KEY_FILE):
                # Ensure PEM_FILE directory exists
                dir_name = os.path.dirname(CERT_PLUS_KEY_FILE)
                try:
                    os.makedirs(dir_name)
                except OSError as exc:  # Python >2.5
                    if exc.errno == errno.EEXIST and os.path.isdir(dir_name):
                        pass
                    else:
                        raise
                # Generate a certificate if one doesn't exist on disk
                subprocess.check_call([
                    'openssl', 'req', '-new',
                    '-newkey', 'rsa:2048', '-days', '365', '-nodes', '-x509',
                    '-subj', '/C=XX/ST=XX/L=XX/O=generated/CN=generated',
                    '-keyout', CERT_PLUS_KEY_FILE, '-out', CERT_PLUS_KEY_FILE])
                # Restrict access to PEM_FILE
                os.chmod(CERT_PLUS_KEY_FILE, stat.S_IRUSR | stat.S_IWUSR)
                c.NotebookApp.certfile = CERT_PLUS_KEY_FILE
            else:
                c.NotebookApp.certfile = CERT_PLUS_KEY_FILE

# Set a password if PASSWORD is set
if 'PASSWORD' in os.environ:
    from IPython.lib import passwd
    c.NotebookApp.password = passwd(os.environ['PASSWORD'])
    del os.environ['PASSWORD']
