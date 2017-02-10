
from __future__ import print_function
import httplib2
import os
import json

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import pandas as pd

from prospecting.env import (PROJECTNAME,
                             CREDSDIR,
                             CLIENT_SECRET_FILE,
                             DATADIR,
                             NOAUTH_LOCAL_WEBSERVER
                             )

try:
    import argparse
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    parser.set_defaults(noauth_local_webserver=NOAUTH_LOCAL_WEBSERVER)
    flags = parser.parse_known_args()[0]
except ImportError:
    flags = None

import logging
log = logging.getLogger('prospecting.api')


class GoogleApi:
    """Base class for interfacing with Google APIs


    https://developers.google.com/apis-explorer/

    """

    def __init__(self, apiname, apiversion, scopelist):
        """Initialize GoogleApi base class

        Args:
            apiname (str):  Name of Google API, example: 'sheets'
            apiversion (str): Version of API, example: 'v4'
            scopelist (list):   List of authorization scopes, example: []

        """
        self.api_name = apiname
        self.api_version = apiversion
        self.api_id = (self.api_name + ":" + self.api_version)
        self.api_scope = scopelist
        #self.discovery_url = ('https://' + self.api_name + '.googleapis.com/$discovery/rest?'
        #                      'version=' + self.api_version)
        self.discovery_url = ('https://www.googleapis.com/discovery/v1/apis/' + self.api_name +
                              '/' + self.api_version + '/rest')
        self.api_info = self._discover_api(self.discovery_url)

    def authenticate(self):
        log.info('Authenticating...{0}, {1}'.format(self.api_name, self.api_version))
        self.credentials = self._get_credentials(self.api_scope)
        self.http = self.credentials.authorize(httplib2.Http())
        service = self._build_service_object()
        log.info('Successfully authenticated...{0}, {1}'.format(self.api_name, self.api_version))
        return service

    def reauthenticate(self, scopelist):
        if os.path.isfile(self.credential_path):
            os.remove(self.credential_path)
        self.api_scope = scopelist
        self.authenticate()

    def _get_credentials(self, scopelist):
        log.info('Getting credentials...')
        credsfile = ('googleapis.' + self.api_name + '.' + PROJECTNAME + '.json')
        self.credential_path = os.path.join(CREDSDIR, credsfile)
        self.store = Storage(self.credential_path)
        file_exists = os.path.isfile(self.credential_path)
        scopes_match = False
        if file_exists:
            with open(self.credential_path) as f:
                credjson = json.load(f)
            scopes_match = set(credjson['scopes']) == set(scopelist)
        if scopes_match:
            creds = self.store.get()
        else:
            creds = None
            if (not creds or creds.invalid):
                creds = self._run_credentials_flow()
        return creds

    def _run_credentials_flow(self):
        log.info('Running credentials flow...')
        secretspath = os.path.join(CREDSDIR, CLIENT_SECRET_FILE)
        flow = client.flow_from_clientsecrets(secretspath, self.api_scope)
        flow.user_agent = PROJECTNAME
        if flags or flags is None:
            self.credentials = tools.run_flow(flow, self.store, flags)
        else:  # Needed only for compatibility with Python 2.6
            self.credentials = tools.run(self.flow, self.store)
        log.info('Storing credentials to {0}'.format(self.credential_path))
        return self.credentials

    def _build_service_object(self):
        log.info('Building service object...')
        service_object = discovery.build(self.api_name,
                                         self.api_version,
                                         http=self.http,
                                         discoveryServiceUrl=self.discovery_url)
        log.info('Service object built...{0}'.format(service_object))
        return service_object

    def _discover_api(self, discoveryurl):
        discovery_file = os.path.join(DATADIR,
                                      'discoveryapi_' + self.api_name + '.json')
        if os.path.isfile(discovery_file):
            log.info(('Reading discovery file for {0}').format(self.api_id))
            with open(discovery_file) as f:
                disco_info = json.load(f)
        else:
            h = httplib2.Http()
            resp, content = h.request(discoveryurl, 'GET')
            log.info(('Resp from 1st discoveryurl attempt: {0}'.format(resp['status'])))
            if resp['status'] == '404':
                DISCOVERY_URI = 'https://www.googleapis.com/discovery/v1/apis?preferred=true'
                resp2, content2 = h.request(DISCOVERY_URI, 'GET')
                disco_all = json.loads(content2.decode())
                disco_api = [apiinfo for apiinfo in disco_all['items'] for k, v in apiinfo.items() if v == self.api_id][0]
                self.discovery_url = disco_api['discoveryRestUrl']
                resp, content = h.request(self.discovery_url, 'GET')
                if resp['status'] == '404':
                    try:
                        raise Exception(resp['status'])
                    except Exception as e:
                        log.error('Error response in 2nd discoveryurl attempt: {0}'.format(e))
                        assert resp['status'] != '404'
                else:
                    disco_info = json.loads(content.decode())
                    print(disco_info)
                    log.info(('Resp from 2nd discoveryurl attempt: {0}'.format(resp['status'])))
            disco_info = json.loads(content.decode())
            log.info(('Writing discovery file for {0}').format(self.api_id))
            with open(discovery_file, 'w') as outfile:
                json.dump(json.loads(content.decode()), outfile)
            log.info('Read from api, write to file complete. Check new file in' + discovery_file)
        return disco_info


