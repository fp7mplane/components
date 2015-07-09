#
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
# mPlane Protocol Reference Implementation
# OTT probe component code for component-initiated workflow
#               Author: Janos Bartok-Nagy <janos.bartok-nagy@netvisor.hu>
#
# Based on: ICMP Ping probe component code
# (c) 2013-2014 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Gabor Molnar <gabor.molnar@netvisor.hu>
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
Implements OTT probe for integration into 
the mPlane reference implementation.

TODO:
 * currently one count is supported

"""

import argparse
import configparser
import collections
from datetime import datetime, timedelta
from ipaddress import ip_address
import json
import os
import platform
import re
import subprocess
import threading
from time import sleep

import urllib3
from urllib3 import HTTPConnectionPool
from urllib3 import HTTPSConnectionPool

import mplane.tls
import mplane.model
import mplane.scheduler
import mplane.component # bnj:

import socket
import sys
import pprint   # bnj: just for diag

_ottopt_period = "--mplane"
_ottopt_url    = "--url"

IP4ADDR = '127.0.0.1'
SUPERVISOR_IP4  = 'localhost'
SUPERVISOR_PORT = 8888
DUMMY_DN = 'Dummy.Distinguished.Name'
REGISTRATION_PATH  = "register/capability"
SPECIFICATION_PATH = "show/specification"
RESULT_PATH        = "register/result"

caplist = ["bandwidth.nominal.kbps", "http.code.max", "http.redirectcount.max", "qos.manifest", "qos.content", "qos.aggregate", "qos.level"]

# urllib3.disable_warnings()

# this method is for starting the OTT measurement. probe-ott will return with a measurement JSON.
def _ott_process(period=None, url=None):
    ott_argv = ["probe-ott"]
    ott_argv += [ "--slot", "-1"]
    if period is not None:
        ott_argv += [_ottopt_period, str(int(period))]
    if url is not None:
        ott_argv += [_ottopt_url, str(url)]
    print("\n >>> " + str(datetime.now()) + ": running " + " ".join(ott_argv) + "\n")
    return subprocess.Popen(ott_argv, stdout=subprocess.PIPE)

    
def services(ip4addr = None, ip6addr = None):
    services = []
    if ip4addr is not None:
        services.append(OttService(ott_capability(ip4addr)))
    return services


# assemble offered parameters
def ott_capability(ipaddr):
    cap = mplane.model.Capability(label="ott-download", when = "now ... future / 10s")
    cap.add_parameter("source.ip4",ipaddr)
    cap.add_parameter("content.url")
    cap.add_result_column("time")
    for c in caplist:
        cap.add_result_column(c)
    return cap

    
# return 1 if the result is an "offered" parameter (see capability)
def contains_result(cap):
    for c in caplist:
        if cap.has_result_column(c):
            return 1
    return 0

    
# this inherited class implements the OTT service based on the mplane scheduler
# - gets parameters from probe-ott via _ott_process
# - sets the result YAML
class OttService(mplane.scheduler.Service):
    def __init__(self, cap):
        # verify the capability is acceptable
        if not ((cap.has_parameter("source.ip4")) and
                (cap.has_parameter("content.url")) and
                (contains_result(cap))):
            raise ValueError("capability not acceptable")
        super(OttService, self).__init__(cap)

    def run(self, spec, check_interrupt):
        # unpack parameters
      try:
        period = spec.when().period().total_seconds()

        if spec.has_parameter("content.url"):
            url = spec.get_parameter_value("content.url")
            ott_process = _ott_process(period, url)
        else:
            raise ValueError("Missing URL")
      
        # read output from ping
        jsonS = ""
        for line in ott_process.stdout:
            strLine = line.decode()
            if strLine is "}":
                jsonS += strLine
                break
            jsonS += strLine

        jsonO = json.loads(jsonS)
        e = str(datetime.now())
        s = str(datetime.now()-timedelta(seconds=period))

        # derive a result from the specification
        res = mplane.model.Result(specification=spec)
        #print(jsonS)

        # put actual start and end time into result
        errcode = [jsonO["manifestQos.Max"], jsonO["contentQos.Max"]]
        res.set_when(mplane.model.When( s, e))
        res.set_result_value("time", s)
        res.set_result_value("bandwidth.nominal.kbps", jsonO["nominalBitrate.Max"], 0)
        res.set_result_value("http.code.max", jsonO["httpCode.Max"], 0)
        res.set_result_value("http.redirectcount.max", jsonO["redirect.Max"], 0)
        res.set_result_value("qos.manifest", errcode[0], 0)
        res.set_result_value("qos.content", errcode[1], 0)
        res.set_result_value("qos.aggregate", min(errcode), 0)
        res.set_result_value("qos.level", jsonO["qualityIndex.Max"], 0)
        # print(res)
        return res
      except:
        print("Unexpected error in run:", sys.exc_info())
        raise


class OttProbe():
    """
    This class manages interactions with the supervisor:
    registration, specification retrievement, and return of results    
    """

    def __init__(self, config):
        """
        Initiates a OTT probe for component-initiated workflow. 
        Command line parameters ported to config file equivalents.  
        """

        self.config = config
        self.supervisorhost = None
        if "supervisorhost" in config["module_ott"]:
            self.supervisorhost = config["module_ott"]["supervisorhost"]
        self.supervisorhost = self.supervisorhost or SUPERVISOR_IP4
        
        self.supervisorport = None
        if "supervisorport" in config["module_ott"]:
            self.supervisorport = config["module_ott"]["supervisorport"]
        self.supervisorport = self.supervisorport or SUPERVISOR_PORT
        
        self.ip4addr = None
        if "ip4addr" in config["module_ott"]:
            self.ip4addr = config["module_ott"]["ip4addr"]
        self.ip4addr = self.ip4addr or IP4ADDR    
        print(">>> supervisor = " + self.supervisorhost + ":" + str(self.supervisorport) + ", ip4addr = "+ str(self.ip4addr) + "\n")
            
        tls_state = mplane.tls.TlsState(config)
        self.dn = self.get_dn( tls_state._keyfile, tls_state)
        self.forged_identity = mplane.tls.TlsState.extract_local_identity(tls_state, None)
        
        headers={"content-type": "application/x-mplane+json"}
        if tls_state._keyfile is None:
            if( self.forged_identity is not None ):
                headers={"content-type": "application/x-mplane+json","Forged-MPlane-Identity": self.forged_identity}
            self.pool = HTTPConnectionPool(self.supervisorhost, self.supervisorport, headers=headers)
        else:
            self.pool = HTTPSConnectionPool(self.supervisorhost, self.supervisorport, key_file=tls_state._keyfile, cert_file=tls_state._certfile, ca_certs=tls_state._cafile, headers=headers)

        self.scheduler = mplane.scheduler.Scheduler(self.config)
        if self.ip4addr is not None:
            self.scheduler.add_service(OttService(ott_capability(self.ip4addr)))
            # self.scheduler.add_service(OttService(cap(self.ip4addr)))

        
    def register_capabilities(self):
        print( ">>> register_capabilities(): register with supervisor at " + self.supervisorhost + ":" + str(self.supervisorport) )
        
        caps_list = ""
        for key in self.scheduler.capability_keys():
            cap = self.scheduler.capability_for_key(key)
            #if (self.scheduler.ac.check_azn(cap._label, self.dn)):
            if (self.scheduler.azn.check(cap, self.dn)):
                caps_list = caps_list + mplane.model.unparse_json(cap) + ","
        caps_list = "[" + caps_list[:-1].replace("\n","") + "]"
        
        print( ">>> register_capabilities(): caps_list = \n" + caps_list )

        if self.forged_identity is None:
            self.forged_identity = ""
        print( ">>> register_capabilities(): self.forged_identity = " + self.forged_identity )

        while True:
            try:
                # print(">>> register_capabilities(): urlopen with headers={content-type: application/x-mplane+json, Forged-MPlane-Identity: " + self.forged_identity + "})\n")
                res = self.pool.urlopen('POST', "/" + REGISTRATION_PATH, 
                    body=caps_list.encode("utf-8"), 
                    headers={"content-type": "application/x-mplane+json", "Forged-MPlane-Identity": self.forged_identity})
                
                if res.status == 200:
                    body = json.loads(res.data.decode("utf-8"))
                    print("\nCapability registration outcome:")
                    for key in body:
                        if body[key]['registered'] == "ok":
                            print(key + ": Ok")
                        else:
                            print(key + ": Failed (" + body[key]['reason'] + ")")
                    print("")
                else:
                    print("Error registering capabilities, Supervisor said: " + str(res.status) + " - " + res.data.decode("utf-8"))
                    exit(1)
                break
            except:
                print("Supervisor unreachable. Retrying connection in 5 seconds")
                sleep(5)
    

    def check_for_specs(self):
        """
        Poll the supervisor for specifications
        
        """
        url = "/" + SPECIFICATION_PATH
        
        # send a request for specifications
        res = self.pool.request('GET', url, headers={"Forged-MPlane-Identity": self.forged_identity})
        if res.status == 200:
            
            # specs retrieved: split them if there is more than one
            specs = mplane.utils.split_stmt_list(res.data.decode("utf-8"))
            for spec in specs:
                
                # hand spec to scheduler
                reply = self.scheduler.receive_message(self.dn, spec)
                # return error if spec is not authorized
                if isinstance(reply, mplane.model.Exception):
                    result_url = "/" + RESULT_PATH
                    # send result to the Supervisor
                    myheaders={}
                    if self.forged_identity is None:
                       myheaders={"content-type": "application/x-mplane+json"}
                    else:
                       myheaders={"content-type": "application/x-mplane+json", "Forged-MPlane-Identity": self.forged_identity}
                    res = self.pool.urlopen('POST', result_url, 
                            body=mplane.model.unparse_json(reply).encode("utf-8"), 
                            headers=myheaders)
                    return
                
                # enqueue job
                job = self.scheduler.job_for_message(reply)
                
                # launch a thread to monitor the status of the running measurement
                t = threading.Thread(target=self.return_results, args=[job])
                t.start()
                
        # not registered on supervisor, need to re-register
        elif res.status == 428:
            print("\nRe-registering capabilities with supervisor")
            self.register_to_supervisor()
        pass

        
    def return_results(self, job):
      """
      Monitors a job, and as soon as it is complete sends it to the Supervisor
        
      """
      try:
        url = "/" + RESULT_PATH
        reply = job.get_reply()
        
        # check if job is completed
        while job.finished() is not True:
            if job.failed():
              try:
                reply = job.get_reply()
                break
              except:
                print("Unexpected error in return_results job.get_reply():", sys.exc_info())
                raise
            sleep(1)
        if isinstance (reply, mplane.model.Receipt):
            reply = job.get_reply()
        
        # send result to the Supervisor
        res = self.pool.urlopen('POST', url, 
                body=mplane.model.unparse_json(reply).encode("utf-8") ) 

        # handle response
        if res.status == 200:
#            print("Result for " + reply.get_label() + " successfully returned!")
            print("Result successfully returned!")
        else:
            print("Error returning Result for " + reply.get_label())
            print("Supervisor said: " + str(res.status) + " - " + res.data.decode("utf-8"))
        pass
      except:
        print("Unexpected error in return_results:", sys.exc_info())
        raise
    
             
    def get_dn(self, security, tlsState):
    # def get_dn(self, security, cert):
        """
        Extracts the DN from the request object. 
        If SSL is disabled (ie no _keyfile supplied), returns a dummy DN
    
        """
        if security:
        # if security == True:
            self._tls = tlsState
            dn = self._tls._identity
            # dn = ""
            # for elem in cert.get('subject'):
                # if dn == "":
                    # dn = dn + str(elem[0][1])
                # else: 
                    # dn = dn + "." + str(elem[0][1])
        else:
            dn = DUMMY_DN
        # print ( ">>> get_dn(): dn = " + dn )
        return dn

        
    def process_args(self):
        global args
        global config   # bnj
        
        # Read the command line parameters
        parser = argparse.ArgumentParser(description="Run an OTT-probe")
        parser.add_argument('--ip4addr', '-4', metavar="source-v4-address",
                            help="Ping from the given IPv4 address")
        parser.add_argument('--disable-ssl', action='store_true', default=False, dest='DISABLE_SSL',
                            help='Disable secure communication')
        parser.add_argument('--config', metavar="config-file-location",
                            help="Location of the configuration file for certificates")
        parser.add_argument('--supervisorhost', metavar="supervisorhost",
                            help="IP or host name where supervisor runs (default: localhost)")
        parser.add_argument('--supervisorport', metavar="supervisorport",
                            help="port on which supervisor listens (default: 8888)")
        parser.add_argument('--forged-mplane-identity', metavar="forged_identity",
                            help="ID to use in non-secure mode instead of certificate's subject")
        args = parser.parse_args()
        
        # Read the configuration file
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(mplane.utils.search_path(args.config))
        #print("process_args(): config = " + str(config) + " self.config=" + str(self.config))
        print ("repr(config) = " + repr(config))
        
        self.forged_identity = args.forged_identity
        self.supervisorhost = args.supervisorhost or SUPERVISOR_IP4
        self.supervisorport = args.supervisorport or SUPERVISOR_PORT
        print ("process_args(): self.supervisorport = " + str(self.supervisorport) )
        
        self.ip4addr = None

        if args.ip4addr:
            self.ip4addr = ip_address(args.ip4addr)
            if self.ip4addr.version != 4:
                raise ValueError("invalid IPv4 address")
        if self.ip4addr is None :
             iplist = []
             [iplist.append(ip) for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1]
             print("Source address not defined. Lists of IPs found: " + ''.join(iplist) + " Using first: " + iplist[0])
             self.ip4addr = ip_address(iplist[0])
             if self.ip4addr.version != 4:
                raise ValueError("need at least one source address to run")
    
        if not args.DISABLE_SSL:
            if args.config is None:
                raise ValueError("without --disable-ssl, need to specify cert file")
            else:
                #print( "process_args(): pwd: " + os.getcwd() + " - cert config file: " + args.config )
                mplane.utils.check_file(args.config)
                # TODO: use search_path
                self.certfile = mplane.utils.normalize_path(mplane.utils.read_setting(args.config, "cert"))
                self.key = mplane.utils.normalize_path(mplane.utils.read_setting(args.config, "key"))
                self.ca = mplane.utils.normalize_path(mplane.utils.read_setting(args.config, "ca-chain"))
                mplane.utils.check_file(self.certfile)
                mplane.utils.check_file(self.key)
                mplane.utils.check_file(self.ca)
                print("process_args(): (2) self.certfile=" + self.certfile + " self.key=" + self.key + " self.ca=" + self.ca)
        else:
            self.certfile = None
            self.key = None
            self.ca = None
        


def manually_test_ott():
    svc = OttService(capability("127.0.0.1"))
    spec = mplane.model.Specification(capability=svc.capability())
    spec.set_parameter_value("source.ip4", "127.0.0.1")
    spec.set_parameter_value("content.url", "http://devimages.apple.com/iphone/samples/bipbop/bipbopall.m3u8")
    spec.set_when("now + 10s / 10s")

    res = svc.run(spec, lambda: False)
    print(repr(res))
    print(mplane.model.unparse_yaml(res))

    
# For right now, start a Tornado-based ping server
if __name__ == "__main__":
    if platform.system() != "Linux":
        print("Linux is supported only. Output lines of ping command won't probably be parsed correctly.")
        exit(2)

    parser = argparse.ArgumentParser(description="mPlane generic Supervisor")
    parser.add_argument('--config', metavar="config-file",
                        help="Configuration file")
    args = parser.parse_args()

    if not args.config:
        print('\nERROR: missing --config\n')
        parser.print_help()
        exit(1)

    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(mplane.utils.search_path(args.config))

    mplane.model.initialize_registry(config["component"]["registry_uri"])
    
    ottprobe = OttProbe(config)

    # uncomment this line for testing
    # manually_test_ott() 
    
    ottprobe.register_capabilities()

    while True:
        ottprobe.check_for_specs()
        sleep(5)
