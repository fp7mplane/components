
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
import subprocess
import collections
from datetime import datetime
import mplane.model
import mplane.scheduler
import pprint
import json
from datetime import datetime, timedelta
from ipaddress import ip_address
from pymongo import MongoClient



def services(settings_fileName):
    # the parameter is passed to this function by component-py, 
    # that reads it from the [module_exampleServiceName] section 
    # in the config file
    #TODO: read the settings JSON from parameters.
    with open(settings_fileName) as data_file:    
        mongoSettings = json.load(data_file)

    devices = getAvailableDevicesFromDB(mongoSettings)
    services = []
    for service in mongoSettings['measurements']:
        services.append(mongo(mongo_singleton_capability(devices, service, mongoSettings), mongoSettings))
    return services

def get_value_dot_notation(input_dict, accessor_string):
    """Gets data from a dictionary using a dotted accessor-string"""
    try:
        current_data = input_dict
        for chunk in accessor_string.split('.'):
            current_data = current_data.get(chunk, None)
        return current_data
    except:
        return None



def getAvailableDevicesFromDB(mongoSettings):
    """
    Gets the set of devices that are available in the mobileProbe DB. 
    This will be used to populate the "source" field.
    """
    client = MongoClient()
    db = client[mongoSettings['db']]
    source_field = mongoSettings['source_filed']
    devices = db[mongoSettings['collection']].distinct(source_field)
    #devices.remove(None)
    parsed = ",".join(devices)
    #print (parsed)
    return parsed


def getMeasurementFromDB(mongoSettings, fromTs, toTs, device, filterQ = None, collection="mobileMeasurements"):
    """
    Get measurements from the db. 
     Args:
           fromTs (date): The timestamp to search fromTs
           toTs (date): The timestamp to search to
           device (string): The device ID to search for (used in the source field of the spec)
           collection (string): The collection to use
     Returns:
           (Cursor): MongoDB cursor with the results. The cursor only includes the time and the column requested.
           The cursor is empty if no results are found.       
    """
    # Init
    
    db_name = mongoSettings['db']
    timestamp_field = mongoSettings['timestamp_field']
    source_field = mongoSettings['source_filed']

    results = []
    client = MongoClient()
    db = client[db_name]

    #query to run
    query = {}
    query[source_field] = device 
    query[timestamp_field] = {"$gte": fromTs, "$lte": toTs}; # Temporal Scope
    if filterQ != None:
        query[filterQ] = { "$exists": True }

    #perform the query, sort by timestamp
    cursor = db[collection].find(query).sort(timestamp_field , 1 )


    return cursor



def mongo_singleton_capability(devices, capability, settings):
    """
    Spec to retreive connected sectors for a device
    """
    print ("Initializing capability: " + capability)
    cap = mplane.model.Capability(label= capability, when = "past ... now", verb = "query")
    cap.add_metadata("System_version", "1.0")
    cap.add_parameter("source.device", devices)

    for result in settings["measurements"][capability]["return"]:
        cap.add_result_column(result)
    #cap.add_result_column("intermediate.link")
    return cap


class mongo(mplane.scheduler.Service):
    def __init__(self, cap, mongoSettings):
        # ToDo: verify the capability is acceptable
        super(mongo, self).__init__(cap)
        print ("INIT SERIVICE")

    
    def run(self, spec, check_interrupt):
        # Got a request to retreive measurements. 
        # Get the request parameters
        period = spec.when().datetimes()
        fromTs = period[0]
        toTs = period[1]
        device = spec.get_parameter_value("source.device")
        res = mplane.model.Result(specification=spec)

        # put the data
        specType = spec.get_label()
        # Ignore the ending number
        specType = specType[:-2]

        #check if we have settings for this specification
        if specType not in mongoSettings['measurements']:
            print("WARNING COULD NOT FIND SPECIFICATION: ", specType)
            res.set_when(mplane.model.When(a = period[0], b = period[1]))
            return res

        spec_settings = mongoSettings['measurements'][specType]
        collection = spec_settings['collection']
        filter_query = spec_settings['search']
  
        # Get the data
        results = getMeasurementFromDB(mongoSettings, fromTs, toTs, device, filter_query, collection)

        # iF there are no Results in the db... 
        if results == None or results.count() == 0:
            # We set the same temporal scope as the query
            res.set_when(mplane.model.When(a = period[0], b = period[1]))
            return res

        # put actual start and end time into result
        numberOfMeasurements = results.count()
        startTime = results[0]["date"]
        endTime = results[numberOfMeasurements - 1 ]["date"]
        res.set_when(mplane.model.When(a = startTime, b = endTime))


        # RETURN VALUES
        for i in range(0,  results.count()):
            result = results[i]
            for mplane_column, mongo_column in spec_settings['return'].items():
                value = get_value_dot_notation(result, mongo_column) #get data from Mongo
                res.set_result_value(mplane_column, value, i) #add them to mPlane
        return res