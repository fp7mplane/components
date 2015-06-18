# mPlane Protocol Reference Implementation
# repository component code
#
# (c) 2013-2014 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Stefano Pentassuglia
#               Author: Ali Safari Khatouni
#               Author: Stefano Traverso
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
import sys
import os
from threading import Thread
import configparser
import mplane.model
import mplane.scheduler
import mplane.utils
from mplane.components.tstat.repository_importers import rrd_file_grouping
from mplane.components.tstat.repository_importers import repository_rrd_importer
from mplane.components.tstat.repository_importers import repository_streaming_importer
from mplane.components.tstat.repository_importers.repository_rrd_importer import HttpServer

"""
Implements repository capabilities and services

"""

def services(repository_ip, repository_rrd_port, repository_streaming_port, repository_log_port, config_path):
    services = []
    if (repository_ip is not None and
        repository_rrd_port is not None and
        repository_streaming_port is not None and 
        repository_log_port is not None):
        services.append(RepositoryService(collect_rrd_capability(repository_ip, repository_rrd_port), 
                                          repository_ip, int(repository_rrd_port), config_path))
        services.append(RepositoryService(collect_streaming_capability(repository_ip, repository_streaming_port), 
                                          repository_ip, int(repository_streaming_port)))
        services.append(RepositoryService(collect_log_capability(repository_ip, repository_log_port)))
    else:
        raise ValueError("missing 'runtimeconf' parameter for repository capabilities")
    return services

def collect_rrd_capability(ip4, port):
    cap = mplane.model.Capability(label="repository-collect_rrd", when = "past ... future")
    cap.add_metadata("System_type", "repository")
    cap.add_metadata("System_ID", "repository-Proxy")
    cap.add_metadata("System_version", "0.1")
    cap.add_parameter("repository.url", (str(ip4) + ":" + str(port)))
    cap.add_result_column("rrdtimestamp")
    cap.add_result_column("rrdMetirc")
    cap.add_result_column("rrdValue")
    return cap

def collect_streaming_capability(ip4, port):
    cap = mplane.model.Capability(label="repository-collect_streaming", when = "now ... future")
    cap.add_metadata("System_type", "repository")
    cap.add_metadata("System_ID", "repository-Proxy")
    cap.add_metadata("System_version", "0.1")
    cap.add_parameter("repository.url", (str(ip4) + ":" + str(port)))
    return cap

def collect_log_capability(ip4, port):
    cap = mplane.model.Capability(label="repository-collect_log", when = "past ... future")
    cap.add_metadata("System_type", "repository")
    cap.add_metadata("System_ID", "repository-Proxy")
    cap.add_metadata("System_version", "0.1")
    cap.add_parameter("repository.url", (str(ip4) + ":" + str(port)))
    return cap

class RepositoryService(mplane.scheduler.Service):
    """
    This class handles the capabilities exposed by the proxy:
    executes them, and fills the results
    
    """
    
    def __init__(self, cap, repo_ip = None, repo_port = None, config_path = None):
        super(RepositoryService, self).__init__(cap)
        if (repo_ip is not None and repo_port is not None):
            if (config_path is not None):            
                # Read the configuration file
                config = configparser.ConfigParser()
                config.optionxform = str
                config.read(mplane.utils.search_path(config_path))
                self.httpserver = HttpServer(repo_ip, repo_port, config)
            else:
                try:
                    t = Thread(target=repository_streaming_importer.run, args=[repo_ip, repo_port])
                    t.start()
                except (KeyboardInterrupt):
                    return
                


    def run(self, spec, check_interrupt):
        """

        Execute this Service 
        The wait_time is used for the capability which runs directly 
        from client NOT used for Indirect Collect 
        
        """
        start_time = datetime.utcnow()
        wait_time = spec._when.timer_delays()
        wait_seconds = wait_time[1]
        end_time = start_time
        if wait_seconds != None:
            if wait_seconds == 0: # Wait time is NOT inf
                end_time = datetime.max
                wait_seconds = (end_time - start_time).total_seconds()
            else:
                end_time = (start_time + datetime.timedelta(seconds=wait_seconds))


        # start measurement changing the repository conf file
        self.change_conf(spec.get_label(), True)


        if ("repository-collect_rrd" in spec.get_label()):
            print (" Ready to create connection for specification (repository-collect_rrd) : ")
            # check which capability family 
        elif ("repository-collect_streaming" in spec.get_label()):
            print (" Ready to create connection for specification (repository-collect_streaming) : ")
        elif ("repository-collect_log" in spec.get_label()):
            print (" Ready to create connection for specification (repository-collect_log) : ")

        else:
            raise ValueError("Capability family doesn't exist")


        # wait for specification execution
        if wait_seconds != None:
            if end_time != datetime.max: # Wait time is NOT inf
                sleep(wait_seconds)
                # terminate measurement changing the repository conf file
                self.change_conf(spec.get_label(), False)
                end_time = datetime.utcnow()
            print("specification " + spec.get_label() + ": start = " + str(start_time) + ", end = " + str(end_time))
            res = self.fill_res(spec, start_time, end_time)
        return res


    def change_conf(self, cap_label, enable):
        """
        Changes the needed flags in the repository runtime.conf ? file
        
        """
        # change flags according to the measurement requested
        if enable == True:
                    
            # in order to activate/diactivate capabilities
            # we may need to have a configuration file for repository 

            if "repository-collect_rrd" in cap_label :
                print("repository-collect_rrd Enabled \n")
            elif "repository-collect_streaming" in cap_label:
                print("repository-collect_streaming Enabled \n")
            elif "repository-collect_log" in cap_label:
                print("repository-collect_log Enabled \n")
            else:
                print("UNKNOWN CAPABILITY \n")
        else:
            if "repository-collect_rrd" in cap_label :
                print("repository-collect_rrd Disabled \n")
            elif "repository-collect_streaming" in cap_label :
                print("repository-collect_streaming Disabled \n")
            elif "repository-collect_log" in cap_label :
                print("repository-collect_log Disabled \n")
            else:
                print("UNKNOWN CAPABILITY \n")

    def fill_res(self, spec, start, end):
        """
        Create a Result statement, fill it and return it
        
        """

        # derive a result from the specification
        res = mplane.model.Result(specification=spec)

        # put actual start and end time into result
        res.set_when(mplane.model.When(a = start, b = end))
        
        # fill result columns with DUMMY values
        for column_name in res.result_column_names():
            prim = res._resultcolumns[column_name].primitive_name()
            if prim == "natural":
                res.set_result_value(column_name, 0)
            elif prim == "string":
                res.set_result_value(column_name, "hello")
            elif prim == "real":
                res.set_result_value(column_name, 0.0)
            elif prim == "boolean":
                res.set_result_value(column_name, True)
            elif prim == "time":
                res.set_result_value(column_name, start)
            elif prim == "address":
                res.set_result_value(column_name, args.SUPERVISOR_IP4)
            elif prim == "url":
                res.set_result_value(column_name, "www.google.com")
        
        return res