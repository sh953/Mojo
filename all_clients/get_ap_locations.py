"""
Compiled with python 3.5.2
This file runs various API calls for a cloud deployment
"""

from mwmApi import MwmApi
from mlpApi import MlpApi
import time
import sys

if len(sys.argv) < 2:
    print("usage: python3  _.py output_dir")
    sys.exit(1)

devices = {}
third_floor_id = 4
fourth_floor_id = 2

if __name__ == '__main__':

    # MLP Server API instance
    mlp_host = "dashboard.mojonetworks.com"

    # KVS Credentials
    kvs_auth_data = {
        "keyId" : "KEY-ATN563405-456",
        "keyValue" : "e8311505a2d3a6d2156152e206839910",
        #"keyId": "KEY-ATN59618-1",
        #"keyValue": "42ff84734541cbd98f674b02555330ef",
        "cname": "ATN563",
    }

    with MlpApi(mlp_host) as mlp_api:
        mlp_api.login(kvs_auth_data)
        mwm_service_hostname = mlp_api.get_mwm_service_url()
        print('mwm service hostname: %s'%mwm_service_hostname) 
        client = "api-client"       # Simple string parameter to identify your service to MWM
        login_timeout = str(5*60)  # seconds
        
    with MwmApi(mwm_service_hostname) as mwm_api:
        loginResponse = mwm_api.login(client, login_timeout, kvs_auth_data)
        print(loginResponse)
        # Get Clients
        clientResponse = mwm_api.get_clients()
        now = time.time()
        out = open('id_to_name_map.txt', 'w')
        for client in clientResponse:
            boxId = client["boxId"]
            # get observing APs
            observingAPs = mwm_api.get_observing_aps(boxId)
            if observingAPs is None:
                #print("No observing APs for device %s"%boxId)
                continue
            devices[boxId] = {}
            for ap in observingAPs:
                ap_id = ap['observingDevice']['boxId']
                ap_name = ap['observingDevice']['name']
                out.write('%s %s\n'%(ap_id, ap_name))
        out.close()




