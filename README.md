![prospecting](https://img.shields.io/badge/prospecting-active-lightgrey.svg) ![license](https://img.shields.io/badge/license-MIT-blue.svg)

<!-- 
![docker pulls](https://img.shields.io/docker/pulls/jupyter/base-notebook.svg) ![docker stars](https://img.shields.io/docker/stars/jupyter/base-notebook.svg) [![](https://images.microbadger.com/badges/image/jupyter/base-notebook.svg)](https://microbadger.com/images/jupyter/base-notebook "jupyter/base-notebook image metadata")
-->

# Prospecting analytics environment

Prediction-oriented analytics environment based on [docker-stacks](https://github.com/jupyter/docker-stacks/) ( debian jessie + base + minimal + scipy).

A key characteristic of this project is that it uses Google Sheets to support common ML workflows, basically using Google Sheets as a config file for logic. This project reflects my current toolset and should be considered a first draft/WIP. Check LICENSE.md for permissions.

## Overview

* The project contains:
```
        .
        ├── .dockerignore
        ├── .gitattributes      # For CRLF correction
        ├── .gitignore
        ├── credentials/        # Not necessarily best practice
        │   ├── README.md
        │   └── certs/
        │       └── README.md
        ├── data/
        │   ├── README.md
        │   └── tmp/
        │       ├── README.md
        │       └── joblib/
        │           └── README.md
        ├── Dockerfile
        ├── LICENSE.md
        ├── jupyter_notebook_config.py
        ├── mplimporthook.py
        ├── notebooks/
        ├── prospecting
        │   ├── __init__.py
        │   ├── env.py
        │   ├── utils.py
        │   ├── api.py          # Google Sheets and Google Drive API classes
        │   ├── process.py      # Data cleaning functions
        │   ├── model.py        # TBD
        │   ├── report.py
        │   ├── errors.py
        │   └── version.py
        ├── README.md           # Main README.md
        ├── requirements_nonconda.txt
        ├── scripts
        │   └── hash_jupyter_pw.py
        ├── start-notebook.sh
        ├── start.sh
        └── start-singleuser.sh
```
* Jupyter Notebook 4.3.x
* Conda Python 3.x and Python 2.7.x environments
* pandas, matplotlib, scipy, seaborn, scikit-learn, scikit-image, sympy, cython, patsy, statsmodel, cloudpickle, dill, numba, bokeh, vincent, beautifulsoup, xlrd and more pre-installed (check Dockerfile and `./requirements_nonconda.txt` for full detail)
* Unprivileged user `prspctr` (uid=1000, configurable, see options) in group `users` (gid=100) with ownership over `/home/prspctr` and `/opt/conda`
* [tini](https://github.com/krallin/tini) as the container entrypoint and [start-notebook.sh](../base-notebook/start-notebook.sh) as the default command
* A [start-singleuser.sh](../base-notebook/start-singleuser.sh) script useful for running a single-user instance of the Notebook server, as required by JupyterHub
* A [start.sh](../base-notebook/start.sh) script useful for running alternative commands in the container (e.g. `ipython`, `jupyter kernelgateway`, `jupyter lab`)
* Options for HTTPS, password auth, and passwordless `sudo`

## Basic Use

The following commands are Linux specific (Ubuntu 16.04), will update with Windows examples eventually (reach out if you have questions).

#### Pre-build

- Clone repo to local directory
- To enable integrations with Google API's, get a `client_secret.json` credential file from the Google Developers Console and save it in the `./prospecting/credentials` directory Examples: Step 1 here [sheets](https://developers.google.com/sheets/api/quickstart/python), or [drive](https://developers.google.com/drive/v3/web/quickstart/python)
- Within your Google Cloud Console project, make sure the Sheets and/or Drive APIs are enabled.
- Make sure Docker is installed [Ubuntu](https://docs.docker.com/engine/installation/linux/ubuntu/) | [Windows](https://docs.docker.com/docker-for-windows/)

Set env variable to current date to pass as BUILD_DATE argument when building docker image:
```
TIMESTAMP_RFC3339="$(date --rfc-3339=seconds)"
# format example: 2017-01-18 23:53:17-06:00
```

#### Build
Build the Docker image (this will take awhile). USE_HTTPS flag is 'true' by default. If you want to use HTTPS, don't pass the USE_HTTPS build arg, and place your certificate and key files in `./credentials/certs/` prior to building. Also, if you want any specific Python packages, add them to the Dockerfile or (if managed by pip) add to the `./requirements_nonconda.txt` file.
```
docker build --build-arg BUILD_DATE="$TIMESTAMP_RFC3339" --build-arg USE_HTTPS='false' -t prospecting/notebook:scipy .
```

#### Post-build
Create a data-specific container to persist data to local machine (and _caution_ allow sharing of data between containers _caution_). From the project directory, run the following:
```
docker create -v $PWD/credentials:/home/prspctr/work/prospecting/credentials -v $PWD/data:/home/prspctr/work/prospecting/data -v $PWD/notebooks:/home/prspctr/work/prospecting/notebooks -v $PWD/prospecting:/home/prspctr/work/prospecting/prospecting -v $PWD/scripts:/home/prspctr/work/prospecting/scripts --name data prospecting/notebook:scipy
```


Start a container with the Notebook server listening for HTTP connections on port 8888 with password authentication configured (leave off `--NotebookApp.password=hashedpw` option if you don't want to password protect the notebook).
```
docker run -it -p 8888:8888 --rm --volumes-from data --name scipynbook prospecting/notebook:scipy start-notebook.sh --NotebookApp.password='sha1:Use ./scripts/hash_jupyter_pw.py to create hashed password'
```

## Notebook Options

The Docker container executes a [`start-notebook.sh` script](./start-notebook.sh) script by default. The `start-notebook.sh` script handles the `NB_UID` and `GRANT_SUDO` features documented in the next section, and then executes the `jupyter notebook`.

You can pass [Jupyter command line options](https://jupyter.readthedocs.io/en/latest/projects/jupyter-command.html) through the `start-notebook.sh` script when launching the container. For example, to secure the Notebook server with a password hashed using `IPython.lib.passwd()`, run the following:

For example, to set the base URL of the notebook server, run the following:

```
docker run -d -p 8888:8888 prospecting/notebook:scipy start-notebook.sh --NotebookApp.base_url=/some/path
```

You can sidestep the `start-notebook.sh` script and run your own commands in the container. See the *Alternative Commands* section later in this document for more information.

## Docker Options

You may customize the execution of the Docker container and the command it is running with the following optional arguments.

* `-e PASSWORD="YOURPASS"` - Configures Jupyter Notebook to require the given plain-text password. Should be combined with `USE_HTTPS` on untrusted networks. **Note** that this option is not as secure as passing a pre-hashed password on the command line as shown above.
* `-e USE_HTTPS=yes` - Configures Jupyter Notebook to accept encrypted HTTPS connections. If a `pem` file containing a SSL certificate and key is not provided (see below), the container will generate a self-signed certificate for you.
* `-e NB_UID=1000` - Specify the uid of the `prspctr` user. Useful to mount host volumes with specific file ownership. For this option to take effect, you must run the container with `--user root`. (The `start-notebook.sh` script will `su prspctr` after adjusting the user id.)
* `-e GRANT_SUDO=yes` - Gives the `prspctr` user passwordless `sudo` capability. Useful for installing OS packages. For this option to take effect, you must run the container with `--user root`. (The `start-notebook.sh` script will `su prspctr` after adding `prspctr` to sudoers.) **You should only enable `sudo` if you trust the user or if the container is running on an isolated host.**
* `-v /some/host/folder/for/work:/home/prspctr/work` - Host mounts the default working directory on the host to preserve work even when the container is destroyed and recreated (e.g., during an upgrade).
* `-v /some/host/folder/for/server.pem:/home/prspctr/prospecting/credentials/certs/certkeyfile.pem` - Mounts a SSL certificate plus key for `USE_HTTPS`. Useful if you have a real certificate for the domain under which you are running the Notebook server.

## SSL Certificates

The notebook server configuration in this Docker image expects the `notebook.pem` file mentioned above to contain a base64 encoded SSL key and at least one base64 encoded SSL certificate. The file may contain additional certificates (e.g., intermediate and root certificates).

If you have your key and certificate(s) as separate files, you must concatenate them together into the single expected PEM file. Alternatively, you can build your own configuration and Docker image in which you pass the key and certificate separately.

For additional information about using SSL, see the following:

* The [docker-stacks/examples](https://github.com/jupyter/docker-stacks/tree/master/examples) for information about how to use [Let's Encrypt](https://letsencrypt.org/) certificates when you run these stacks on a publicly visible domain.
* The [jupyter_notebook_config.py](jupyter_notebook_config.py) file for how this Docker image generates a self-signed certificate.
* The [Jupyter Notebook documentation](https://jupyter-notebook.readthedocs.io/en/latest/public_server.html#using-ssl-for-encrypted-communication) for best practices about running a public notebook server in general, most of which are encoded in this image.

## Conda Environment

The default Python 3.x [Conda environment](http://conda.pydata.org/docs/using/envs.html) resides in `/opt/conda`. The commands `ipython`, `python`, `pip`, `easy_install`, and `conda` (among others) are available in this environment.

## Alternative Commands

### start-singleuser.sh

[JupyterHub](https://jupyterhub.readthedocs.io) requires a single-user instance of the Jupyter Notebook server per user.   To use this stack with JupyterHub and [DockerSpawner](https://github.com/jupyter/dockerspawner), you must specify the container image name and override the default container run command in your `jupyterhub_config.py`:

```python
# Spawn user containers from this image
c.DockerSpawner.container_image = 'prospecting/notebook:scipy'
# Have the Spawner override the Docker run command
c.DockerSpawner.extra_create_kwargs.update({
        'command': '/usr/local/bin/start-singleuser.sh'
})
```

### start.sh

The `start.sh` script supports the same features as the default `start-notebook.sh` script (e.g., `GRANT_SUDO`), but allows you to specify an arbitrary command to execute. For example, to run the text-based `ipython` console in a container, do the following:

```
docker run -it --rm prospecting/notebook:scipy start.sh ipython
```

This script is particularly useful when you derive a new Dockerfile from this image and install additional Jupyter applications with subcommands like `jupyter console`, `jupyter kernelgateway`, and `jupyter lab`.

### Others

You can bypass the provided scripts and specify your an arbitrary start command. If you do, keep in mind that certain features documented above will not function (e.g., `GRANT_SUDO`).