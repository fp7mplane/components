# mPlane Protocol Reference Implementation
# based on example component code
#
# (c) 2013-2015 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Gábor Molnár
#
# (c) 2013-2015 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Stefano Pentassuglia
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

import time
import json
import os.path
import pickle

import mplane.model
import mplane.scheduler
import mplane.utils

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import task
from twisted.internet import reactor

from threading import Thread

globalRepo = None
RESULTS_TMP = "/tmp/results.json"
THRESHOLD= "mplane/threshold.json"


class MarkResult():

    def __init__(self, _dict):
        self.mark = {}
        self.myResult = _dict

class MyRepo(DatagramProtocol):

    def __init__(self, fname):
        global globalRepo

        self.mark_results = {}
        self.mark_results["ping"] = []
        self.mark_results["ott"] = []

        self.ping_thresholds = {}

        """ TODO loading data from RESULTS_TMP
        if os.path.isfile(RESULTS_TMP):
            with open(RESULTS_TMP, 'rb') as i:
                self.mark_results = pickle.load(i)
        """

        if os.path.isfile(THRESHOLD):
            with open(THRESHOLD, 'r') as fp:
                self.ping_thresholds = json.load(fp)
        else:
            raise IOError(THRESHOLD, " not found, grading is impossible")

        globalRepo = self.mark_results;

    def doMark(self, metric, li, i, resultvalues):
        mark = 1
        eq = 1
        if self.ping_thresholds[metric]["2"] > self.ping_thresholds[metric]["3"]:
            eq = -1
        for k, v in li.items():
            for array in resultvalues:
                if eq == -1:
                    if float(array[i]) < v:
                        mark = k
                          
                    else:
                        break
                elif eq == 1:
                    if float(array[i]) > v:
                        mark = k
                    else:
                        break
                else:
                    print("Unknown EQ")
        return mark

    def handlePing(self, _dict):
        mark_result = MarkResult(_dict)
        for i in range(len(_dict["results"])):
            metric = _dict["results"][i]
            if metric in self.ping_thresholds:
                #threshold exists for metric
                mark_result.mark[metric] = int(self.doMark(metric, self.ping_thresholds[metric], i, _dict["resultvalues"]))
                print("metric: ", metric, " mark: ", mark_result.mark[metric] )
        self.mark_results["ping"].append(mark_result)

    def datagramReceived(self, data, hostAndPort):
        # TODO:
        # - check if it is a Result in a better way
        # - errorhandling

        #print(data.decode("utf-8"))
        global globalRepo
        _dict = eval(data.decode("utf-8"))
        if 'label' in _dict:
            label = _dict["label"]
            if label.startswith("ping"):
                self.handlePing(_dict)
            elif label.startswith("ott"):
                self.handleOTT(_dict)
        globalRepo = self.mark_results

def runEveryMinute():
    # saving the results to RESULTS_TMP
    global globalRepo
    with open(RESULTS_TMP, 'wb') as o:
        pickle.dump(globalRepo, o)

    
"""
Implements service capabilities and services
"""

def services(port = "9900"):

    # TODO fname from config
    fname = "mplane/threshold.json"

    # l = task.LoopingCall(runEveryMinute)
    # l.start(10)
    port = port.replace(" ", "")
    try:
        ports = port.split(",")
        for p in ports:
            reactor.listenUDP(int(p), MyRepo(fname))
    except:
        reactor.listenUDP(int(port), MyRepo(fname))

    Thread(target=reactor.run, args=(False,)).start()

    # the parameter is passed to this function by component-py, 
    # that reads it from the [module_repository] section 
    # in the config file
    services = []
    services.append(RepositoryService(repository_capability()) )
    return services

def repository_capability():
    cap = mplane.model.Capability(verb="query", label="ezrepo", when = "past ... future")

    cap.add_parameter("type.repo") #TODO add this to registry.json. Set not working like cap.add_parameter("type.repo", "ott, ping"). 
    cap.add_parameter("range.grade")
    cap.add_parameter("select.grade")
    cap.add_parameter("metric.repo")

    cap.add_result_column("results.repo")
    cap.add_result_column("overall.grade")
    cap.add_result_column("source.ip4")
    cap.add_result_column("destination.ip4")
    return cap

class RepositoryService(mplane.scheduler.Service):
    """
    This class handles the capabilities exposed by the component:
    executes them, and fills the results
    """

    def __init__(self, cap):
        super(RepositoryService, self).__init__(cap)

    def run(self, spec, check_interrupt):
        """ Execute this Service """
        global globalRepo
        time.sleep(1)
        # Run measurements here
        res = mplane.model.Result(specification=spec)
        (start_time , end_time) = spec._when.datetimes()
        if not start_time:
            start_time = "1970-01-01 00:00:00.000000"
        res.set_when(mplane.model.When(a = start_time, b = end_time))

        myType = spec.get_parameter_value("type.repo")
        (mark_min, mark_max) = spec.get_parameter_value("range.grade").split(' ... ')
        metric = spec.get_parameter_value("metric.repo")
        iterator = 0

        mark_min = int(mark_min)
        mark_max = int(mark_max)

        if myType not in globalRepo:
            raise ValueError("Unknown type.repo: ",myType," Currently supported: ott, ping")

        if mark_min < 1 or mark_min > 5:
            raise ValueError("Error in mark.min.repo: ",mark_min," Value must be between 1 and 5")

        if mark_max < 1 or mark_max > 5:
            raise ValueError("Error in mark.max.repo: ",mark_max," Value must be between 1 and 5")

        for myRes in globalRepo[myType]:
            # myRes => all of the Results from myType
            for m in myRes.mark:
                # m => metric
                # myRes.mark[m] => mark for the metric
                # is metric filtered?
                print("1")
                if m == metric or metric == 'all':
                    print(" 2")
                    # will it fit for the mark?
                    if myRes.mark[m] >= mark_min and myRes.mark[m] <= mark_max:
                        print("  3")
                        # is in the queried period?
                        (when_a , when_b) = mplane.model.Result(myRes.myResult)._when.datetimes()
                        print(when_a, " ", when_b)
                        if when_a >= start_time and when_b <= end_time: 
                            print("   4")
                            print(myRes.myResult)
                            res.set_result_value("results.repo", myRes.myResult, iterator)
                            res.set_result_value("overall.grade", myRes.mark[m], iterator)
                            if "source.ip4" in myRes.myResult["parameters"]:
                                res.set_result_value("source.ip4", myRes.myResult["parameters"]["source.ip4"], iterator)
                            else:
                                res.set_result_value("source.ip4", "1.2.3.4", iterator)
                            if "destination.ip4" in myRes.myResult["parameters"]:
                                res.set_result_value("destination.ip4", myRes.myResult["parameters"]["destination.ip4"], iterator)
                            else:
                                res.set_result_value("destination.ip4", "1.2.3.4", iterator)
                            iterator += 1
            
        #res.set_result_value("results.repo", globalRepo["ping"][2].myResult, 2)
        #print(mplane.model.unparse_json(res).encode("utf-8"))
        return res
