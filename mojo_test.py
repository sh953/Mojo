#!/usr/bin/env python3

import json
import urllib.parse as urlparse
from collections import defaultdict

import cv2
import numpy as np
import requests as rq

# Global params
key_id = "KEY-ATN563405-456"
key_value = "e8311505a2d3a6d2156152e206839910"
header = {'Content-Type': 'application/json', 'Accept-Encoding': 'gzip'}

# API URLs
dashboard_url = "https://dashboard.mojonetworks.com/rest/api/v2"
service_url = "/services"
webservice_url = "/new/webservice"
webservice_version_url = "/v3"
mwm_login_url = "/login/key/api-client/3600?getClusterChildrenData=true"
mwm_devices_url = "/devices"
fetch_client_paginated_url = "/clients/0/1"
fetch_image_url = "/sfiles"
fetch_placement_url = "/layouts/placement"
fetch_layout_url = "/layouts?locationid=%s"

ans = []
names = []
sigs = []

# Login to Mojo Launchpad
auth_url = "/kvs/login"
auth_r = rq.request(method="get", url=dashboard_url + auth_url, params={"key_id"         : key_id,
                                                                        "key_value"      : key_value,
                                                                        "session_timeout": 60})
if auth_r.status_code != 200:
    print("Authentication Failed")
    exit(0)

# Fetch service URL
service_r = rq.get(url=dashboard_url + service_url, params={"type": "amc"}, cookies=auth_r.cookies, headers=header)

if service_r.status_code == 200:
    service_json = json.loads(service_r.text)
    if "wireless".lower() in (service_json["data"]["customerServices"][0]["customer_service_name"]).lower():
        mwm_url = service_json["data"]["customerServices"][0]["service"]["service_url"]
    else:
        print("MWM URL Not Found")
else:
    print("MWM URL Fetch Failed")
    exit(0)

# Login to Mojo Wireless Manager
mwm_payload = {'type': 'apikeycredentials', 'keyId': key_id, 'keyValue': key_value}
mwm_auth_r = rq.post(url=mwm_url + webservice_url + mwm_login_url, json=mwm_payload, headers=header,
                     cookies=auth_r.cookies)
mwm_cookies = None
if mwm_auth_r.status_code == 200:
    mwm_cookies = mwm_auth_r.cookies
else:
    print("MWM Login Failed")
    exit(0)

# Fetch client by username
search_filter = {
    "property": "username",
    "value"   : ["nspring"],
    "operator": "="
}
fetch_client_url_parsed = mwm_url + webservice_url + webservice_version_url + mwm_devices_url + \
                          fetch_client_paginated_url + "?filter=" + \
                          urlparse.quote(json.dumps(search_filter))

fetch_client_r = rq.request(method="get", url=fetch_client_url_parsed, cookies=mwm_cookies, headers=header)
client_box_id = None
if fetch_client_r.status_code == 200:
    client_json = json.loads(fetch_client_r.text)
    client_box_id = client_json["clientList"][0]["boxId"]
    client_name = client_json["clientList"][0]["name"]
else:
    print("Search Failed")
    exit(0)

# Fetch observing devices from client ID
if client_box_id is not None:
    fetch_observing_devices_url = ("/clients/%s/observingmanageddevices" % str(client_box_id))
    fetch_observing_devices_url_parsed = mwm_url + webservice_url + webservice_version_url + mwm_devices_url + \
                                         fetch_observing_devices_url
    fetch_observing_devices_r = rq.request(method="get", url=fetch_observing_devices_url_parsed, cookies=mwm_cookies,
                                           headers=header)
    observing_device_list = defaultdict(int)
    if fetch_observing_devices_r.status_code == 200:
        observing_devices_json = json.loads(fetch_observing_devices_r.text)
        for i in range(len(observing_devices_json)):
            device_name = observing_devices_json[i]["name"]
            device_box_id = observing_devices_json[i]["boxId"]
            device_signal_strength = observing_devices_json[i]["signalStrength"]
            #if "RM4" in device_name or "HW4" in device_name:
            observing_device_list[device_box_id] = device_signal_strength
            if "AVW4" in device_name:
                names.append(device_name[3:7])
                sigs.append(device_signal_strength)
            ans.append(("[Device: %s] [Box ID: %02d] [Signal Strength: %d]") % (device_name,
                                                                                device_box_id,
                                                                                device_signal_strength))
    else:
        print("Failed")
else:
    exit(0)

names = names[0:3]
sigs = sigs[0:3]

print(names)
print(sigs)