class SheetsApi(GoogleApi):
    """Class for SheetsApi object


    https://developers.google.com/resources/api-libraries/documentation/sheets/v4/python/latest/
    https://developers.google.com/apis-explorer/#p/sheets/v4/

    """

    def __init__(self,
                 apiname='sheets',
                 apiversion='v4',
                 spreadsheetid=None,
                 sheetrange=None,
                 scopelist=['https://www.googleapis.com/auth/spreadsheets.readonly',
                            'https://www.googleapis.com/auth/drive.readonly']):
        self.spreadsheet_id = spreadsheetid
        self.sheet_range = sheetrange
        self.info = None  # reserved for metadata
        self.sheets = {}  # store data from get requests
        GoogleApi.__init__(self, apiname, apiversion, scopelist)
        pass

    def authenticate(self):
        self.service = GoogleApi.authenticate(self)

    def get_ss_info(self, sheetranges=None, includegriddata=False):
        """Returns the spreadsheet from a given ID

        Params:
            sheetranges (list): List of comma separated range names as strings, Ex: ['Sheet1','Sheet2!A1:B5]
            includegriddata (bool): True if grid data should be returned, Ex: True

        Returns:
            {
                "spreadsheetId": "1MdZzXvqftMJTfLdbBpzYJA42kCv9R6SSEAT5tSUNe5g",
                "properties": {
                    ...
                },
                "sheets": [
                    {
                        "properties": {
                            ...
                        },
                        ...
                    }
                ],
                "spreadsheetUrl": "https://docs.google.com/spreadsheets/d/.../edit"
            }
        """
        spreadsheetid = self.spreadsheet_id
        if sheetranges is None:
            if spreadsheetid is None:
                raise ValueError('Please set self.spreadsheet_id')
            response = self.service.spreadsheets().get(
                spreadsheetId=spreadsheetid,
                includeGridData=includegriddata
            ).execute()
            log.info('Spreadsheet loaded.')
            log.info('Sheets include: {0}'.format([sheet['properties']['title'] for sheet in response['sheets']]))
            return response
        else:
            response = self.service.spreadsheets().get(
                spreadsheetId=spreadsheetid,
                ranges=sheetranges,
                includeGridData=includegriddata
            ).execute()
            return response

    def get(self,
            sheetrange=None,
            asdataframe=True,
            headerrow=0,
            majordimension='ROWS',
            valuerenderoption='FORMATTED_VALUE',
            datetimerenderoption='SERIAL_NUMBER'):
        """Returns one range of values from a spreadsheet.

        Params:
            sheetrange (str): Name of range to get, Ex: ['Sheet1']
            asdataframe (bool): Flag to determine response type, Ex: False
            headerrow (int): Specifies location of header, Ex: 2
            majordimension (str): The major dimension that results should use, Ex 'COLUMNS'
            valuerenderoption (str): How values should be represented in the output, Ex: 'UNFORMATTED_VALUE'
            datetimerenderoption (str): How dates, times, and durations should be represented in the output,
                                        Ex: 'FORMATTED_STRING'

        Returns:
            Google Sheet as requested

        https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values/get

        """
        tmpdf = pd.DataFrame()
        spreadsheetid = self.spreadsheet_id
        if spreadsheetid is None:
            raise ValueError('Please set self.spreadsheet_id')
        if not sheetrange:
            sheetrange = self.sheet_range
        self.response = self.service.spreadsheets().values().get(
            spreadsheetId=spreadsheetid,
            range=sheetrange,
            majorDimension=majordimension,
            valueRenderOption=valuerenderoption,
            dateTimeRenderOption=datetimerenderoption
        ).execute()
        values = self.response.get('values', None)
        if not values:
            log.info('No data found.')
            tmpdf = None
        else:
            if headerrow is not None:
                if asdataframe is True:
                    try:
                        tmpdf = pd.DataFrame.from_records(values[(headerrow + 1):len(values)],
                                                          columns=values[headerrow])
                    except AssertionError as err:
                        print('AssertionError: {0}'.format(err))
                        print('No columns in headerrow. Add columns to sheet or pass headerrow=None.')
                        print('Check self.data for malformed response (no columns set).')
                else:
                    tmpdf = values[(headerrow + 1)]
            else:
                if asdataframe is True:
                    tmpdf = pd.DataFrame.from_records(values[0:len(values)])
                else:
                    tmpdf = values[0:len(values)]
        return (tmpdf)

    def batchGet(self,
                 sheetranges,
                 majordimension='ROWS',
                 valuerenderoption='FORMATTED_VALUE',
                 datetimerenderoption='SERIAL_NUMBER'):
        """Returns one or more ranges of values from a spreadsheet.

        Params:
            sheetranges (list): List of comma separated range names as strings, Ex: ['Sheet1','Sheet2!A1:B5]
            majordimension (str): The major dimension that results should use, Ex 'COLUMNS'
            valuerenderoption (str): How values should be represented in the output, Ex: 'UNFORMATTED_VALUE'
            datetimerenderoption (str): How dates, times, and durations should be represented in the output,
                                        Ex: 'FORMATTED_STRING'

        Returns:
            List of tuples, one tuple for each range requested, Ex: [('col_1, col_2), ]


        https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values/batchGet

        """
        spreadsheetid = self.spreadsheet_id
        if spreadsheetid is None:
            raise ValueError('Please set self.spreadsheet_id')
        if not sheetranges:
            sheetranges = self.sheet_range
        self.response = self.service.spreadsheets().values().batchGet(
            spreadsheetId=spreadsheetid,
            ranges=sheetranges,
            majorDimension=majordimension,
            valueRenderOption=valuerenderoption,
            dateTimeRenderOption=datetimerenderoption
        ).execute()
        values = {vr['range']: vr.get('values', []) for vr in self.response['valueRanges']}
        if not values:
            print('No data found.')
        return {k: v for k, v in values.items()}

    def update(self,
               dataframe,
               sheetrange,
               majordimension='ROWS',
               valueinputoption='RAW',
               includevaluesinresponse=False,
               responsevaluerenderoption='FORMATTED_VALUE',
               responsedatetimerenderoption='SERIAL_NUMBER'):
        """Sets values in a range of a spreadsheet

        Params:
            sheetrange (str):                   Name of range to get,
                                                Ex: ['Sheet1']

            valueinputoption (str):             How the input data should be interpreted,
                                                Ex: 'USER_ENTERED'

            includevaluesinresponse (bool):     Determines if the update response should include
                                                the values of the cells that were updated,
                                                Ex. False

            responsevaluerenderoption (str):    Determines how values in the response
                                                should be rendered,
                                                Ex: 'UNFORMATTED_VALUE'

            responsedatetimerenderoption (str): Determines how dates, times, and durations
                                                in the response should be rendered,
                                                Ex: 'FORMATTED_STRING'

        Returns:
            response, returns "UpdateValuesResponse" in format:
                {
                  "spreadsheetId": string,
                  "updatedRange": string,
                  "updatedRows": number,
                  "updatedColumns": number,
                  "updatedCells": number,
                  "updatedData": {
                    object(ValueRange)
                  },
                }

        https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values/update

        """
        spreadsheetid = self.spreadsheet_id
        data = {
            "range": sheetrange,
            "majorDimension": majordimension,
            "values":
                [(dataframe.columns.values.tolist())] + (dataframe.values.tolist())
        }
        self.response = self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheetid,
            range=sheetrange,
            valueInputOption=valueinputoption,
            #includeValuesInResponse=includevaluesinresponse,
            #responseValueRenderOption=responsevaluerenderoption,
            #responseDateTimeRenderOption=responsedatetimerenderoption,
            body=data
        ).execute()
        if not self.response:
            log.info('Update Failed!')
        else:
            log.info('Update Successful!')

    def batchUpdate(self,):
        pass

    def clear(self):
        pass

    def batchClear(self):
        pass

    def append(self,
               dataframe,
               sheetrange,
               majordimension='ROWS',
               valueinputoption='RAW',
               insertdataoption='INSERT_ROWS',
               includevaluesinresponse=False,
               responsevaluerenderoption='FORMATTED_VALUE',
               responsedatetimerenderoption='SERIAL_NUMBER'):
        """Append values to a spreadsheet

        Params:
            sheetrange (str): The A1 notation of a range to search for a logical table of data.
                              Values will be appended after the last row of the table,
                              Ex: 'Sheet1'
            valueinputoption (str): How the input data should be interpreted, Ex: 'USER_ENTERED'
            insertdataoption (str): How the input data should be inserted, Example 'OVERWRITE'
            includevaluesinresponse (bool): Determines if the update response should
                                            include the values of the cells that were appended, Ex: False
            responsevaluerenderoption (str): Determines how values in the response should be rendered,
                                             Ex: 'UNFORMATTED_VALUE'
            responsedatetimerenderoption (str): Determines how dates, times, and durations in the response
                                                should be rendered,
                                                Ex: 'FORMATTED_STRING'

        Returns:
            response, returns response body in format:
                {
                  "spreadsheetId": string,
                  "tableRange": string,
                  "updates": {
                    object(UpdateValuesResponse)
                  },
                }

        https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values/append

        """
        spreadsheetid = self.spreadsheet_id
        data = {
            "range": sheetrange,
            "majorDimension": majordimension,
            "values": dataframe.values.tolist()
            #[(dataframe.columns.values.tolist())] + (dataframe.values.tolist())
        }
        self.response = self.service.spreadsheets().values().append(
            spreadsheetId=spreadsheetid,
            range=sheetrange,
            valueInputOption='RAW',
            body=data
        ).execute()
        if not self.response:
            log.info('No data found.')
        else:
            log.info('Append Successful!')

    def extract_sheet_names(self):
        pass

    def load_sheets(self, sheetslist, batch=None):
        data = {}
        if batch is None:
            batch = self.batchGet(sheetslist)
        for s in sheetslist:
            tmp = [value for key, value in batch.items() if s in key][0]
            if tmp is None:
                data[s] = tmp
            else:
                try:
                    data[s] = pd.DataFrame.from_records(tmp[1:len(tmp[1])],
                                                        columns=tmp[0][0:len(tmp[1])])
                except:
                    log.warning('Failed to load dataframe, returning tmp')
                    data[s] = tmp
        return (data)


