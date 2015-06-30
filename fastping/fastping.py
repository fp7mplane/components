#
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
# mPlane Protocol Reference Implementation
# ICMP Ping probe component code
#
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
Implements Fastping for integration into 
the mPlane reference implementation.

"""

import re
import subprocess
import collections
from datetime import datetime
import mplane.model
import mplane.scheduler
import os

_fastPingCmd=os.getcwd()+"/mplane/components/fastpingBash/FastpingBash.py" #CHANGE it
_fastPingopt_deltaM="-d"
_fastPingopt_freqPing="-f" #check if in the code it's really frequency or period
_fastPingopt_numberCycle="-n"
_fastPingopt_targetList="-t"
_fastPingopt_saveRW="-R"
_fastPingopt_saveQD="-Q"
_fastPingopt_saveSM="-C"
_fastPingopt_saveST="-S"
_fastPingopt_Upload="-U"


def services(ip4addr = None):
    services = []
    if ip4addr is not None:
        services.append(FastPingService(fastPing_aggregate_capability(ip4addr)))
        #services.append(FastPingService(fastPing_aggregate_mplane_capability(ip4addr)))
    return services
    
def _parse_fastping_line(line):
    
    if line.startswith("result:"):
        return line.replace("result: ","",1).replace("\n","")
    elif line.startswith("Time:"):
         return line.replace("Time: ","",1).replace("\n","")
    elif line.startswith("Error:"):
         raise ValueError(line)

    print(line)
    return None


def _fastPing_process(progname, sipaddr, dipaddr, duration=None, period=None, numberCycle=None,upload=None):
    fastping_argv = [progname]

    fastping_argv = [progname]   
    fastping_argv +=[_fastPingopt_targetList,str(dipaddr)]
    if duration is not None:
        fastping_argv += [_fastPingopt_deltaM, str(int(duration))]
    if period is not None:
        fastping_argv += [_fastPingopt_freqPing, str(period)] 
    if numberCycle is not None:
        fastping_argv += [_fastPingopt_numberCycle, str(numberCycle)]

    fastping_argv +=[_fastPingopt_saveRW]
    fastping_argv +=[ _fastPingopt_saveSM]
    fastping_argv +=[_fastPingopt_saveST]
    fastping_argv +=[_fastPingopt_saveQD]    
    if upload[0] is not None:
        fastping_argv +=[_fastPingopt_Upload]+upload
        
    print("running " + " ".join(fastping_argv))
    
    return subprocess.Popen(fastping_argv, stdout=subprocess.PIPE)

def fastPing_aggregate_capability(ipaddr):
    cap = mplane.model.Capability(label="fastping-ip4", when = "now ... future / 1s")
    cap.add_parameter("source.ip4",ipaddr)
    cap.add_parameter("destinations.ip4") #listIp
    cap.add_parameter("cycleduration.s") #deltaM
    cap.add_parameter("period.s") #freqPing:1/period
    cap.add_parameter("numberCycle") #numberCycle: natural
    cap.add_parameter("ftp.ip4") 
    cap.add_parameter("ftp.user")
    cap.add_parameter("ftp.password")
    cap.add_parameter("ftp.port") 
    cap.add_parameter("ftp.currdir")
    cap.add_parameter("ftp.ispsv") 
    cap.add_result_column("file.list") 
    return cap

"""
def fastPing_aggregate_mplane_capability(ipaddr):
    cap = mplane.model.Capability(label="mplane-fastping-ip4", when = "now ... future / 1s")
    cap.add_parameter("source.ip4",ipaddr)
    cap.add_parameter("destinations.ip4")
    cap.add_parameter("cycleduration.s") #deltaM
    cap.add_parameter("period.s") #freqPing:1/period
    cap.add_parameter("numberCycle") #numberCycle: natural
    cap.add_parameter("ftp.ip4") #ftp_serverip
    cap.add_parameter("ftp.user")
    cap.add_parameter("ftp.password")
    cap.add_parameter("ftp.port") #ftp_serverip
    cap.add_parameter("ftp.currdir")
    cap.add_parameter("ftp.ispsv") #user    
    cap.add_result_column("file.list") 

    return cap
"""

class FastPingService(mplane.scheduler.Service):
    def __init__(self, cap):
        # verify the capability is acceptable
        #IMPROVE THIS FUNCTION FOR ALL OPTIONAL PARAMETERS
        if not (cap.has_parameter("source.ip4") and cap.has_parameter("destinations.ip4")  and
                cap.has_parameter("ftp.ip4") and #UPLOADER parameter 
                cap.has_parameter("ftp.user") and
                cap.has_parameter("ftp.password") and
                cap.has_parameter("ftp.port") and 
                cap.has_parameter("ftp.currdir") and
                cap.has_parameter("ftp.ispsv")):
                 
            raise ValueError("capability not acceptable")
        super(FastPingService, self).__init__(cap)

    def run(self, spec, check_interrupt):
        # unpack parameters
        sipaddr = spec.get_parameter_value("source.ip4")
        dipaddr = spec.get_parameter_value("destinations.ip4")
        duration = spec.when().duration().total_seconds()
        period = spec.when().period().total_seconds()
        ftp_server = spec.get_parameter_value("ftp.ip4")
        user       = spec.get_parameter_value("ftp.user")
        pwd        = spec.get_parameter_value("ftp.password")
        port       = spec.get_parameter_value("ftp.port")
        curr_dir   = spec.get_parameter_value("ftp.currdir")
        is_pasv    = spec.get_parameter_value("ftp.ispsv")
        numberCycle=spec.get_parameter_value("numberCycle")
        saveRW="True"
        saveQD="True"
        saveSM="True"
        saveST="True"
        ping_process = _fastPing_process(_fastPingCmd,sipaddr, dipaddr,duration, period, numberCycle,[ftp_server,user,pwd,str(port),curr_dir,str(is_pasv)])
        

        # read output from ping
        pings = []
        result= []    
        for line in ping_process.stdout:
            oneline = _parse_fastping_line(line.decode("utf-8"))
                 
            if oneline is not None:
                print("FastPing: "+ oneline)
                result.append(oneline)
                
 
     # shut down and reap
        try:
            ping_process.kill()
        except OSError:
            print ("error in killing")
            pass
        ping_process.wait()

        # derive a result from the specification

        # derive a result from the specification
        res = mplane.model.Result(specification=spec)
        # put actual start and end time into result
        res.set_when(mplane.model.When(a= datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S.%f") ,b=datetime.strptime(result[-1], "%Y-%m-%d %H:%M:%S.%f")))
        res.set_result_value("file.list",",".join(result[1:-1]))


        return res
