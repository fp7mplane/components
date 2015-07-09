# (c) 2013-2014 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Danilo Cicalese 
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
Implements anycast geolocation for integration into 
the mPlane reference implementation.

"""

from datetime import datetime
import mplane.model
import mplane.scheduler
from mplane.components.anycast_mod.anycast import Anycast
import os

anycast_data=os.getcwd()+"/mplane/components/anycast_mod/anycast_census.csv"

def services(ip4addr = None):
    services = []
    if ip4addr is not None:
        services.append(AnycastService(anycast_detection(ip4addr)))
        services.append(AnycastService(anycast_enumeration(ip4addr)))
        services.append(AnycastService(anycast_geolocation(ip4addr)))
    return services


def anycast_detection(ipaddr):
    cap = mplane.model.Capability(label="anycast-detection-ip4", when="now")
    cap.add_parameter("source.ip4",ipaddr)
    cap.add_parameter("destination.ip4") #listIp
    cap.add_result_column("anycast") 

    return cap
       
def anycast_enumeration(ipaddr):
    cap = mplane.model.Capability(label="anycast-enumeration-ip4", when="now")
    cap.add_parameter("source.ip4",ipaddr)
    cap.add_parameter("destination.ip4") #listIp
    cap.add_result_column("anycast") 
    cap.add_result_column("anycast_enumeration")

    return cap

def anycast_geolocation(ipaddr):
    cap = mplane.model.Capability(label="anycast-geolocation-ip4", when="now")
    cap.add_parameter("source.ip4",ipaddr)
    cap.add_parameter("destination.ip4") #listIp
    cap.add_result_column("anycast") 
    cap.add_result_column("anycast_geolocation")

    return cap

class AnycastService(mplane.scheduler.Service):
    
    def __init__(self, cap):
        
        if not cap.has_parameter("source.ip4"):
            raise ValueError("capability not acceptable")
        super(AnycastService, self).__init__(cap)

    def run(self, spec, check_interrupt):
        """
        Execute this Service
        
        """
        dipaddr = spec.get_parameter_value("destination.ip4")
        ip24=".".join(str(dipaddr).split(".")[:3])+".0"
        anycast=Anycast(anycast_data)
        start_time = str(datetime.utcnow())
        if "anycast-detection-ip4" in spec.get_label():
            result=anycast.detection(ip24) 
        elif "anycast-enumeration-ip4" in spec.get_label():
            result=anycast.enumeration(ip24)
        elif "anycast-geolocation-ip4" in spec.get_label():
            result=anycast.geolocation(ip24)
        end_time = str(datetime.utcnow())

        # derive a result from the specification
        res = mplane.model.Result(specification=spec)

        # put actual start and end time into result
        res.set_when(mplane.model.When(start_time, end_time))

        if result:
            res.set_result_value("anycast",True)
            if res.has_result_column("anycast_enumeration"):
                res.set_result_value("anycast_enumeration", result)

            if res.has_result_column("anycast_geolocation"):
                res.set_result_value("anycast_geolocation", result)
        else:
           res.set_result_value("anycast",False)

        return res
