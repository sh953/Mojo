#!/usr/bin/env python3
import operator
import json
import urllib.parse as urlparse
from collections import defaultdict
import cv2
import numpy as np
import requests as rq
import sys
from scipy.optimize import minimize
from datetime import datetime
import os
import datetime

out_dir = '/Users/katura/818g/images'

pixel_to_feet = 845.0 / 406

#Free Space Path Loss formula for distance
def dist(sig, freq=2412):
        return 10**((27.55-(20*np.log10(freq)) - sig)/20.0)
    
def mse(x, locations, distances):
        """
        Mean standard error to minimize
        We don't know x, we're going to solve for it below.
        """
        mse = 0.0
        for location, distance in zip(locations, distances):
            distance_calculated = np.sqrt( np.power(x[0]-location[0],2) +
                                           np.power(x[1]-location[1],2) )
            mse += np.power(distance_calculated - distance, 2.0)
        return mse / len(locations)

def main(rssi_in):
    timestamp = rssi_in.split('_')[-1].split('.')[0]

    apLocs = {}
    ap_loc_map = open('/Users/katura/818g/ap_coords.txt','r')
    for line in ap_loc_map.readlines():
        toks = line.split()
        apLocs[toks[0]] = (float(toks[2]), float(toks[3]))
     
    f3_raw = cv2.imread('/Users/katura/818g/avw3_full.jpeg',cv2.IMREAD_COLOR)
    f3 = cv2.resize(f3_raw, (845,605), None)
    f4 = cv2.imread('/Users/katura/818g/avw4_full.jpeg',cv2.IMREAD_COLOR)

    clients = {}
    f = open(rssi_in, 'r')
    for line in f.readlines():
        toks = line.split(',')
        if toks[1] == '19':
            continue
        if toks[0] not in clients:
            clients[toks[0]] = {toks[1]:int(toks[2])}
        else:
            clients[toks[0]][toks[1]] = int(toks[2])
    c = 0 
    for client, aps in clients.items():
        client_aps = sorted(aps.items(),key=operator.itemgetter(1))
        client_aps.reverse()
        if(len(client_aps) < 3):
            continue # we can't trianguate without 3 ...
        if client_aps[0][1] < -65: #too weak, bad location
            continue
        
        l = min(4, len(client_aps))
        client_aps = client_aps[0:l]
        c += 1
        if int(client_aps[0][0]) in [12,19,28,14,7,25,16,17,18,20,15]:
            img = f3
        else:
            img = f4
        
        locs = []

        for i in client_aps:
            locs.append((float(apLocs[i[0]][0]), float(apLocs[i[0]][1])))


        Ls = locs
        Ds = [dist(s[1]) for s in client_aps]

        # initial_location: (lat, long)
        # locations: [ (lat1, long1), ... ]
        # distances: [ distance1,     ... ]

        #initial guess to start minmization = average of beacon positions
        initial_location = [np.mean([locs[0][0],locs[1][0],locs[2][0]]),
                            np.mean([locs[0][1],locs[1][1],locs[2][1]])]
        locations = Ls
        distances = Ds

        result = minimize(
            mse,                         # The error function
            initial_location,            # The initial guess
            args=(locations, distances), # Additional parameters for mse
            method='BFGS',           # The optimisation algorithm
            options={
                #'ftol':1e-7,         # Tolerance
                'maxiter': 1e7      # Maximum iterations
            })
        location = result.x
        cv2.circle(img, (int(location[0] * pixel_to_feet),
            int(location[1]* pixel_to_feet)),
            radius=2, color=(0, 0, 255),
                       thickness=5)
    v_concat = np.concatenate((f3,f4), axis=0)
    date_str = datetime.datetime.fromtimestamp(
        int(timestamp)).strftime('%m-%d %H:%M')
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(v_concat, date_str,(300,50), font, 1,(0,0,0),2,cv2.LINE_AA)
    cv2.imwrite('avw_%s.jpg'%(timestamp), v_concat)
    print(c)

if __name__ == "__main__":
    for file in os.listdir(sys.argv[1]):
        print(file)
        main(os.path.join(sys.argv[1], file))
