"""
A collection of functions related to Open edX Integration with L&D
"""
from datetime import datetime, timedelta
import json
import requests
import adal
import re
#pylint: disable=line-too-long


class LdIntegration(object):
    """
    **Use cases**

    get the data from OpenEdx and post the data to L&D in MSI(Managed Service Identity)
        enabled Linux deployment.

        1) get secrets from Azure key vault
        2) get data from Edx
        3) Mapping the data
        4) Post the data to L&D

    """
    def __init__(
            self,
            logger=None
    ):

        # get reference to the user-specified python logger that has already been initialized
        self.logger = logger

    def log(
            self,
            message,
            message_type="info"
    ):

        """
        Log a message

        :param message: the message to log
        :param message_type: the type of log message (info, warning, error or debug).
                             If a message is not info or warning, it falls back to debug

        """

        if self.logger:
            if message_type == "info":
                self.logger.info(message)

            elif message_type == "warning":
                self.logger.warning(message)
            
            elif message_type == "error":
                self.logger.error(message)
            
            else:
                self.logger.debug(message)

    def get_access_token(
            self
    ):

        """

        Get OAuth2 access token for REST API call using azure MSI extension

        :param resourse_url: principal resource url. Example: 'https://vault.azure.net'
        :param headers: required headers for the service url
        :param url: this was the request url. By defalt 'http://localhost:50342/oauth2/token'
                      in MSI implementation
        :param data: Meta data for the servie
        :return: returns the access_token

        """

        resource = 'https://vault.azure.net'
        url = 'http://localhost:50342/oauth2/token'
        data = dict(resource=resource)
        headers = dict(MetaData='true')

        response = requests.post(url, data=data, headers=headers, timeout=1)
        if not response.ok:
            raise RuntimeError(response.content)
        else:
            self.log("Got OAuth2 access token using MSI")
        return response.json()['access_token']

    def get_access_token_ld(
            self,
            ldauthorityhosturl,
            ldtenant,
            ldresource,
            ldclientid,
            ldclientsecret
    ):

        """
        Get OAuth2 access token for REST API call for L&D services

        :param ldtenant: tenant id of the AAD application
        :param ldresource: L&D resource url
        :param ldclientid: client id of the AAD application
        :param ldclientsecret: client secret provided by L&D
        :return: access token

        """
        authority_url = (ldauthorityhosturl + '/' + ldtenant)
        context = adal.AuthenticationContext(
            authority_url, validate_authority=ldtenant != 'adfs',
            api_version=None)

        token = context.acquire_token_with_client_credentials(
            ldresource,
            ldclientid,
            ldclientsecret)
        if token['accessToken']:
            self.log("Got Oauth2 access token for L&D REST API")
            return token['accessToken']
        else:
            raise Exception("Un-handled exception occured while accessing the token for L&D")


    def get_key_vault_secret(
            self,
            access_token,
            key_vault_url,
            key_name,
            api_version='2016-10-01'
    ):
        """

        Get value of a key from Azure Key-vault

            1) this function calls a local MSI endpoint to get an access token

            2) MSI uses the locally injected credentials to get an access token from Azure AD

            3) returned access token can be used to authenticate to an Azure service

        :param access_token: access_token obtained from azure AD tenant
        :param keyvault_url: url of the key_vault
        :param key_name: name of the key_vault
        :param api_version: GRAPH api version for the key_vault
        :return: secret value for the provided key

        """

        headers_credentilas = {'Authorization': 'Bearer' + ' ' + (access_token)}
        request_url = "{}/secrets/{}?api-version={}".format(key_vault_url, key_name, api_version)
        response = requests.get(request_url, headers=headers_credentilas)
        if response.ok:
            self.log("Got the secret key %s from key vault", key_name)
        else:
            raise Exception("Un-handled exception occured while accessing %s from key vault", key_name)
        return response.json()['value']

    def get_api_data(
            self,
            request_url,
            headers=None
    ):

        """
        Get the data from the provided api url with optional headers using requests python library

        :param request_url: api url to get the data
        :param headers: headers for the api request. defaults to None
        :return: return the api data

        """
        try:
            results = requests.get(request_url, headers=headers, verify=False, timeout=2).json()
            return results
        except requests.exceptions.Timeout as error:
            self.log(error, "error")
        except requests.exceptions.ConnectionError as error:
            self.log(error, "error")
        except requests.exceptions.RequestException as error:
            self.log(error, "error")

    def get_course_catalog_data(
            self,
            request_url,
            headers=None
    ):
        """
        returns data with combined paginated responses for a given api url with optional headers

        :param request_url: api url to get the data
        :param headers: required headers obtained from open edx
        :return: return the results including the paginated data

        """
        self.log("Calling OpenEdx Course Catalog API")
        user_data = self.get_api_data(request_url, headers)
        req_api_data = user_data['results']
        while user_data['pagination']['next']:
            user_data = self.get_api_data(user_data['pagination']['next'], headers)
            req_api_data = req_api_data + user_data['results']
        return req_api_data

    def catalog_data_mapping(
            self,
            source_system_id,
            course_catalog_data
    ):

        """

        mapping the provided EDX data to L&D acceptable request body format

        :param course_catalog_data: course catalog data obtained from edx
        :param source_system_id: system_id provided by L&D as part of onboarding
        :return: mapped course catalog data to L&D

        """
        self.log("Mapping the course catalog data to L&D format")
        all_course_catalog = []
        each_catalog = {}
        for each in course_catalog_data:
            each_catalog["Confidential"] = "null"
            each_catalog["BIClassification"] = "MBI"
            each_catalog["BusinessOrg"] = "null"
            each_catalog["IsPrimary"] = "true"
            each_catalog["IsShareable"] = "null"
            each_catalog["CourseType"] = "Build"
            each_catalog["HideInSearch"] = "hidden"
            each_catalog["HideInRoadMap"] = "null"
            each_catalog["ParentSourceSystemId"] = "0"
            each_catalog["Deleted"] = "false"
            each_catalog["SourceSystemid"] = source_system_id
            # each_catalog["Language"] = "en-us"
            each_catalog["Version"] = "1"
            each_catalog["Brand"] = "Infopedia"
            each_catalog["Modality"] = "OLT"
            each_catalog["MediaType"] = "Course"
            each_catalog["Status"] = "Active"
            each_catalog["DescriptionLong"] = "null"
            each_catalog["SunsetDate"] = each['end'].split('T')[0]
            each_catalog["Keywords"] = each['name']
            each_catalog["ThumbnailLargeUri"] = each['media']['image']['large']
            each_catalog["AvailabilityDate"] = each['enrollment_start'].split('T')[0]
            each_catalog["CreatedDateAtSource"] = datetime.now().replace(microsecond=0).isoformat()
            each_catalog["Name"] = each['name']
            each_catalog["Url"] = each['blocks_url'].split('/')[0] + '//' + each['blocks_url'].split('/')[2] + "/courses/" + each['course_id'] + "/about"
            each_catalog["DescriptionShort"] = "null"
            each_catalog["ThumbnailShort"] = each['media']['image']['small']
            each_catalog["TrainingOrgs"] = each['org']
            each_catalog["ExternalId"] = each['course_id'].split(':')[1]
            all_course_catalog.append(each_catalog)
            each_catalog = {}
        return json.dumps(all_course_catalog)


    def post_data_ld(self, url, headers, data):
        """

        POST data to L&D services

        """
        self.log("Preparing to post the data to L&D Course catalog API")
        try:
            response = requests.post(url, data=data, headers=headers)
            if response.ok:
                message = "Data posted sucessfully with %s" % response
                self.log(message, "info")
            else:
                message = "Error occured while posting the data  %s" % response
                self.log(message, "warning")
        #TODO: change the response.ok to response['errormessage'] = none
        except requests.exceptions.Timeout as error:
            self.log(error, "error")
        except requests.exceptions.ConnectionError as error:
            self.log(error, "error")
        except requests.exceptions.RequestException as error:
            self.log(error, "error")
    def mapping_api_data(self, data):
        all_user_grades = []
        each_user = {}
        #LOG.warning("Starting the mapping of data")
        for user in data:
            #L&D only accepts the user emails with '@microsoft.com' accounts
            if  not bool(re.search('(?i)^(?:(?!(microsoft.com)).)+$', user['username'])):
                #print i.keys()
                #each_user["UserAlias"] = user['email']
                each_user["UserAlias"] = 'v-mankon@microsoft.com'
                each_user["ExternalId"] = user['course_key']
                #each_user["ConsumptionStatus"] = i['letter_grade']
                #each_user["grade"] = i[3]
                each_user["SourceSystemId"] = 16
                each_user["PersonnelNumber"] = 0
                each_user["SFSync"] = 0
                each_user["UUID"] = "null"
                each_user["ActionVerb"] = "null"
                each_user["ActionValue"] = 0
                #each_user["CreatedDate"] = i[4]
                each_user["CreatedDate"] = "22"
                each_user["SubmittedBy"] = "landd_user@oxa.com"
                each_user["ActionFlag"] = "null"
                if each_user['letter_grade'] == 'Pass':
                    each_user["ConsumptionStatus"] = 'Passed'
                elif each_user['letter_grade'] == 'Fail':
                    each_user["ConsumptionStatus"] = "Failed"
                else:
                    each_user["ConsumptionStatus"] = "InProgress"
            all_user_grades.append(each_user)
            each_user = {}

        #LOG.warning("Mapping of data is finished")
        return json.dumps(all_user_grades)


    def get_and_post_consumption_data(self, request_edx_url, edx_headers, ld_headers, consumption_url_ld):
        """
        TODO: 
        """
        start_date = open('api_call_time.txt', 'r')
        k = start_date.read()
        #time_log = open('api_call_time.txt', 'w')
        #f = open('api_call_time.txt', 'w')
        #call_time = (datetime.now()-timedelta(days=29)).replace(microsecond=0).isoformat()
        #time_log.write(call_time)
        start_date.close()
        end_date = datetime.now().replace(microsecond=0).isoformat()
        self.log('here is the end call time',"info")
        self.log(end_date, "info")
        request_edx_url = request_edx_url + '&start_date=' + k[:19] + '&end_date=' + end_date
        user_data = self.get_api_data(request_edx_url, edx_headers)
        #print(user_data)
        #req_grades_data = user_data['results']
        #self.mapping_api_data(user_data['results'])
        self.post_data_ld(consumption_url_ld, ld_headers, self.mapping_api_data(user_data['results']))
        while user_data['pagination']['next']:
            user_data = self.get_api_data(user_data['pagination']['next'], edx_headers)
            self.log("hello","info")
            response = self.post_data_ld(consumption_url_ld, ld_headers, self.mapping_api_data(user_data['results']))
            #req_grades_data = req_grades_data + user_data['results']
        write_time = open('api_call_time.txt','w')
        write_time.write(end_date)

        return user_data
