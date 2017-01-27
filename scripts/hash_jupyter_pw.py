#! /usr/bin/env python

from notebook.auth import passwd
from notebook.auth.security import passwd_check
from getpass import getpass
try:
    import argparse
    argparse_imported = 1
except Exception:
    import sys
    argparse_imported = 0


def main(argv):
    if argparse_imported == 0:
        if len(argv) == 1:
            pw = passwd(argv[0])
        elif len(argv) == 2:
            pw = passwd(argv[0], argv[1])
        else:
            print("incorrect number of args provided")
            return
    else:
        pw = passwd(argv.p, argv.a)
        if not passwd_check(pw, getpass("Please re-enter your password:")):
            print("Passwords do not match. Please try again.")
            return

    print("\nNew hashed password:\n\n  ", pw)
    print(
        "\n--------------------\
        \nUse the new hashed password when running the prospecting docker image\
        \n\nEXAMPLE:\
        \n  sudo docker run -it -p 8888:8888 --rm --volumes-from nameofvolume \
        \n  --name nameofcontainer nameofdockerimage start-notebook.sh\
        \n  --NotebookApp.password='" + pw + "' \
        \n\nOr, add NotebookApp.password='" + pw + "'\
        \nto jupyter_notebook_config.py file prior to building docker image from base-notebook.\n"
    )
    return


if __name__ == '__main__':
    if argparse_imported:
        args_parser = argparse.ArgumentParser(
            description='receive api, scope, and (sheet id OR query)',
            formatter_class=argparse.RawDescriptionHelpFormatter)
        args_parser.add_argument(
            '--p',
            '--password',
            #required=True,
            default=getpass("Please enter a strong password:"),
            action='store',
            help='Password to hash')
        args_parser.add_argument(
            '--a',
            '--algorithm',
            required=False,
            default='sha1',
            action='store',
            help='Hashing algorithm to use (e.g, "sha1" or any argument supported by `hashlib.new`)')
        args = args_parser.parse_args()
        main(args)
    else:
        print('running else...')
        if len(sys.argv) == 3:
            password = sys.argv[1]
            algorithm = sys.argv[2]
            main([password, algorithm])
        elif len(sys.argv) == 2:
            password = sys.argv[1]
            main([password])
        else:
            print("please provide a password with optional algorithm (ex. 'sha1' or any supported by `hashlib.new`)")
