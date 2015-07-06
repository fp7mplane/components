# (c) 2013-2014 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Ali Safari Khatouni
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.
#

from datetime import datetime, timedelta
from time import sleep, time, mktime
import mplane.model
import mplane.utils


from socket import socket
import sys

import multiprocessing
from os import listdir
from os.path import isfile, join

import json
import rrdtool
from dateutil import tz


DEFAULT_RRD_INTERVAL = 300
RESULT_PATH_INDIRECT = "register/result/indirect_export"


"""
Hint:

In the rrd export we assume that each recieving time expressed in UTC timezone (according to mplane time format)
before fetching the data we chnage the utc time to the machine local timezone


"""

def change_to_local_tzone(start_zone):

    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()
    start_utc = start_zone.replace(tzinfo=from_zone)
    start_local = start_utc.astimezone(to_zone)

    return start_local

def connect_to_repository(self, tls, repository_ip4, repository_port):
    """
    connect to repository for Indirect export RRD files
    repository address extract from the specification parameters
    it can support HTTPS and HTTP  

    """
    self.repo_pool = tls.pool_for(None, host=repository_ip4, port=repository_port)
    return

def indirect_export(self, tls, path, spec, start,interval):
    """
    
    Indirect Export the RRD metrics to repository
    first connect then fetch finally send result to Repository
    it runs until the process stops

    """
    repository_ip = str(spec.get_parameter_value("repository.url").split(":")[-2])
    repository_port = int(spec.get_parameter_value("repository.url").split(":")[-1])

    connect_to_repository(self, tls, repository_ip, repository_port)
    last_fetched_time = 0

    # change the time expressed in UTC to local timezone    
    start_local = change_to_local_tzone(start)

    print ("local start time :" + str(start_local))
    print ("UTC start time :" + str(start))

    while True:

        # fetch RRD files till the process killed by the function -> change_conf_indirect_export
        result_list = []
        if(last_fetched_time == 0):
            #convert timedate fprmat to time format
            start_time_local = int(mktime(start_local.timetuple()))
            startTime = str (start_time_local - interval )

        else:
            startTime = str(last_fetched_time)


        endTime = str (int(time()))
        rrd_files = [ f for f in listdir(path) if isfile(join(path,f)) and (".rrd" in f) ]

        for f in rrd_files :
            rrdMetric = rrdtool.fetch( (path  + f),  "AVERAGE" ,'--resolution', str(interval), '-s', startTime, '-e', endTime)

            rrd_time = rrdMetric[0][0]

            for tuple in rrdMetric[2]:
                if tuple[0] is not None:

                    rrd_time = rrd_time + interval
                    timestamp = float(rrd_time)
                    value = float(tuple[0])
                    metric = f
                    
                    if (rrd_time > last_fetched_time):
                        last_fetched_time = int(rrd_time)

                    result_list.append((metric,timestamp,value))
            
        print ("result list size :    " + str(len (result_list)))

        if len(result_list) > 0:
            return_results_to_repository(self, result_list)

        sleep(interval)

def return_results_to_repository(self, res):
    """
    It returns the fetched data with POST to
    repository proxy    

    """


    url = "/" + RESULT_PATH_INDIRECT

    # send result to the Repository
    
    rec_res = self.repo_pool.urlopen('POST', url, 
    body=json.dumps(res).encode("utf-8"), 
    headers={"content-type": "application/json"})
            
    # handle response
    if rec_res.status == 200:
        print("RRD logs successfully returned!")
    else:
        print("Error returning Result for " )
        print("Repository said: " + str(rec_res.status) + " - " + rec_res.data.decode("utf-8"))
    pass 



def run(self, config, path, spec, start):

    """
    The actual Indirect RRD Export execute here 
    with creating a new process here  

    """

    tls = mplane.tls.TlsState(config)

    global proc 
    proc = multiprocessing.Process(target=indirect_export, args=[self, tls, path, spec, start, DEFAULT_RRD_INTERVAL])
    proc.deamon = True
    print("tstat-exporter_rrd Enabled \n")
    proc.start()
    return proc
