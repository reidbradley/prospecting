
Place data files in this directory. When using the Docker image, this directory is mounted to the notebook container via a data-specific container created after building the image (see README_detail.md), so any data files in this directory will be shared (and persist) between host and container.

When an initial SheetsApi or DriveApi instance is created, a `discoveryapi_<apiname>.json` file will be saved here. The discovery files provide a comprehensive overview of the rest API available for each service. These files are useful when learning about each API. The discovery files will match these documents: [sheets](https://www.googleapis.com/discovery/v1/apis/sheets/v4/rest), [drive](https://www.googleapis.com/discovery/v1/apis/drive/v3/rest))

Example data is available here:

- Train - [InnoCentive_Challenge_9933493_training_data.csv.gz (90 MB compressed / 566 MB decompressed)](https://storage.cloud.google.com/prospecting/data/innocentive/InnoCentive_Challenge_9933493_training_data.csv.gz)
- Test - [InnoCentive_Challenge_9933493_testing_data.csv.gz (109 MB compressed / 688 MB decompressed)](https://storage.cloud.google.com/prospecting/data/innocentive/InnoCentive_Challenge_9933493_testing_data.csv.gz) (**no way to check accuracy of predictions as test outcomes were not provided, including this file for completeness)

Example data is from an old InnoCentive challenge [# 9933493](https://www.innocentive.com/ar/challenge/9933493)