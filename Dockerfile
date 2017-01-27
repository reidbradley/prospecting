# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
# Modified by Reid Bradley

# Debian Jessie image released 2016 May 03.
FROM debian@sha256:32a225e412babcd54c0ea777846183c61003d125278882873fb2bc97f9057c51

MAINTAINER Reid Bradley

USER root

# Install all OS dependencies for notebook server that starts but lacks all
# features (e.g., download as all possible file formats)
ENV DEBIAN_FRONTEND noninteractive
RUN REPO=http://cdn-fastly.deb.debian.org \
 && echo "deb $REPO/debian jessie main\ndeb $REPO/debian-security jessie/updates main" > /etc/apt/sources.list \
 && apt-get update && apt-get -yq dist-upgrade \
 && apt-get install -yq --no-install-recommends \
    wget \
    curl \
    bzip2 \
    apt-transport-https \
    ca-certificates \
    sudo \
    locales \
    git \
    vim \
    jed \
    emacs \
    build-essential \
    python-dev \
    unzip \
    libsm6 \
    pandoc \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-extra \
    texlive-fonts-recommended \
    texlive-generic-recommended \
    libxrender1 \
    inkscape \
    libav-tools \
    tree \
    lsb-release \
 #&& apt-get clean \
 && apt-get autoclean \
 && apt-get autoremove \
 && rm -rf /var/lib/apt/lists/*

RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen

# Install Tini
ENV TINI_VERSION v0.13.2
RUN wget --quiet https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini && \
    echo "790c9eb6e8a382fdcb1d451f77328f1fac122268fa6f735d2a9f1b1670ad74e3 *tini" | sha256sum -c - && \
    mv tini /usr/local/bin/tini && \
    chmod +x /usr/local/bin/tini

ENV CONDA_DIR /opt/conda
ENV PATH $CONDA_DIR/bin:$PATH
ENV SHELL /bin/bash
ENV NB_USER prspctr
ENV NB_UID 1000
ENV HOME /home/$NB_USER
ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

# Configure environment
#ENV CONDA_DIR="/opt/conda" PATH="$CONDA_DIR/bin:$PATH" SHELL="/bin/bash" NB_USER="prspctr" NB_UID="1000" HOME="/home/$NB_USER" LC_ALL="en_US.UTF-8" LANG="en_US.UTF-8" LANGUAGE="en_US.UTF-8"


# ##############################
# prospecting  - section 1/3
# ------------------------------
ARG BUILD_DATE
ARG USE_HTTPS
ARG USERSUDOPW
# USERSUDOPW arg is passed as user pw when adding user to sudo; check prospecting section 3/3

ENV BUILD_DATE ${BUILD_DATE:-"none set"}
ENV USE_HTTPS ${USE_HTTPS:-'true'}
ENV PROJECTNAME prospecting
ENV PROJECTDIR /home/$NB_USER/work/prospecting
ENV CODEDIR $PROJECTDIR/prospecting
ENV NOTEBOOKDIR $PROJECTDIR/notebooks
ENV CREDSDIR $PROJECTDIR/credentials
ENV CERTSDIR $CREDSDIR/certs
ENV DATADIR $PROJECTDIR/data
ENV TMPDIR $DATADIR/tmp
ENV SCRIPTSDIR $PROJECTDIR/scripts
ENV PYTHONPATH $PROJECTDIR
ENV JOBLIB_TEMP_FOLDER $TMPDIR/joblib
#ENV GRANT_SUDO 'true'

#ENV BUILD_DATE=${BUILD_DATE:-"none set"} \
#    PROJECTNAME=prospecting \
#    PROJECTDIR=/home/$NB_USER/work/prospecting \
#    CODEDIR=$PROJECTDIR/prospecting \
#    NOTEBOOKDIR=$PROJECTDIR/notebooks \
#    CREDSDIR=$PROJECTDIR/credentials \
#    CERTSDIR=$CREDSDIR/certs \
#    DATADIR=$PROJECTDIR/data \
#    TMPDIR=$DATADIR/tmp \
#    SCRIPTSDIR=$PROJECTDIR/scripts \
#    PYTHONPATH=$PROJECTDIR

#ENV BUILD_DATE="${BUILD_DATE:-'none set'}" PROJECTNAME="prospecting" PROJECTDIR="/home/$NB_USER/work/prospecting" CODEDIR="$PROJECTDIR/prospecting" NOTEBOOKDIR="$PROJECTDIR/notebooks" CREDSDIR="$PROJECTDIR/credentials" CERTSDIR="$CREDSDIR/certs" DATADIR="$PROJECTDIR/data" TMPDIR="$DATADIR/tmp" SCRIPTSDIR="$PROJECTDIR/scripts" PYTHONPATH="$PROJECTDIR"

LABEL org.label-schema.schema-version = "1.0" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="prospecting" \
      org.label-schema.description="Customized jupyter/docker-stacks/base-notebook" \
      org.label-schema.vcs-url="https://github.com/reidbradley/prospecting" \
      org.label-schema.docker.cmd="docker create \
                                   -v $PWD/credentials:/home/prspctr/work/prospecting/credentials \
                                   -v $PWD/data:/home/prspctr/work/prospecting/data \
                                   -v $PWD/notebooks:/home/prspctr/work/prospecting/notebooks \
                                   -v $PWD/prospecting:/home/prspctr/work/prospecting/prospecting \
                                   -v $PWD/scripts:/home/prspctr/work/prospecting/scripts \
                                   --name data \
                                   prospecting/notebook:scipy && \
                                   docker run -it -p 8888:8888 --rm \
                                   --volumes-from data \
                                   --name scipynbook prospecting/notebook:scipy start-notebook.sh \
                                   --NotebookApp.password='sha1:use ./scripts/hash_jupyter_pw.py to get hashed pw'" \
    org.label-schema.docker.cmd.devel="docker exec -it scipynbook bash"

RUN export CLOUD_SDK_REPO="cloud-sdk-$(lsb_release -c -s)" && \
    echo "deb https://packages.cloud.google.com/apt $CLOUD_SDK_REPO main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add - && \
    sudo apt-get update && sudo apt-get install google-cloud-sdk -yq && \
    apt-get autoclean && apt-get autoremove
# ##############################


# Create prspctr user with UID=1000 and in the 'users' group
RUN useradd -m -s /bin/bash -N -u $NB_UID $NB_USER && \
    mkdir -p $CONDA_DIR && \
    chown $NB_USER $CONDA_DIR

USER $NB_USER

# Install conda as prspctr
RUN cd /tmp && \
    mkdir -p $CONDA_DIR && \
    wget --quiet https://repo.continuum.io/miniconda/Miniconda3-4.2.12-Linux-x86_64.sh && \
    echo "d0c7c71cc5659e54ab51f2005a8d96f3 *Miniconda3-4.2.12-Linux-x86_64.sh" | md5sum -c - && \
    /bin/bash Miniconda3-4.2.12-Linux-x86_64.sh -f -b -p $CONDA_DIR && \
    rm Miniconda3-4.2.12-Linux-x86_64.sh && \
    $CONDA_DIR/bin/conda install --quiet --yes conda==4.2.12 && \
    $CONDA_DIR/bin/conda config --system --add channels conda-forge && \
    $CONDA_DIR/bin/conda config --system --set auto_update_conda false && \
    conda clean -tipsy

# Temporary workaround for https://github.com/jupyter/docker-stacks/issues/210
# Stick with jpeg 8 to avoid problems with R packages
RUN echo "jpeg 8*" >> /opt/conda/conda-meta/pinned

# Install Python 3 packages
# Remove pyqt and qt pulled in for matplotlib since we're only ever going to
# use notebook-friendly backends in these images
RUN conda install --quiet --yes \
    'nomkl' \
    'ipywidgets=5.2*' \
    'pandas=0.19*' \
    'numexpr=2.6*' \
    'matplotlib=1.5*' \
    'scipy=0.18.*' \
    'seaborn=0.7*' \
    'scikit-learn=0.18*' \
    'scikit-image=0.11*' \
    'sympy=1.0*' \
    'cython=0.23*' \
    'patsy=0.4*' \
    'statsmodels=0.6*' \
    'cloudpickle=0.2*' \
    'dill=0.2*' \
    'numba=0.23*' \
    'bokeh=0.11*' \
    'sqlalchemy=1.1*' \
    'hdf5=1.8.17' \
    'h5py=2.6*' \
    'vincent=0.4.*' \
    'beautifulsoup4=4.5.*' \
    'xlrd' && \
    conda remove --quiet --yes --force qt pyqt && \
    conda clean -tipsy

# Activate ipywidgets extension in the environment that runs the notebook server
RUN jupyter nbextension enable --py widgetsnbextension --sys-prefix

# Install Python 2 packages
# Remove pyqt and qt pulled in for matplotlib since we're only ever going to
# use notebook-friendly backends in these images
RUN conda create --quiet --yes -p $CONDA_DIR/envs/python2 python=2.7 \
    'nomkl' \
    'ipython=4.2*' \
    'ipywidgets=5.2*' \
    'pandas=0.19*' \
    'numexpr=2.6*' \
    'matplotlib=1.5*' \
    'scipy=0.18.*' \
    'seaborn=0.7*' \
    'scikit-learn=0.18*' \
    'scikit-image=0.11*' \
    'sympy=1.0*' \
    'cython=0.23*' \
    'patsy=0.4*' \
    'statsmodels=0.6*' \
    'cloudpickle=0.1*' \
    'dill=0.2*' \
    'numba=0.23*' \
    'bokeh=0.11*' \
    'hdf5=1.8.17' \
    'h5py=2.6*' \
    'sqlalchemy=1.0*' \
    'pyzmq' \
    'vincent=0.4.*' \
    'beautifulsoup4=4.5.*' \
    'xlrd' && \
    conda remove -n python2 --quiet --yes --force qt pyqt && \
    conda clean -tipsy
# Add shortcuts to distinguish pip for python2 and python3 envs
RUN ln -s $CONDA_DIR/envs/python2/bin/pip $CONDA_DIR/bin/pip2 && \
    ln -s $CONDA_DIR/bin/pip $CONDA_DIR/bin/pip3

# Import matplotlib the first time to build the font cache.
ENV XDG_CACHE_HOME /home/$NB_USER/.cache/
RUN MPLBACKEND=Agg $CONDA_DIR/envs/python2/bin/python -c "import matplotlib.pyplot"

# Configure ipython kernel to use matplotlib inline backend by default
RUN mkdir -p $HOME/.ipython/profile_default/startup
COPY mplimporthook.py $HOME/.ipython/profile_default/startup/

# Install Jupyter notebook and other conda packages as prspctr
RUN $CONDA_DIR/bin/conda install --quiet --yes \
    'notebook=4.3*' \
    jupyterhub=0.7 \
    'numpy=1.11*' \
    'dask=0.13*' \
    'graphviz=2.38*' \
    'networkx=1.11*' \
    'pytables=3.3*' \
    'psutil=5.0*' && \
    conda clean -tipsy


# ##############################
# prospecting  - section 2/3
# ------------------------------
# Setup prspctr home directory
RUN mkdir /home/$NB_USER/.jupyter && \
    mkdir -p $PROJECTDIR && \
    mkdir -p $CODEDIR && \
    mkdir -p $CREDSDIR && \
    mkdir -p $CERTSDIR && \
    mkdir -p $DATADIR && \
    mkdir -p $TMPDIR && \
    mkdir -p $SCRIPTSDIR && \
    mkdir -p $NOTEBOOKDIR && \
    mkdir -p $JOBLIB_TEMP_FOLDER && \
    echo "cacert=/etc/ssl/certs/ca-certificates.crt" > /home/$NB_USER/.curlrc

COPY requirements.txt $PROJECTDIR/requirements.txt
COPY requirements_nonconda.txt $PROJECTDIR/requirements_nonconda.txt
COPY setup.py $PROJECTDIR/setup.py
# ##############################

USER root

# Install Python 2 kernel spec globally to avoid permission problems when NB_UID
# switching at runtime and to allow the notebook server running out of the root
# environment to find it. Also, activate the python2 environment upon kernel
# launch.
RUN pip install kernda --no-cache && \
    $CONDA_DIR/envs/python2/bin/python -m ipykernel install && \
    kernda -o -y /usr/local/share/jupyter/kernels/python2/kernel.json && \
    pip uninstall kernda -y


# ##############################
# prospecting  - section 3/3
# ------------------------------
# add password for user and add user to sudo
RUN echo "$NB_USER:${USERSUDOPW:-'shouldhavepassedhashedpwduringbuild'}" | chpasswd -e && \
    adduser $NB_USER sudo && \
    pip3 install --upgrade pip && \
    pip3 install -r $PROJECTDIR/requirements_nonconda.txt
# ##############################

EXPOSE 8888
WORKDIR $PROJECTDIR

# Configure container startup
ENTRYPOINT ["tini", "--"]
CMD ["start-notebook.sh"]

# Add local files as late as possible to avoid cache busting
COPY start.sh /usr/local/bin/
COPY start-notebook.sh /usr/local/bin/
COPY start-singleuser.sh /usr/local/bin/
COPY jupyter_notebook_config.py /home/$NB_USER/.jupyter/
RUN chown -R $NB_USER:users /home/$NB_USER/.jupyter && \
    chown -R $NB_USER:users /home/$NB_USER/work
RUN chmod +rx /usr/local/bin/start*

# Switch back to prspctr to avoid accidental container runs as root
USER $NB_USER
