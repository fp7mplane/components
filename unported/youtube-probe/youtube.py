# mPlane Protocol Reference Implementation
# YouTube Ping probe component code
#
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
# (c) 2013-2014 mPlane Consortium (http://www.ict-mplane.eu)
#		Author: Tivadar Szemethy <tivadat.szemethy@netvisor.hu>
#               Based on the ping.py code from: Brian Trammell <brian@trammell.ch>
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

# Implements YouTube measurements for integration into 
# the mPlane reference implementation.

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
# import argparse
import sys
from yp import YouTubeClient

YouTubeMetrics = ( "delay.urlresolve.ms", "octets.layer7", "delay.download.ms", "bandwidth.min.bps", "bandwidth.avg.bps", "bandwidth.max.bps", "delay.srvresponse.ms", "rebuffer.counter" )

def youtube_capability(vid):
    # TODO: might be able to do it periodically - check for the video's length for period constraint
    # cap = mplane.model.Capability(label="ping-average-ip4", when = "now ... future / 1s")
    cap = mplane.model.Capability(label="youtube-probe", when = "now ... future")
    cap.add_parameter("youtube.video.id", vid)
    for m in YouTubeMetrics: 
        cap.add_result_column(m)
    return cap

class YouTubeProbeService(mplane.scheduler.Service):
    def __init__(self, cap):
        # verify the capability is acceptable
        if (not (cap.has_parameter("youtube.video.id"))):
            raise ValueError("Missing youtube.video.id")
        
        if not (cap.has_result_column("octets.layer7") or
            cap.has_result_column("bandwidth.avg.bps") or
            cap.has_result_column("bandwidth.max.bps") or
            cap.has_result_column("bandwidth.min.bps") or
            cap.has_result_column("delay.urlresolve.ms") or
            cap.has_result_column("delay.srvresponse.ms") or
            cap.has_result_column("delay.download.ms") or
            cap.has_result_column("rebuffer.counter")):
            raise ValueError("capability not acceptable")
        super(YouTubeProbeService, self).__init__(cap)


    def run(self, spec, check_interrupt):
        # unpack parameters
        youtube_id = spec.get_parameter_value("youtube.video.id")

        # TODO - here you invoke yc in a try - catch block

        start_time = datetime.utcnow()

        params = { 'video_id': youtube_id, 'bwlimit': 0 }
        # not supposed to throw any exception, just better safe than sorry
        try:
            probe = YouTubeClient(params)
            (success, metrics) = probe.run()
            print("Metrics: %s" % str(metrics))
        except Exception as e:
            metrics = {}

        end_time = datetime.utcnow()

        # derive a result from the specification
        res = mplane.model.Result(specification=spec)

        # put actual start and end time into result
        res.set_when(mplane.model.When(a = start_time, b = end_time))

        for m in YouTubeMetrics:
            e = mplane.model.element(m)
            # some numbers are returned as floats: need to int() them
            if  str(e._prim) == 'natural':
                r = int(metrics[m])
            else:
                r = metrics[m]

            res.set_result_value(m, r)

        return res

def parse_args():
    global video_id
    # parser = argparse.ArgumentParser(description="Run an mPlane YouTube probe server")
    # args = parser.parse_args()
    video_id = "riyXuGoqJlY"
    if len(sys.argv) >= 2:
        video_id = sys.argv[1]

# For right now, start a Tornado-based ping server
if __name__ == "__main__":

    mplane.model.initialize_registry()
    parse_args()

    scheduler = mplane.scheduler.Scheduler()
    scheduler.add_service(YouTubeProbeService(youtube_capability(video_id)))

    mplane.httpsrv.runloop(scheduler)
