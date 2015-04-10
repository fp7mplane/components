
# mPlane Protocol Reference Implementation
# Fastping probe component code
#
# (c) 2013-2014 mPlane Consortium (http://www.ict-mplane.eu)
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
import os
import time

_fastPingCmd=os.getcwd()+"/fastpingBash/FastpingBash.py" #change it
_fastPingopt_deltaM="-d"
_fastPingopt_freqPing="-f" #check if in the code it's really frequency or period
_fastPingopt_numberCycle="-n"
_fastPingopt_targetList="-t"
_fastPingopt_saveRW="-R"
_fastPingopt_saveQD="-Q"
_fastPingopt_saveSM="-C"
_fastPingopt_saveST="-S"
_fastPingopt_Upload="-U"

LOOP4 = "127.0.0.1"

#OUTPUT
 
def _parse_fastping_line(line):
    
    if line.startswith("result:"):
        return line.replace("result: ","",1).replace("\n","")
    elif line.startswith("Time:"):
         return line.replace("Time: ","",1).replace("\n","")

    print(line)
    return None

def _fastPing_process(progname, sipaddr, dipaddr,duration=None, period=None, numberCycle=None,upload=None):
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
    cap = mplane.model.Capability(label="Full fastping", when = "now ... future / 1s") #check
    cap.add_parameter("source.ip4",ipaddr)
    cap.add_parameter("destinations.ipv4range") #listIp
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

def fastPing_aggregate_mplane_capability(ipaddr):
    cap = mplane.model.Capability(label="Mplane Fastping", when = "now ... future / 1s") #check
    cap.add_parameter("source.ip4",ipaddr)
    cap.add_parameter("destination.ip4")
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

class FastPingService(mplane.scheduler.Service):
    def __init__(self, cap):
        # verify the capability is acceptable
        #IMPROVE THIS FUNCTION FOR ALL OPTIONAL PARAMETERS
        if not (cap.has_parameter("source.ip4") and
                (cap.has_parameter("destinations.ipv4range") or cap.has_parameter("destination.ip4"))  and
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
        if spec.has_parameter("destination.ip4"):
            dipaddr = str(spec.get_parameter_value("destination.ip4"))
        else:
            dipaddr = spec.get_parameter_value("destinations.ipv4range")
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
        res = mplane.model.Result(specification=spec)
        # put actual start and end time into result
        res.set_when(mplane.model.When(a= datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S.%f") ,b=datetime.strptime(result[-1], "%Y-%m-%d %H:%M:%S.%f")))
        res.set_result_value("file.list",",".join(result[1:-1]))            
                  
        return res        


def parse_args():
    global args
    parser = argparse.ArgumentParser(description="Run an mPlane ping probe server")
    parser.add_argument('--ip4addr', '-4', metavar="source-v4-address",
                        help="Ping from the given IPv4 address")
    parser.add_argument('--ip6addr', '-6', metavar="source-v6-address",
                        help="Ping from the given IPv6 address")
    parser.add_argument('--sec', metavar="security-on-off",
                        help="Toggle security on/off. Values: 0=on,1=off")
    parser.add_argument('--certfile', metavar="cert-file-location",
                        help="Location of the configuration file for certificates")
    args = parser.parse_args()


# For right now, start a Tornado-based ping server
if __name__ == "__main__":
    global args

    mplane.model.initialize_registry()
    parse_args()
    
    ip4addr = None
    ip6addr = None
    
    if args.ip4addr:
        ip4addr = ip_address(args.ip4addr)
        if ip4addr.version != 4:
            raise ValueError("invalid IPv4 address")
    if args.ip6addr:
        ip6addr = ip_address(args.ip6addr)
        if ip6addr.version != 6:
            raise ValueError("invalid IPv6 address")
    if ip4addr is None and ip6addr is None:
        raise ValueError("need at least one source address to run")
    if args.sec is None:
        raise ValueError("need --sec parameter (0=True,1=False)")
    else:
        if args.sec == '0':
            if args.certfile is None:
                raise ValueError("if --sec=0, need to specify cert file")
            else:
                security = True
                mplane.utils.check_file(args.certfile)
                certfile = args.certfile
        else:
            security = False
            certfile = None

    scheduler = mplane.scheduler.Scheduler(security)
    if ip4addr is not None:
         scheduler.add_service(FastPingService(fastPing_aggregate_capability(ip4addr)))
         scheduler.add_service(FastPingService(fastPing_aggregate_mplane_capability(ip4addr)))
    if ip6addr is not None:
         scheduler.add_service(FastPingService(fastPing_aggregate_capability(ip6addr)))        
    mplane.httpsrv.runloop(scheduler, security, certfile)















