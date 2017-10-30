"""
A collection of functions related to Open edX Integration with L&D
"""

import json
from datetime import datetime, timedelta

import requests
import adal



class Ldintegration(object):
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

        Get OAuth2 access  token for REST API call

        """

        #resource = 'https://vault.azure.net'
        #url = 'http://localhost:50342/oauth2/token'
        #data = dict(resource=resource)
        #headers = dict(MetaData='true')

        response = requests.post(url, data=data, headers=headers)
        if not response.ok:
            raise RuntimeError(response.content)
        return response.json()['access_token']

    def get_access_token_ld(self, ldauthorityhosturl, ldtenant, ldresource, ldclientid, ldclientSecret):
        """

        :param ldtenant:
        :param ldresource:
        :param ldclientid:
        :param ldclientSecret:
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

        # return type(json.dumps(token,indent=2))
        return token['accessToken']

    def get_keyvault_secret(self, access_token, keyvault_url, key_name, api_version='2016-10-01'):
        """

        Get value of a key from Azure Key-vault
        :param access_token:
        :param keyvault_url:
        :param key_name:
        :param api_version:
        :return: secret value

        """
        # print("Here is the access_token")
        # print(access_token)
        headers_credentilas = {'Authorization': 'Bearer' + ' ' + (access_token)}
        request_url = "{}/secrets/{}?api-version={}".format(keyvault_url, key_name, api_version)
        # print(request_url)
        response = requests.get(request_url, headers=headers_credentilas).json()
        return response['value']
