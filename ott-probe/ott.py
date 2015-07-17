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
 * ER_0 : currently one count is supported
 * ER_1 : more robust subprocess handling

"""

import sys
import argparse
import subprocess
from time import sleep
from datetime import datetime, timedelta
import urllib3
# from urllib3 import HTTPConnectionPool
# from urllib3 import HTTPSConnectionPool
import json
import mplane.model
import mplane.scheduler


_ottopt_period = "--mplane"
_ottopt_url    = "--url"

caplist = ["bandwidth.nominal.kbps", "http.code.max", "http.redirectcount.max", "qos.manifest", "qos.content", "qos.aggregate", "qos.level"]

# urllib3.disable_warnings()

"""
this method is for starting the OTT measurement. probe-ott will return with a measurement JSON.
"""
def _ott_process(period=None, url=None):
    ott_argv = ["probe-ott"]
    ott_argv += [ "--slot", "-1"]
    if period is not None:
        ott_argv += [_ottopt_period, str(int(period))]
    if url is not None:
        ott_argv += [_ottopt_url, str(url)]
    print("\n >>> " + str(datetime.now()) + ": running " + " ".join(ott_argv) + "\n", file=sys.stderr)
    return subprocess.Popen(ott_argv, stdout=subprocess.PIPE)

    
def services(ip4addr = None, ip6addr = None):
    services = []
    if ip4addr is not None:
        services.append(OttService(ott_capability(ip4addr)))
        # print("\n>>> after services.append: services = " + str(services), file=sys.stderr)
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
# bnj : we suppose that it runs repeatedly during the range, so that
# now + 30s / 10s results in 3 runs, 10 seconds long each
#
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
      #try:
        period = int(spec.when().period().total_seconds())
        duration = spec.when().duration().total_seconds()
        if duration is not None and duration > 0:
            count = int(duration / period)
        else:
            count = None

        if spec.has_parameter("content.url"):
            url = spec.get_parameter_value("content.url")
        else:
            raise ValueError("Missing URL")
            
        while count > 0:
            print("\n>>> runcount = " + str(count), file=sys.stderr)
            ott_process = _ott_process(period, url)
            count -= 1
            if count > 0:
                sleep(period)
        print("\n>>> probe-ott runs finished, output process begins...", file=sys.stderr)
      
        # read output 
        lc = 0
        jsonS = ""
        for line in ott_process.stdout:
            # ER_1 :
            # if check_interrupt():
               # break
            strLine = line.decode()
            if strLine is "}":
                jsonS += strLine
                break
            jsonS += strLine
            lc += 1
        print("\n>>> " + str(lc) + " JSON lines read", file=sys.stderr)

        # ER_1 : maybe should be placed somewhere else
        # shut down and reap
        # try:
           # ott_process.kill()
        # except OSError:
           # pass
        # ott_process.wait()

        jsonO = json.loads(jsonS)
        e = str(datetime.now())
        s = str(datetime.now()-timedelta(seconds=period))

        # derive a result from the specification
        res = mplane.model.Result(specification=spec)

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
        return res
