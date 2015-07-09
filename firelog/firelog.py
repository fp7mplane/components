# mPlane Protocol Reference Implementation
# Firelog component code
#
# (c) 2013-2014 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Marco Milanesio
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

from datetime import datetime
from time import sleep
import mplane.model
import mplane.scheduler
import mplane.utils

import json
import sys
import configparser
from mplane.components.phantomprobe import phantomprobe as phtm

"""
Implements firelog capabilities and services

"""

def services(runtimeconf):
    services = []
    if runtimeconf is not None:
        services.append(firelogService(diagnose_capability(), mplane.utils.search_path(runtimeconf)))
    else:
        raise ValueError("missing runtimeconf parameter for firelog capabilities")
    return services
    
def diagnose_capability():
    cap = mplane.model.Capability(label="firelog-diagnose", when="now + 5m")
    cap.add_metadata("System_type", "firelog")
    cap.add_metadata("System_ID", "firelog-Proxy")
    cap.add_metadata("System_version", "0.1")
    cap.add_parameter("destination.url")
    cap.add_result_column("firelog.diagnose")
    return cap
           
class firelogService(mplane.scheduler.Service):
    """
    This class handles the capabilities exposed by the proxy:
    executes them, and fills the results
    
    """
    
    def __init__(self, cap, fileconf):
        super(firelogService, self).__init__(cap)
        self._fileconf = fileconf

    def run(self, spec, check_interrupt):
        """
        Execute this Service
        
        """
        if not spec.has_parameter("destination.url"):
            raise ValueError("Missing destination.url")
            
        start_time = datetime.utcnow()

        try:
            fp = phtm.PhantomProbe(self._fileconf, spec.get_parameter_value("destination.url"))
            fp.execute()
            firelog_result = fp.get_result()
        except Exception as e:
            firelog_result = {"Error": "Something bad happened"}
            print(e)

        end_time = datetime.utcnow()
        
        # fill result message 
        print("specification " + spec._label + ": start = " + str(start_time) + ", end = " + str(end_time))
        res = self.fill_res(spec, start_time, end_time, firelog_result)
        print
        return res


    def fill_res(self, spec, start, end, fres):
        """
        Create a Result statement, fill it and return it
        
        """
        # derive a result from the specification
        res = mplane.model.Result(specification=spec)
        # put actual start and end time into result
        res.set_when(mplane.model.When(a = start, b = end))
        res.set_result_value('firelog.diagnose', json.dumps(fres))
        return res
