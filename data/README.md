
Place data files in this directory. This directory is mounted to the notebook container via the data-specific container created after build (see main README.md), so any data files here will be shared (and persist) between host and container.

When an initial SheetsApi or DriveApi instance is created, a `discoveryapi_<apiname>.json` file will be saved here. The discovery files provide a comprehensive overview of the rest API available for each service. The discovery files will match the `discoveryRestUrl` attribute listed [here](https://www.googleapis.com/discovery/v1/apis?preferred=true) (ex: [sheets](https://www.googleapis.com/discovery/v1/apis/sheets/v4/rest), [drive](https://www.googleapis.com/discovery/v1/apis/drive/v3/rest).

Though the SheetsApi and DriveApi classes rely on the methods made available via the API-specific service objects returned via the [`google-api-python-client`](https://developers.google.com/api-client-library/python/start/get_started) (vs using the Rest API directly), the discovery information can provide insight into the scopes available for each API, links to documentation, etc.


Example data is available here:

- Train - [InnoCentive_Challenge_9933493_training_data.csv.gz (90 MB)](https://storage.cloud.google.com/prospecting/data/innocentive/InnoCentive_Challenge_9933493_training_data.csv.gz)
- Test - [InnoCentive_Challenge_9933493_testing_data.csv.gz (109 MB)](https://storage.cloud.google.com/prospecting/data/innocentive/InnoCentive_Challenge_9933493_testing_data.csv.gz) (**no way to check accuracy of predictions as test outcomes were not provided)

Example data is from a old InnoCentive challenge [# 9933493](https://www.innocentive.com/ar/challenge/9933493)