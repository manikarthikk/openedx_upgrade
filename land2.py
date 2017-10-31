import logging
import sys
import land

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
LOG = logging.getLogger(__name__)

def sync_course_catalog():
    """
    TODO:

    """
    k = land.LdIntegration(logger=LOG)
    edx_course_catalog_url = "https://lms-lexoxabvtc99-tm.trafficmanager.net/api/courses/v1/courses/"
    key_vault_url = "https://manikeyvault3.vault.azure.net"
    key_vault_resource = "https://vault.azure.net"
    key_vault_headers = dict(MetaData='true')
    edx_api_key = k.get_key_vault_secret(k.get_access_token(key_vault_resource,key_vault_url,key_vault_headers), key_vault_url,'edx-api-key')
    edx_access_token = k.get_key_vault_secret(k.get_access_token(key_vault_resource,key_vault_url,key_vault_headers), key_vault_url,'edx-access-token')
    edx_headers = dict(Authorization='Bearer' + edx_access_token, X_API_KEY=edx_api_key)
    print(k.get_course_catalog_data(edx_course_catalog_url,edx_headers))

if __name__ == "__main__":
    sync_course_catalog()
