![prospecting](https://img.shields.io/badge/prospecting-active-lightgrey.svg) ![license](https://img.shields.io/badge/license-MIT-blue.svg)

<!-- 
![docker pulls](https://img.shields.io/docker/pulls/jupyter/base-notebook.svg) ![docker stars](https://img.shields.io/docker/stars/jupyter/base-notebook.svg) [![](https://images.microbadger.com/badges/image/jupyter/base-notebook.svg)](https://microbadger.com/images/jupyter/base-notebook "jupyter/base-notebook image metadata")
-->

# Prospecting &#x2692; <!-- &#9874; -->

This project started as an effort to predict a 'prospect score' for each business in a list of current and (predominantly) potential customers. Though the initial goal was to provide a list to help prioritize sales opportunities (ex. rank order prospects by state), I also had some ideas about tying in Google Sheets to help with my typical ML workflow (data profiling, model performance reporting, and delivery of final predictions, revisiting column treatments, etc). OAuth 2.0 is used for Google API authentication when using the `SheetsApi` and `DriveApi` classes, and the usual Sheets sharing options exist if you want to invite collaborators.

I'll be updating this README and documentation in general...In the interim - as an example of how Google Sheets is used, the following table outlines the various spreadsheets and tabs used:

| spreadsheet | sheet | note
| --- | --- | ---
| **prospecting_metadata** | _metadata_ | Control logic for column processing treatments; used by Python to inform how each column is processed. The functions in `process.py` rely on information from this tab.
|  | _raw_descr_ | Descriptive information about raw data (`df_raw`)
|  | _clean_descr_ | Descriptive information about cleaned dataset (`df_clean`)
| --- | --- | ---
| **prospecting_model_reporting** | _session_report_ | Summarizes model performance, plan to make this the main performance tab. A "session" represents an instance of a "ModelSession" class instance which is used to share access to train/test sets.
|  | _cv_results_ | If GridSearchCV is used, the `GridSearchCV.cv_results_` reporting is saved here (shows k-fold performance for each parameter set evaluated)
|  | _model_types_ | A simple lookup table, used by Python script a reference when building the report for the `session_report` tab
| --- | --- | ---
| **prospecting_predictions** | _predictions_ | Final predictions, with probabilities, by firm
|  | _prospects_ | Master list of prospects
|  | _README_ | Intend to use as an FYI tab, to provide overview of health of predictions made (ex. highlight number of correct/incorrect predictions, etc)
<!--
- **prospecting_metadata**
 - _metadata_ - Control logic for column processing treatments; used by Python to inform how each column is processed
 - _raw_descr_ - Descriptive information about raw data (`df_raw`)
 - _clean_descr_ - Descriptive information about cleaned dataset (`df_clean`)

- **prospecting_model_reporting** (data model WIP)
 - _session_report_ - Summarizes model performance, plan to make this the main performance tab. A "session" represents an instance of a "ModelSession" class I created to allow sharing of train/test sets.
 - _cv_results_ - If GridSearchCV is used, the `GridSearchCV.cv_results_` reporting is saved here (shows k-fold performance for each parameter set evaluated)
 - _model_types_ - A simple lookup table, used as a reference when building the report for the `session_report` tab

- **prospecting_predictions**
 - _predictions_ - Final predictions, with probabilities, by firm
 - _prospects_ - Master list of prospects
 - _README_ - Intend to use as an FYI tab, and to provide overview of health of predictions made (ex. highlight number of correct/incorrect predictions, etc)
-->

## Overview

* The project directory contains:
```
        .
        ├── .dockerignore
        ├── .gitattributes              # For CRLF correction
        ├── .gitignore
        ├── credentials/                # Not necessarily best practice, but convenient
        │   ├── README.md
        │   └── certs/
        │       └── README.md
        ├── data/
        │   ├── README.md
        │   └── tmp/                    # Logs saved here
        │       ├── README.md
        │       └── joblib/             # Used by scikit learn when running in Docker container
        │           └── README.md
        ├── Dockerfile                  # See README_detail.md for more info
        ├── LICENSE.md
        ├── jupyter_notebook_config.py  # See README_detail.md for more info
        ├── mplimporthook.py            # Used by Dockerfile
        ├── notebooks/                  # Jupyter Notebooks
        ├── prospecting
        │   ├── __init__.py
        │   ├── env.py                  # Check here for environment variables required
        │   ├── utils.py
        │   ├── api.py                  # Google Sheets and Google Drive API classes
        │   ├── process.py              # Data cleaning functions, relies on info in metadata tab
        │   ├── model.py
        │   ├── report.py
        │   ├── errors.py
        │   └── version.py
        ├── README.md
        ├── requirements_nonconda.txt   # Used by Dockerfile
        ├── scripts
        │   └── hash_jupyter_pw.py      # Create hashed password to use with Docker container
        ├── start-notebook.sh           # Used by Dockerfile
        ├── start.sh                    # Used by Dockerfile
        └── start-singleuser.sh         # Used by Dockerfile
```
