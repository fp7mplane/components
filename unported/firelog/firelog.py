
# mPlane Protocol Reference Implementation
# Firelog probe component code
#
# (c) 2013-2014 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Marco Milanesio <marco.milanesio@eurecom.fr>
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
Implements Firelog on the mPlane reference implementation.

"""

import threading
from datetime import datetime
from time import sleep
import mplane.model
import mplane.scheduler
import mplane.utils
import mplane.tstat_caps
from urllib3 import HTTPSConnectionPool
from urllib3 import HTTPConnectionPool
from socket import socket
import ssl
import argparse
import sys
import re
import json

DEFAULT_IP4_NET = "192.168.1.0/24"
DEFAULT_SUPERVISOR_IP4 = '127.0.0.1'
DEFAULT_SUPERVISOR_PORT = 8888
REGISTRATION_PATH = "register/capability"
SPECIFICATION_PATH = "show/specification"
RESULT_PATH = "register/result"

DUMMY_DN = "Dummy.Distinguished.Name"


def services(url):
    services = []
    if url is not None:
        services.append(FirelogService(firelog_capability(url)))
    return services
    
def _firelog_process(url):
    cmd = ''
    return subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE)
    
def firelog_capability(url):
    cap = mplane.model.Capability(label="firelog-diagnosis", when = "now + inf ... future")
    cap.add_parameter("destination.url", "default")
    cap.add_result_column("firelog.diagnosis")
    return cap

class FirelogService(mplane.scheduler.Service):
    
    def __init__(self, cap):
        # verify the capability is acceptable
        #if not (cap.has_parameter("source.ip4") and
        if not cap.has_parameter("destination.url"):
            raise ValueError("capability not acceptable")
        super(FirelogService, self).__init__(cap)
        self._starttime = datetime.utcnow()
        
    def run(self, spec, check_interrupt):
        if not spec.has_parameter("destination.url"):
            #with open(args.CONFFILE, 'r') as i:
            #    urllist = ['www.google.com']
            raise ValueError("Missing url")
            
        
        firelog_process = None

        def target():
            #self._sipaddr = spec.get_parameter_value("source.ip4")
            url = spec.get_parameter_value("destination.url")
            firelog_process = _firelog_process(url)
            
        t = threading.Thread(target=target)
        t.start()
        out, err = t.join()
        if t.is_alive():
            firelog_process.terminate()
            out, err = t.join()
        
        # derive a result from the specification
        res = mplane.model.Result(specification=spec)

        # put actual start and end time into result
        now = datetime.utcnow()
        res.set_when(mplane.model.When(a = self._starttime, b = now))
        
        res.set_result_value("firelog.diagnosis", out)

        return res


def parse_args():
    global args
    parser = argparse.ArgumentParser(description="Run firelog probe server")
    parser.add_argument('--url', '-u', metavar="firelog session web page url", dest='URL',
                        help="Browse the given web page", default = None)
    parser.add_argument('-conf', '--conffile', metavar="path", dest='CONFFILE', default = None,
                        help="Location of the configuration file for the Firelog probe")
    parser.add_argument('-d', '--supervisor-ip4', metavar='supervisor-ip4', default=DEFAULT_SUPERVISOR_IP4, dest='SUPERVISOR_IP4',
                        help='Supervisor IP address')
    parser.add_argument('-p', '--supervisor-port', metavar='supervisor-port', default=DEFAULT_SUPERVISOR_PORT, dest='SUPERVISOR_PORT',
                        help='Supervisor port number')
    parser.add_argument('--disable-ssl', action='store_true', default=False, dest='DISABLE_SSL',
                        help='Disable secure communication')
    parser.add_argument('-c', '--certfile', metavar="path", dest='CERTFILE', default = None,
                        help="Location of the configuration file for certificates")
    
    args = parser.parse_args()

# from tstat-proxy.py
class HttpProbe():
    """
    This class manages interactions with the supervisor:
    registration, specification retrievement, and return of results
    
    """
    
    def __init__(self, immediate_ms = 5000):
        parse_args()
        self.dn = None
        
        # check if security is enabled, if so read certificate files
        self.security = not args.DISABLE_SSL
        if self.security:
            mplane.utils.check_file(args.CERTFILE)
            self.cert = mplane.utils.normalize_path(mplane.utils.read_setting(args.CERTFILE, "cert"))
            self.key = mplane.utils.normalize_path(mplane.utils.read_setting(args.CERTFILE, "key"))
            self.ca = mplane.utils.normalize_path(mplane.utils.read_setting(args.CERTFILE, "ca-chain"))
            mplane.utils.check_file(self.cert)
            mplane.utils.check_file(self.key)
            mplane.utils.check_file(self.ca)
            self.pool = HTTPSConnectionPool(args.SUPERVISOR_IP4, args.SUPERVISOR_PORT, key_file=self.key, cert_file=self.cert, ca_certs=self.ca)
        else: 
            self.pool = HTTPConnectionPool(args.SUPERVISOR_IP4, args.SUPERVISOR_PORT)
            self.cert = None
        
        # get server DN, for Access Control purposes
        self.dn = self.get_dn()
        
        # generate a Service for each capability
        self.immediate_ms = immediate_ms
        self.scheduler = mplane.scheduler.Scheduler(self.security, self.cert)
        self.scheduler.add_service(FirelogService(firelog_capability(args.URL)))
        
    def get_dn(self):
        """
        Extracts the DN from the server. 
        If SSL is disabled, returns a dummy DN
        
        """
        if self.security == True:
            
            # extract DN from server certificate.
            # Unfortunately, there seems to be no way to do this using urllib3,
            # thus ssl library is being used
            s = socket()
            c = ssl.wrap_socket(s,cert_reqs=ssl.CERT_REQUIRED, keyfile=self.key, certfile=self.cert, ca_certs=self.ca)
            c.connect((args.SUPERVISOR_IP4, args.SUPERVISOR_PORT))
            cert = c.getpeercert()
            
            dn = ""
            for elem in cert.get('subject'):
                if dn == "":
                    dn = dn + str(elem[0][1])
                else: 
                    dn = dn + "." + str(elem[0][1])
        else:
            dn = DUMMY_DN
        return dn
     
    def register_to_supervisor(self):
        """
        Sends a list of capabilities to the Supervisor, in order to register them
        
        """
        url = "/" + REGISTRATION_PATH
        
        # generate the capability list
        caps_list = ""
        no_caps_exposed = True
        for key in self.scheduler.capability_keys():
            cap = self.scheduler.capability_for_key(key)
            if (self.scheduler.ac.check_azn(cap._label, self.dn)):
                caps_list = caps_list + mplane.model.unparse_json(cap) + ","
                no_caps_exposed = False
        caps_list = "[" + caps_list[:-1].replace("\n","") + "]"
        connected = False
        
        if no_caps_exposed is True:
           print("\nNo Capabilities are being exposed to the Supervisor, check permission files. Exiting")
           exit(0)
        
        # send the list to the supervisor, if reachable
        while not connected:
            try:
                res = self.pool.urlopen('POST', url, 
                    body=caps_list.encode("utf-8"), 
                    headers={"content-type": "application/x-mplane+json"})
                connected = True
                
            except:
                print("Supervisor unreachable. Retrying connection in 5 seconds")
                sleep(5)
                
        # handle response message
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
    
    def check_for_specs(self):
        """
        Poll the supervisor for specifications
        
        """
        url = "/" + SPECIFICATION_PATH
        
        # send a request for specifications
        res = self.pool.request('GET', url)
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
                    res = self.pool.urlopen('POST', result_url, 
                            body=mplane.model.unparse_json(reply).encode("utf-8"), 
                            headers={"content-type": "application/x-mplane+json"})
                    return
                
                # enqueue job
                job = self.scheduler.job_for_message(reply)
                
                # launch a thread to monitor the status of the running measurement
                t = threading.Thread(target=self.return_results, args=[job])
                t.start()
                
        # not registered on supervisor, need to re-register
        elif res.status == 428:
            print("\nRe-registering capabilities on Supervisor")
            self.register_to_supervisor()
        pass
    
    def return_results(self, job):
        """
        Monitors a job, and as soon as it is complete sends it to the Supervisor
        
        """
        url = "/" + RESULT_PATH
        reply = job.get_reply()
        
        # check if job is completed
        while job.finished() is not True:
            if job.failed():
                reply = job.get_reply()
                break
            sleep(1)
        if isinstance (reply, mplane.model.Receipt):
            reply = job.get_reply()
        
        # send result to the Supervisor
        res = self.pool.urlopen('POST', url, 
                body=mplane.model.unparse_json(reply).encode("utf-8"), 
                headers={"content-type": "application/x-mplane+json"})
                
        # handle response
        if res.status == 200:
            print("Result for " + reply.get_label() + " successfully returned!")
        else:
            print("Error returning Result for " + reply.get_label())
            print("Supervisor said: " + str(res.status) + " - " + res.data.decode("utf-8"))
        pass

        
# For right now, start a Tornado-based ping server
if __name__ == "__main__":
    mplane.model.initialize_registry()
    probe = HttpProbe()
    
    # register this probe to the Supervisor
    probe.register_to_supervisor()
    
    # periodically polls the Supervisor for Specifications
    print("Checking for Specifications...")
    while(True):
        probe.check_for_specs()
        sleep(5)
