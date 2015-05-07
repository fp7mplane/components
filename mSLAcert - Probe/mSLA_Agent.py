# mPlane Protocol Reference Implementation
# tStat component code
#
# (c) 2013-2014 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Edion TEGO
# mSLAcert-Agent-V-1.0.0
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
#-------------------------------------------------------------------------------
# Find proccess and kill it if you cannot bind port
# ps aux | grep -i iperf
# sudo kill proccess_ID
#

import threading
from datetime import datetime
from time import sleep
import time
import mplane.model
import mplane.scheduler
import mplane.utils
from urllib3 import HTTPSConnectionPool
from urllib3 import HTTPConnectionPool
from socket import socket
import ssl
import argparse
import sys
import re
import json
import subprocess
import collections
from datetime import datetime, timedelta
from ipaddress import ip_address
import tornado.web
import tornado.ioloop
from subprocess import Popen
import urllib3
urllib3.disable_warnings()

DEFAULT_IP4_NET = "192.168.1.0/24"
DEFAULT_SUPERVISOR_IP4 = '127.0.0.1'
DEFAULT_SUPERVISOR_PORT = 8888
REGISTRATION_PATH = "register/capability"
SPECIFICATION_PATH = "show/specification"
RESULT_PATH = "register/result"

DUMMY_DN = "Dummy.Distinguished.Name"

print("    ###########################################################################################################");
print("    ###$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$##");
print("    ###$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$     $$$$$$$$  $$$$$$       $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$##");
print("    ##$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$  $$$  $$$$$$  $$$$$  $$$$$  $$$$$$  $$$$$$$$$$$$$$    $$$$$$$$##");
print("    ##$$$$$$$$$$$$$      $$$$$$$$$$$$$$$$$$$$$  $$$$$  $$$$  $$$$  $$$$$$$  $$$$$        $$$$$$  $$$$  $$$$$$##");
print("    ##$$$$$$$$$$   ;$$$$   $$$$$$       $$$$$$  $$$$  $$$$$  $$$$$$$$$   $  $$$$$  $$$$$  $$$$  $$$$$  $$$$$$##");
print("    ##$$$$$$$$   $$$$$$$$  $$$$   $$$$$  $$$$$  $$  $$$$$$$  $$$$$$$  $$$$  $$$$$  $$$$$  $$$$        $$$$$$$##");
print("    ##$$$$$$   $$$$$$$$$$!      $$$$$$$   $$$$   $$$$$$$$$$  $$$$$  $$$$$$  $$$$$  $$$$$  $$$$  $$$$$$$$$$$$$##");
print("    ##$$$$   $$$$$$$$$$$$$$  $$$$$$$$$$$  $$$$  $$$$$$$$$$$  $$$$  $$$$$    $$$$$  $$$$$  $$$$  $$$$$  $$$$$$##");
print("    ##$$$  $$$$$$$$$$$$$$$$$$$$$$$$$$$$$  $$$$  $$$$$$$$$$$  $$$$$       $  $$$$$  $$$$$  $$$$$       $$$$$$$##");
print("    ###$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$##");
print("    ##$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$##");
print("    ###$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$##");
print("    ###$$$$$$$$_____________________&______________________&_____________&_______________$$$$$$$$$$$$$$$$$$$$##");
print("    ###$$$$$$$$$___| mSLAcert probe| TCP & UDP Agent verification and certification|_______$$$$$$$$$$$$$$$$$$##");
print("    ###########################################################################################################");


"""
Implements mSLA-Agent proxy for integration into 
the mPlane reference implementation.
(capability push, specification pull)

"""
commands = [
    'echo Starteded on	$(date)	-------------------->> ./results/mslaTCP.receive.client.txt',
    'iperf -s -p 5001 -i 1 -f k >> ./results/mslaTCP.receive.client.txt &',
    'pid5001=$!',
#    'echo Ended on	$date	------------------------------->> ./mslaTCP.receive.client.txt',
    'echo Starteded on	$(date)	-------------------->> ./results/mslaUDP.receive.client.txt',
    'iperf -s -u -p 5002 -i 1 -f  k >> ./results/mslaUDP.receive.client.txt &',
    'pid5002=$!',
    'ps aux | grep -i iperf',
#    'echo Ended on	$date	------------------------------->> ./mslaUDP.receive.client.txt',
]
# run in parallel and store locally the result
processes = [Popen(cmd, shell=True) for cmd in commands]

def sla_AGENT_capability(ip4addr):
    cap = mplane.model.Capability(label="msla-AGENT-Probe-ip4", when = "now ... future / 1s")
    cap.add_parameter("source.ip4",ip4addr)
    cap.add_parameter("destination.ip4")
    cap.add_result_column("mSLA.udpCapacity.download.iperf")
    return cap
    
def services(ip4addr = None):
    services = []
    if ip4addr is not None:
        services.append(mSLAcert_Agent_Service(sla_AGENT_capability(ip4addr)))
    return services
    
class mSLAcert_Agent_Service(mplane.scheduler.Service):
    def __init__(self, cap):
        # verify the capability is acceptable
        if not ((cap.has_parameter("source.ip4") or 
                 cap.has_parameter("source.ip6")) and
                (cap.has_parameter("destination.ip4") or 
                 cap.has_parameter("destination.ip6")) and
                (cap.has_result_column("mSLA.udpCapacity.download.iperf"))):
            raise ValueError("capability not acceptable")
        super(mSLAcert_Agent_Service, self).__init__(cap)

    def run(self, spec, check_interrupt):
         # unpack parameters
        period = spec.when().period().total_seconds()
        duration = spec.when().duration().total_seconds()
        if duration is not None and duration > 0:
            count = int(duration / period)
        else:
            count = None
        
        agent = []
        a = time.time()
        time.sleep(count)
        report_i_am_agent = -1001
        b = time.time()
        
        # derive a result from the specification
        res = mplane.model.Result(specification=spec)
        # put actual start and end time into result
        res.set_when(mplane.model.When(a , b))
        # are we returning aggregates or raw numbers?
        if res.has_result_column("mSLA.udpCapacity.download.iperf"):
                res.set_result_value("mSLA.udpCapacity.download.iperf", report_i_am_agent)
                #os.system("scp ./results/mslaTCP.receive.client.txt USER@Repository:/repository/temp/")
                #os.system("scp ./results/mslaUDP.receive.client.txt USER@Repository:/repository/temp/")
        return res
