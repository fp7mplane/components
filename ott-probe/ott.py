#
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
# mPlane Protocol Reference Implementation
# OTT probe component code for component-initiated workflow. 
#               Author: Janos Bartok-Nagy <janos.bartok-nagy@netvisor.hu>
#
# Based on: ICMP Ping probe component code
# (c) 2013-2014 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Brian Trammell <brian@trammell.ch>
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
Implements OTT-probe's download measurements for integration into 
the mPlane reference implementation.

"""

import re
import subprocess
import collections
from datetime import datetime, timedelta
import mplane.model
import mplane.scheduler
import sys
import json

_ottcmd = "ott"
_ottopt_period = "--mplane"
_ottopt_url    = "--url"

LOOP4 = "127.0.0.1"
LOOP6 = "::1"

caplist = ["bandwidth.nominal.kbps", "http.code.max", "http.redirectcount.max", "qos.manifest", "qos.content", "qos.aggregate", "qos.level"]


def services(ip4addr = None, ip6addr = None):
    services = []
    if ip4addr is not None:
        services.append(OttService(ott_capability(ip4addr)))
    return services

    
def _ott_process(period=None, url=None):
    ott_argv = ["probe-ott"]
    ott_argv += [ "--slot", "-1"]
    if period is not None:
        ott_argv += [_ottopt_period, str(int(period))]
    if url is not None:
        ott_argv += [_ottopt_url, str(url)]
    print("\n" + str(datetime.now()) + ": running " + " ".join(ott_argv))
    return subprocess.Popen(ott_argv, stdout=subprocess.PIPE)


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

        period = int(spec.when().period().total_seconds())

        if spec.has_parameter("content.url"):
            url = spec.get_parameter_value("content.url")
            ott_process = _ott_process(period, url)
        else:
            raise ValueError("Missing URL")
            
        # read output from ott-probe # read output from ping
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
        print(res)
        return res
      except:
        print("Unexpected error in run:", sys.exc_info())
        raise
        
