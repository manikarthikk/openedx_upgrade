"""

Course catalolg syncronization between OXA and  L&D

"""
import logging

import sys
import land

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
LOG = logging.getLogger(__name__)

#pylint: disable=line-too-long

def sync_course_catalog():
    """
    1) GET access token from Azure tenant using MSI
    2) GET secrets from Azure keyvault using the access token
    3) GET the Course catalog data from OpenEdx using the secrets obtined from Azure key vault
    4) Map and process the OpenEdx course catalog data with L&D Catalog_UpdateMultipleCatalogAsync API request body
    5) POST the mapped data to L&D Catalog_UpdateMultipleCatalogAsync API

    """
    k = land.LdIntegration(logger=LOG)
    edx_course_catalog_url = "https://lms-lexoxabvtc99-tm.trafficmanager.net/api/courses/v1/courses/"
    key_vault_url = "https://manikeyvault3.vault.azure.net"
    landd_catalog_url = 'https://ldserviceuat.microsoft.com/Consumption/exptrack'

    # get secrets from Azure Key Vault
    edx_api_key = k.get_key_vault_secret(k.get_access_token(), key_vault_url, 'edx-api-key')
    edx_access_token = k.get_key_vault_secret(k.get_access_token(), key_vault_url, 'edx-access-token')
    landd_authorityhosturl = k.get_key_vault_secret(k.get_access_token(), key_vault_url, 'landd-authorityhosturl')
    landd_clientid = k.get_key_vault_secret(k.get_access_token(), key_vault_url, 'landd-clientid')
    landd_clientsecret = k.get_key_vault_secret(k.get_access_token(), key_vault_url, 'landd-clientsecret')
    landd_resource = k.get_key_vault_secret(k.get_access_token(), key_vault_url, 'landd-resource')
    landd_tenant = k.get_key_vault_secret(k.get_access_token(), key_vault_url, 'landd-tenant')
    landd_subscription_key = k.get_key_vault_secret(k.get_access_token(), key_vault_url, 'landd-subscription-key')

    edx_headers = dict(Authorization='Bearer' + ' ' + edx_access_token, X_API_KEY=edx_api_key)
    catalog_data = k.get_course_catalog_data(edx_course_catalog_url, edx_headers)
    headers = {
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': landd_subscription_key,
        'Authorization': k.get_access_token_ld(
            landd_authorityhosturl,
            landd_tenant,
            landd_resource,
            landd_clientid,
            landd_clientsecret
            )
        }

    k.post_data_ld(landd_catalog_url, headers, k.catalog_data_mapping(16, catalog_data))

if __name__ == "__main__":
    sync_course_catalog()
