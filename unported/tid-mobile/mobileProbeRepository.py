
# mPlane Protocol Reference Implementation
# TID mplane mobile probe access
#
# (c) 2013-2014 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Ilias Leontiadis <ilias@tid.es>
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

"""
Implements functionality to read data from TIDs mobile probe repository

"""

import re
import ipaddress
import threading
import subprocess
import collections
from datetime import datetime, timedelta
from ipaddress import ip_address
import mplane.model
import mplane.scheduler
import mplane.httpsrv
import tornado.web
import tornado.ioloop
import argparse
from pymongo import MongoClient



def getAvailableDevicesFromDB():
    """
    Gets the set of devices that are available in the mobileProbe DB. 
    This will be used to populate the "source" field.
    """
    client = MongoClient()
    db = client.mPlaneClient
    devices = db.cellInfo.distinct("properties.deviceID")
    devices.remove(None)
    parsed = ",".join(devices)
    #print (parsed)
    return parsed


def getMeasurementFromDB(fromTs, toTs, device, collection="cellInfo"):
    """
    Get measurements from the db. 
     Args:
           fromTs (date): The timestamp to search fromTs
           toTs (date): The timestamp to search to
           device (string): The device ID to search for (used in the source field of the spec)
           collection (string): The db to use
     Returns:
           (Cursor): MongoDB cursor with the results. The cursor only includes the time and the column requested.
           The cursor is empty if no results are found.       
    """
    # Init
    results = []
    client = MongoClient()
    db = client.mPlaneClient
    #query to run
    query = {}
    query["properties.deviceID"] = device 
    query["properties.date"] = {"$gte": fromTs, "$lte": toTs}; # Temporal Scope
    #perform the query, sort by timestamp
    cursor = db[collection].find(query).sort("properties.timeStamp" , 1 )
    #print ("FOUND ", cursor.count(), " measurements")

    return cursor



def connectionSector_singleton_capability(devices):
    """
    Spec to retreive connected sectors for a device
    """
    cap = mplane.model.Capability(label="connected-sector", when = "past ... now", verb = "query")
    cap.add_parameter("source.device", devices)
    cap.add_result_column("time")
    cap.add_result_column("intermediate.link")
    cap.add_result_column("snr")
    return cap


def connectionSectorLocation_singleton_capability(devices):
    """
    Spec to retreive connected sectors for a device
    """
    cap = mplane.model.Capability(label="connected-sector-location", when = "past ... now", verb = "query")
    cap.add_parameter("source.device", devices)
    cap.add_result_column("time")
    cap.add_result_column("intermediate.link")
    cap.add_result_column("snr")
    cap.add_result_column("source.location")
    return cap




class MobileProbeService(mplane.scheduler.Service):
    def __init__(self, cap):
        # ToDo: verify the capability is acceptable
        super(MobileProbeService, self).__init__(cap)
        print ("INIT SERIVICE")

    def run(self, spec, check_interrupt):
        # Got a request to retreive measurements. 
        # Get the request parameters
        period = spec.when().datetimes()
        fromTs = period[0]
        toTs = period[1]
        device = spec.get_parameter_value("source.device")
        
        # Get the data
        results = getMeasurementFromDB(fromTs, toTs, device)
        # Put the results into the specification reply msg
        res = mplane.model.Result(specification=spec)

        # iF there are no Results in the db... 
        if results == None or results.count() == 0:
            # We set the same temporal scope as the query
            res.set_when(mplane.model.When(a = period[0], b = period[1]))
            return res

        # put actual start and end time into result
        #fixme: null/empty results.
        numberOfMeasurements = results.count()
        startTime = results[0]["properties"]["date"]
        endTime = results[numberOfMeasurements - 1 ]["properties"]["date"]
        res.set_when(mplane.model.When(a = startTime, b = endTime))

        #put the data
        specType = spec.get_label()
        print("SPEC: ", specType)

        # Depending on the specification, fill in the reply!
        if specType == "connected-sector":
            for i in range(0,  results.count()):
                result = results[i]
                date = result["properties"]["date"]
                value = result["properties"]["currentCellLocation"]
                snr = result["properties"]["latestGSMSignalStrength"]
                res.set_result_value("time", date, i)
                res.set_result_value("intermediate.link", value, i)
                res.set_result_value("snr", snr, i)
        elif specType == "connected-sector-location":
            for i in range(0,  results.count()):
                result = results[i]
                date = result["properties"]["date"]
                value = result["properties"]["currentCellLocation"]
                snr = result["properties"]["latestGSMSignalStrength"]
                location = (result["properties"]["loc_latitude"], result["properties"]["loc_longitude"])
                res.set_result_value("time", date, i)
                res.set_result_value("intermediate.link", value, i)
                res.set_result_value("snr", snr, i)
                res.set_result_value("source.location", location, i)
        return res


def manually_test_capability():
    print ("TESTING : connectionSector_singleton_capability")
    devices = getAvailableDevicesFromDB()
    svc = MobileProbeService(connectionSector_singleton_capability(devices))
    spec = mplane.model.Specification(capability=svc.capability())
    spec.set_parameter_value("source.device", "353918050540026")
    spec.set_when("2013-09-20 ... 2013-10-5")
    res = svc.run(spec, lambda: False)
    print(repr(res))
    print(mplane.model.unparse_yaml(res))

    print ("TESTING : connectionSectorLocation_singleton_capability")
    svc = MobileProbeService(connectionSectorLocation_singleton_capability(devices))
    spec = mplane.model.Specification(capability=svc.capability())
    spec.set_parameter_value("source.device", "353918050540026")
    spec.set_when("2013-09-20 ... 2013-10-5")
    res = svc.run(spec, lambda: False)
    print(repr(res))
    print(mplane.model.unparse_yaml(res))


# For right now, start a Tornado-based ping server
if __name__ == "__main__":
    global args

    #initialize the registry
    mplane.model.initialize_registry()

    #MANUAL TEST (DISABLE NORMALY)
    manually_test_capability()
    exit()

    #create the scheduler 
    scheduler = mplane.scheduler.Scheduler()
    #get devices 
    devices = getAvailableDevicesFromDB()
    #add all the capabilities
    scheduler.add_service(MobileProbeService(connectionSector_singleton_capability(devices)))
    scheduler.add_service(MobileProbeService(connectionSectorLocation_singleton_capability(devices)))
    #run the scheduler 
    mplane.httpsrv.runloop(scheduler)
