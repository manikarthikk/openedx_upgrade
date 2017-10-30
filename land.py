"""
A collection of functions related to Open edX Integration with L&D
"""

import json
from datetime import datetime, timedelta

import requests
import adal



class LdIntegration(object):
    def __init__(self, logger=None):

        # get reference to the user-specified python logger that has already been initialized
        self.logger = logger
        self.db = None

    def log(self, message, message_type="info"):

        """
        Log a message

        :param message: the message to log
        :param message_type: the type of log message (info, warning or debug). If a message is not info or warning, it
        falls back to debug

        """

        if self.logger:
            if message_type == "info":
                self.logger.info(message)

            elif message_type == "warning":
                self.logger.warning(message)

            else:
                self.logger.debug(message)

    def get_access_token(self,resource,url,headers,data):

        """

        Get OAuth2 access  token for REST API call in azure MSI extension

        :param resourse_url: principal resource url. Example: 'https://vault.azure.net'
        :param headers: required headers for the service url
        :param url: this was the request url. By defalt 'http://localhost:50342/oauth2/token' in MSI implementation
        :param data: Meta data for the servie
        :return: returns the access_token

        """

        #resource = 'https://vault.azure.net'
        #url = 'http://localhost:50342/oauth2/token'
        #data = dict(resource=resource)
        #headers = dict(MetaData='true')

        response = requests.post(url, data=data, headers=headers,timeout=1)
        if not response.ok:
            raise RuntimeError(response.content)
        return response.json()['access_token']

    def get_access_token_ld(self, ldauthorityhosturl, ldtenant, ldresource, ldclientid, ldclientSecret):
        """
        Get OAuth2 access token for REST API call for L&D services

        :param ldtenant: tenant id of the AAD application
        :param ldresource: L&D resource url
        :param ldclientid: client id of the AAD application
        :param ldclientSecret: client secret provided by L&D
        :return: access token

        """
        authority_url = (ldauthorityhosturl + '/' + ldtenant)
        context = adal.AuthenticationContext(
            authority_url, validate_authority=ldtenant != 'adfs',
            api_version=None)

        token = context.acquire_token_with_client_credentials(
            ldresource,
            ldclientid,
            ldclientSecret)

        return token['accessToken']

    def get_keyvault_secret(self, access_token, keyvault_url, key_name, api_version='2016-10-01'):
        """

        Get value of a key from Azure Key-vault
        :param access_token: access_token obtained from azure AD tenant
        :param keyvault_url: url of the key_vault
        :param key_name: name of the key_vault
        :param api_version: GRAPH api version for the key_vault
        :return: secret value for the provided key

        """

        headers_credentilas = {'Authorization': 'Bearer' + ' ' + (access_token)}
        request_url = "{}/secrets/{}?api-version={}".format(keyvault_url, key_name, api_version)
        response = requests.get(request_url, headers=headers_credentilas).json()
        return response['value']

    def get_api_data(request_url,headers=None):
        """

        :param request_url: api url to get the data
        :param headers: headers for the api request. defaults to None
        :return: return the api data

        """
        try:
            return requests.get(request_url,headers=headers, verify=False,timeout=1).json()
        except requests.exceptions.Timeout as e:
            self.log(e, "debug")
        except requests.exceptions.ConnectionError as e:
            self.log(e, "debug")
        except requests.exceptions.RequestException as e:
            self.log(e, "debug")

    def get_course_catalog_data(request_url,headers=None):
        """

        :param request_url: api url to get the data
        :param headers: required headers obtained from open edx
        :return: return the results including the paginated data

        """
        user_data = self.get_api_data(request_url,headers)
        req_api_data = user_data['results']
        while user_data['pagination']['next']:
            user_data = self.get_api_data(user_data['pagination']['next'],headers)
            req_api_data = req_api_data + user_data['results']
        return req_api_data