class DriveApi(GoogleApi):
    """Class for DriveApi object


    https://developers.google.com/resources/api-libraries/documentation/drive/v3/python/latest/
    https://developers.google.com/apis-explorer/#p/drive/v3/

    """

    def __init__(self,
                 apiname='drive',
                 apiversion='v3',
                 scopelist=['https://www.googleapis.com/auth/drive.metadata.readonly']):
        self.service = None
        self.info = None  # reserved for metadata
        self.data = {}  # store data from get requests
        self.files = []
        GoogleApi.__init__(self, apiname, apiversion, scopelist)
        pass

    def authenticate(self):
        self.service = GoogleApi.authenticate(self)

    def list_files(self,
                   query,
                   corpusdomain='user',
                   space='drive',
                   pagesize=100,
                   orderby='name',
                   pagetoken=None):
        """Lists or searches files

        Params:
            q: string, A query for filtering the file results. See the "Search for Files" guide for supported syntax.
            corpus: string, The source of files to list.
                Allowed values
                    domain - Files shared to the user's domain.
                    user - Files owned by or shared to the user.
            spaces: string, A comma-separated list of spaces to query within the corpus. Supported values are 'drive', 'appDataFolder' and 'photos'.
            pageSize: integer, The maximum number of files to return per page.
            orderBy: string, A comma-separated list of sort keys. Valid keys are 'createdTime', 'folder', 'modifiedByMeTime', 'modifiedTime', 'name', 'quotaBytesUsed', 'recency', 'sharedWithMeTime', 'starred', and 'viewedByMeTime'. Each key sorts ascending by default, but may be reversed with the 'desc' modifier. Example usage: ?orderBy=folder,modifiedTime desc,name. Please note that there is a current limitation for users with approximately one million files in which the requested sort order is ignored.
            pageToken: string, The token for continuing a previous list request on the next page. This should be set to the value of 'nextPageToken' from the previous response.

        Returns:
            object

        """
        files = []
        log.info("Requesting files with {0}, {1}, {2}, {3}, {4}, {5}".format(
            query, corpusdomain, space, pagesize, orderby, pagetoken))
        while self.service:
            response = self.service.files().list(
                q=query,
                corpus=corpusdomain,
                spaces=space,
                orderBy=orderby,
                #fields='nextPageToken, files(id, name, mimeType)',
                pageSize=pagesize,
                pageToken=pagetoken
            ).execute()
            if response['files']:
                for file in response.get('files', []):
                    files.append(file)
                    """
                    filename = file.get('name')
                    fileid = file.get('id')
                    mimetype = file.get('mimeType')
                    print('Found file: {0} ({1}) {2}'.format(filename, fileid, mimetype))
                    """
                pagetoken = response.get('nextPageToken', None)
                if pagetoken is None:
                    log.info('File list received! Total files in list: {0}. Check the class instance attribute `driveapiobject.files` for file list.'.format(len(files)))
                    break
            else:
                log.info('No files found matching query:  {0}'.format(query))
                files = None
        return files

    def create(self,
               _body=None,
               mediabody=None,
               keeprevforever=None,
               usecontentasidxtxt=None,
               ignoredefvis=None,
               ocrlang=None):
        """
        Params:
            _body (object): The request body
            mediabody (str):    The filename of the media request body, or an instance of a MediaUpload object.
            keeprevforever (bool):  Whether to set the 'keepForever' field in the new head revision. This is only applicable to files with binary content in Drive.
            usecontentasidxtxt (bool):  Whether to use the uploaded content as indexable text.
            ignoredefaultvis (bool):    Whether to ignore the domain's default visibility settings for the created file. Domain administrators can choose to make all uploaded files visible to the domain by default; this parameter bypasses that behavior for the request. Permissions are still inherited from parent folders.
            ocrlang (str):  A language hint for OCR processing during image import (ISO 639-1 code).

        Returns:
            object

        https://developers.google.com/resources/api-libraries/documentation/drive/v3/python/latest/drive_v3.files.html#create

        """
        pass

    def get(self,
            fileid,
            ackabuse=None):
        """Get a file's metadata or content by ID

        Args:
            fileid: string, The ID of the file. (required)
            ackabuse: boolean, Whether the user is acknowledging the risk of downloading known malware or other abusive files. This is only applicable when alt=media.

        Returns:
            dict object

        https://developers.google.com/resources/api-libraries/documentation/drive/v3/python/latest/drive_v3.files.html#get

        """

        while self.service:
            response = self.service.files().get(
                fileId = fileid
            ).execute()
        return (response)

    def get_media(self,
                  fileid,
                  ackabuse=None):
        """Get a file's metadata or content by ID

        Args:
            fileid: string, The ID of the file. (required)
            ackabuse: boolean, Whether the user is acknowledging the risk of downloading known malware or other abusive files. This is only applicable when alt=media.

        Returns:
            The media object as a string.

        https://developers.google.com/resources/api-libraries/documentation/drive/v3/python/latest/drive_v3.files.html#get_media

        """
        pass

    def update(self,
               fileid,
               _body=None,
               mediabody=None,
               addparents=None,
               removeparents=None,
               usecontentasidxtxt=None,
               ignoredefvis=None,
               ocrlang=None):
        """Updates a file's metadata and/or content with patch semantics.

        Params:
            fileid (str):    The ID of the file. (required)
            _body (object):   The request body
            mediabody (str):   The filename of the media request body, or an instance of a MediaUpload object.
            addarents (str):   A comma-separated list of parent IDs to add.
            removeparents (str):   A comma-separated list of parent IDs to remove.
            usecontentasidxtxt (bool):  Whether to use the uploaded content as indexable text.
            ignoredefaultvis (bool):    Whether to ignore the domain's default visibility settings for the created file. Domain administrators can choose to make all uploaded files visible to the domain by default; this parameter bypasses that behavior for the request. Permissions are still inherited from parent folders.
            ocrlang (str):  A language hint for OCR processing during image import (ISO 639-1 code).

        Returns:
            dict object

        https://developers.google.com/resources/api-libraries/documentation/drive/v3/python/latest/drive_v3.files.html#update

        """
        pass

    def copy(self,
             fileid,
             _body,
             keeprevforever=None,
             ignoredefvis=None,
             ocrlang=None):
        """Creates a copy of a file and applies any requested updates with patch semantics.

        Params:
            fileid (str):   The ID of the file. (required)
            _body (object):    The request body. (required)
            keeprevforever (bool):   Whether to set the 'keepForever' field in the new head revision. This is only applicable to files with binary content in Drive.
            ignoredefvis (bool):  Whether to ignore the domain's default visibility settings for the created file. Domain administrators can choose to make all uploaded files visible to the domain by default; this parameter bypasses that behavior for the request. Permissions are still inherited from parent folders.
            ocrlang (str):    A language hint for OCR processing during image import (ISO 639-1 code).

        Returns:
            object


        https://developers.google.com/resources/api-libraries/documentation/drive/v3/python/latest/drive_v3.files.html#copy

        """
        pass
