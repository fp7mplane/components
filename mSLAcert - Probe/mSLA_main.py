# mPlane Protocol Reference Implementation
# tStat component code
#
# (c) 2013-2014 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Edion TEGO
# mSLAcert-V-3.0.2
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

import threading
from datetime import datetime
import time
from time import sleep
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
import math
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
print("    ###$$$$$$$|Politecnico di Torino|Fondazione Ugo Bordoni| SSB Progetti| Telecom Italia|&$$$$$$$$$$$$$$$$$$##");
print("    ###$$$$$$$$---------------------&----------------------&-------------&---------------$$$$$$$$$$$$$$$$$$$$##");
print("    ##$$$$________________________&_______&_________________&_______________$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$##");
print("    ###$$|Alcatel-Lucent Bell Labs|EURECOM| Telecom Paritech| NEC Europe LTD| $$$$$$$$$$$$$$$$$$$$$$$$&&&&&$$##");
print("    ###$$$------------------------&-------&-----------------&---------------$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$##");
print("    ##$$________________________________________&________&_____________________________________________$$$$$$##");
print("    ###|Telefonica Investigacion Y Desarrollo Sa|Netvisor|Forschungszentrum Telekommunikation Wien Gmbh|$$$$$##");
print("    ###$----------------------------------------&--------&---------------------------------------------$$$$$$##");
print("    ##$$$$$$$$_______________________&____________________&_____________________________________________$$$$$##");
print("    ##$$$$$$$|Fachhochschule Augsburg||Universite de Liege|Eidgenoessische Technische Hochschule Zurich |$$$$##");
print("    ###$$$$$$$-----------------------&--------------------&---------------------------------------------$$$$$##");
print("    ###$$$$$$$$$$$$$$$$$$$$$$$______________________&_______$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$##");
print("    ###$$$$$$$$$$$$$$$$$$$$$$|Alcatel-Lucent Bell Nv|FASTWEB|$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#");
print("    ###$$$$$$$$$$$$$$$$$$$$$$$----------------------&-------$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$##");
print("    ###$$$$$$$$$| mSLAcert probe| RTT, TCP throughput and UDP throughput verification and certification|$$$$$##");
print("    ###########################################################################################################");

_pingline_re = re.compile("icmp_seq=(\d+)\s+\S+=(\d+)\s+time=([\d\.]+)\s+ms")

_ping4cmd = "ping"
_ping6cmd = "ping6"
_pingopts = ["-n"]
_pingopt_period = "-i"
_pingopt_count = "-c"
_pingopt_source = "-S"

LOOP4 = "127.0.0.1"
LOOP6 = "::1"

PingValue = collections.namedtuple("PingValue", ["time", "seq", "ttl", "usec"])

_tcpslaline_re = re.compile("\[+\s+\d+]\s+\d.+\d+-\s+(\d+.\d+)\s+sec\s+(\d+.\d+)\s+.+\s+(\d+.\d+)\s+.+")

_tcpslaline_re_after_9 = re.compile("\[+\s+\d+]\s+\d.+\d+-(\d+.\d+)\s+sec\s+(\d+.\d+)\s+.+\s+(\d+.\d+)\s+.+")

_tcpsla4cmd = "iperf"
_tcpsla6cmd = "iperf"
_tcpslaopts = ["-n"]
_tcpslaopt_period = "-i"
_tcpslaopt_count = "-t"
_tcpslaopt_source = "-c"
_tcpslaopt_formatout = "-f k"

tcpslaValue = collections.namedtuple("tcpslaValue", ["time", "interval", "Transfer_MB", "Bandwidth_Mbps"])

_udpslaline_re = re.compile("\[+\s+\d+]\s+\d.+\d+-\s+(\d+.\d+)\s+sec\s+(\d+.\d+)\s+.+\s+(\d+.\d+)\s+.+/sec")

_udpslaline_re_after_9 = re.compile("\[+\s+\d+]\s+\d.+\d+\-+(\d+.\d+)\s+sec\s+(\d+.\d+)\s+.+\s+(\d+.\d+)\s+.+/sec")


_udpreport_re = re.compile("\[+\s+\d+]\s+\d.+\d+-\s+(\d+.\d+)\s+sec\s+(\d+.\d+)\s+.+\s+(\d+.\d+)\s+.+\s+(\d+.\d+)\s+ms\s+(\d+)/(\d+)\s+\(+(\d+.\d+)")

_udpreport_re_after_9 = re.compile("\[+\s+\d+]\s+\d.+\d+\-+(\d+.\d+)\s+sec\s+(\d+.\d+)\s+.+\s+(\d+.\d+)\s+.+\s+(\d+.\d+)\s+ms\s+(\d+)/(\d+)\s+\(+(\d+.\d+)")


udpreportvalue = collections.namedtuple("udpreportValue", ["time", "Transfer_MB", "Bandwidth_mean_Mbps", "Jitter_ms", "Lost_Datgrms", "Total_Datgrms", "Error_prc"])

_udpsla4cmd = "iperf"
_udpsla6cmd = "iperf"
_udpslaopts = ["-n"]
_udpslaopt_period = "-i"
_udpslaopt_count = "-t"
_udpslaopt_source = "-c"
_udpslaopt_band = "-b 99m"
_udpslaopt_port = "-p 5002"
_udpslaopt_testudp = "-u"


udpslaValue = collections.namedtuple("udpslaValue", ["time", "interval", "Transfer_MB", "Bandwidth_Mbps"])


def services(ip4addr = None):
    services = []
    if ip4addr is not None:
        services.append(PingService(ping4_aggregate_capability(ip4addr)))
        services.append(PingService(ping4_singleton_capability(ip4addr)))
        services.append(tcpslaService(tcpsla4_aggregate_capability(ip4addr)))
        services.append(tcpslaService(tcpsla4_singleton_capability(ip4addr)))
        services.append(udpslaService(udpsla4_aggregate_capability(ip4addr)))
        services.append(udpslaService(udpsla4_singleton_capability(ip4addr)))
        services.append(mSLAcertService(msla4_aggregate_capability(ip4addr)))
        services.append(mSLAcertService(msla4_singleton_capability(ip4addr)))
    return services
def _parse_ping_line(line):
    m = _pingline_re.search(line)
    if m is None:
        print(line)
        return None
    mg = m.groups()
    return PingValue(datetime.utcnow(), int(mg[0]), int(mg[1]), int(float(mg[2]) * 1000))

def _ping_process(progname, sipaddr, dipaddr, period=None, count=None):
    ping_argv = [progname]
    if period is not None:
        ping_argv += [_pingopt_period, str(period)]
    if count is not None:
        ping_argv += [_pingopt_count, str(count)]
    ping_argv += [_pingopt_source, str(sipaddr)]
    ping_argv += [str(dipaddr)]

    print("running " + " ".join(ping_argv))

    return subprocess.Popen(ping_argv, stdout=subprocess.PIPE)

def _ping4_process(sipaddr, dipaddr, period=None, count=None):
    return _ping_process(_ping4cmd, sipaddr, dipaddr, period, count)

def _ping6_process(sipaddr, dipaddr, period=None, count=None):
    return _ping_process(_ping6cmd, sipaddr, dipaddr, period, count)

def pings_min_delay(pings):
    return min(map(lambda x: x.usec, pings))

def pings_mean_delay(pings):
    return int(sum(map(lambda x: x.usec, pings)) / len(pings))

def pings_median_delay(pings):
    return sorted(map(lambda x: x.usec, pings))[int(len(pings) / 2)]

def pings_max_delay(pings):
    return max(map(lambda x: x.usec, pings))

def pings_start_time(pings):
    return pings[0].time

def pings_end_time(pings):
    return pings[-1].time

def ping4_aggregate_capability(ip4addr):
    cap = mplane.model.Capability(label="ping-average-ip4", when = "now ... future / 1s")
    cap.add_parameter("source.ip4",ip4addr)
    cap.add_parameter("destination.ip4")
    cap.add_result_column("delay.twoway.icmp.us.min")
    cap.add_result_column("delay.twoway.icmp.us.mean")
    cap.add_result_column("delay.twoway.icmp.us.max")
    cap.add_result_column("delay.twoway.icmp.count")
    return cap

def ping4_singleton_capability(ip4addr):
    cap = mplane.model.Capability(label="ping-detail-ip4", when = "now ... future / 1s")
    cap.add_parameter("source.ip4",ip4addr)
    cap.add_parameter("destination.ip4")
    cap.add_result_column("time")
    cap.add_result_column("delay.twoway.icmp.us")
    return cap

def ping6_aggregate_capability(ip6addr):
    cap = mplane.model.Capability(label="ping-average-ip6", when = "now ... future / 1s")
    cap.add_parameter("source.ip6",ip6addr)
    cap.add_parameter("destination.ip6")
    cap.add_result_column("delay.twoway.icmp.us.min")
    cap.add_result_column("delay.twoway.icmp.us.mean")
    cap.add_result_column("delay.twoway.icmp.us.max")
    cap.add_result_column("delay.twoway.icmp.count")
    return cap

def ping6_singleton_capability(ip6addr):
    cap = mplane.model.Capability(label="ping-detail-ip6", when = "now ... future / 1s")
    cap.add_parameter("source.ip6",ip6addr)
    cap.add_parameter("destination.ip6")
    cap.add_result_column("time")
    cap.add_result_column("delay.twoway.icmp.us")
    return cap

def _parse_tcpsla_line(line):
    m = _tcpslaline_re.search(line)
    if m is None:
#        print(line)
        return None
    mg = m.groups()
    return tcpslaValue(datetime.utcnow(), int(float(mg[0])), int(float(mg[1])), int(float(mg[2])))

def _parse_tcpsla_line_after_9(line):
    m = _tcpslaline_re_after_9.search(line)
    if m is None:
#       print (line)
        return None
    mg = m.groups()
    return tcpslaValue(datetime.utcnow(), int(float(mg[0])), int(float(mg[1])), int(float(mg[2])))

def _tcpsla_process(progname, sipaddr, dipaddr, period=None, count=None, formatout=None):
    tcpsla_argv = [progname]
    if period is not None:
        tcpsla_argv += [_tcpslaopt_period, str(period)]
    if count is not None:
        tcpsla_argv += [_tcpslaopt_count, str(count)]
    tcpsla_argv += [_tcpslaopt_source, str(dipaddr)]
    tcpsla_argv += [str(sipaddr)]
    tcpsla_argv += [_tcpslaopt_formatout, str(formatout)]

    print("running " + " ".join(tcpsla_argv))

    return subprocess.Popen(tcpsla_argv, stdout=subprocess.PIPE)

def _tcpsla4_process(sipaddr, dipaddr, period=None, count=None, formatout=None):
    return _tcpsla_process(_tcpsla4cmd, sipaddr, dipaddr, period, count, formatout)

def _tcpsla6_process(sipaddr, dipaddr, period=None, count=None, formatout=None):
    return _tcpsla_process(_tcpsla6cmd, sipaddr, dipaddr, period, count, formatout)

def tcpslas_min_tcpBandwidth(tcpslas):
    return min(map(lambda x: x.Bandwidth_Mbps, tcpslas))

def tcpslas_mean_tcpBandwidth(tcpslas):
    return int(sum(map(lambda x: x.Bandwidth_Mbps, tcpslas)) / len(tcpslas))

def tcpslas_median_tcpBandwidth(tcpslas):
    return sorted(map(lambda x: x.Bandwidth_Mbps, tcpslas))[int(len(tcpslas) / 2)]

def tcpslas_max_tcpBandwidth(tcpslas):
    return max(map(lambda x: x.Bandwidth_Mbps, tcpslas))

def tcpslas_start_time(tcpslas):
    return tcpslas[0].time

def tcpslas_end_time(tcpslas):
    return tcpslas[-1].time

def tcpsla4_aggregate_capability(ip4addr):
    cap = mplane.model.Capability(label="tcpsla-average-ip4", when = "now ... future / 1s")
    cap.add_parameter("source.ip4",ip4addr)
    cap.add_parameter("destination.ip4")
    cap.add_result_column("mSLA.tcpBandwidth.download.iperf.min")
    cap.add_result_column("mSLA.tcpBandwidth.download.iperf.mean")
    cap.add_result_column("mSLA.tcpBandwidth.download.iperf.max")
    cap.add_result_column("mSLA.tcpBandwidth.download.iperf.timecountseconds")
    return cap

def tcpsla4_singleton_capability(ip4addr):
    cap = mplane.model.Capability(label="tcpsla-detail-ip4", when = "now ... future / 1s")
    cap.add_parameter("source.ip4",ip4addr)
    cap.add_parameter("destination.ip4")
    cap.add_result_column("time")
    cap.add_result_column("mSLA.tcpBandwidth.download.iperf")
    return cap

def tcpsla6_aggregate_capability(ip6addr):
    cap = mplane.model.Capability(label="tcpsla-average-ip6", when = "now ... future / 1s")
    cap.add_parameter("source.ip6",ip6addr)
    cap.add_parameter("destination.ip6")
    cap.add_result_column("mSLA.tcpBandwidth.download.iperf.min")
    cap.add_result_column("mSLA.tcpBandwidth.download.iperf.mean")
    cap.add_result_column("mSLA.tcpBandwidth.download.iperf.max")
    cap.add_result_column("mSLA.tcpBandwidth.download.iperf.timecountseconds")
    return cap

def tcpsla6_singleton_capability(ip6addr):
    cap = mplane.model.Capability(label="tcpsla-detail-ip6", when = "now ... future / 1s")
    cap.add_parameter("source.ip6",ip6addr)
    cap.add_parameter("destination.ip6")
    cap.add_result_column("time")
    cap.add_result_column("mSLA.tcpBandwidth.download.iperf")
    return cap
    

def _parse_udpsla_line(line):
    m = _udpslaline_re.search(line)
    if m is None:
#        print(line)
        return None
    mg = m.groups()

    return udpslaValue(datetime.utcnow(), int(float(mg[0])), int(float(mg[1])), int(float(mg[2])))
#    return udpreportvalue(datetime.utcnow(), int(float(mg[0])), int(float(mg[1])), int(float(mg[2])), int(float(mg[3])), int(float(mg[4])), int(float(mg[5])), chr(mg[6]))

def _parse_udpsla_last_line(line):
    lst = _udpreport_re.search(line)
    if lst is None:
#       print (line)
       return None
    lstg = lst.groups()
    return udpreportvalue(datetime.utcnow(), int(float(lstg[1])), float(lstg[2]), float(lstg[3]), int(float(lstg[4])), int(float(lstg[5])), float(lstg[6]))

def _parse_udpsla_line_after_9(line):
    m = _udpslaline_re_after_9.search(line)
    if m is None:
#       print (line)
       return None
    mg = m.groups()

    return udpslaValue(datetime.utcnow(), int(float(mg[0])), int(float(mg[1])), int(float(mg[2])))
#    return udpreportvalue(datetime.utcnow(), int(float(mg[0])), int(float(mg[1])), int(float(mg[2])), int(float(mg[3])), int(float(mg[4])), int(float(mg[5])), chr(mg[6]))

def _parse_udpsla_last_line_after_9(line):
    lst = _udpreport_re_after_9.search(line)
    if lst is None:
#       print (line)
       return None
    lstg = lst.groups()
    return udpreportvalue(datetime.utcnow(), int(float(lstg[1])), float(lstg[2]), float(lstg[3]), int(float(lstg[4])), int(float(lstg[5])), float(lstg[6]))

    
def _udpsla_process(progname, sipaddr, dipaddr, period=None, count=None, testudp=None, band=None, port=None):
    udpsla_argv = [progname]
    udpsla_argv += [_udpslaopt_testudp, str(testudp)]
    udpsla_argv += [_udpslaopt_source, str(dipaddr)]
    if period is not None:
        udpsla_argv += [_udpslaopt_period, str(period)]
    if count is not None:
        udpsla_argv += [_udpslaopt_count, str(count)]
    udpsla_argv += [_udpslaopt_band, str(band)]
    udpsla_argv += [_udpslaopt_port, str(port)]


    print("running " + " ".join(udpsla_argv))

    return subprocess.Popen(udpsla_argv, stdout=subprocess.PIPE)

def _udpsla4_process(sipaddr, dipaddr, period=None, count=None, testudp=None, band=None, port=None):
    return _udpsla_process(_udpsla4cmd, testudp, dipaddr, period, count, band, port)

def _udpsla6_process(sipaddr, dipaddr, period=None, count=None, testudp=None, band=None, port=None):
    return _udpsla_process(_udpsla6cmd, testudp, dipaddr, period, count, band, port)

def udpslas_min_udpCapacity(udpslas):
    return min(map(lambda x: x.Bandwidth_Mbps, udpslas))

def udpslas_mean_udpCapacity(udpslas):
    return int(sum(map(lambda x: x.Bandwidth_Mbps, udpslas)) / len(udpslas))

def udpslas_median_udpCapacity(udpslas):
    return sorted(map(lambda x: x.Bandwidth_Mbps, udpslas))[int(len(udpslas) / 2)]

def udpslas_max_udpCapacity(udpslas):
    return max(map(lambda x: x.Bandwidth_Mbps, udpslas))
    
def udpslas_max_time_udpCapacity(udpslas):
    return max(map(lambda x: x.interval, udpslas))

def udpslas_start_time(udpslas):
    return udpslas[0].time

def udpslas_end_time(udpslas):
    return udpslas[-1].time
    
def udpslas_jitter(udpslas_last):
    return int(map(lambda x: x.Jitter_ms, udpslas_last))

def udpslas_error(udpslas_last):
    return int(map(lambda x: x.Error_prc, udpslas_last))

def udpslas_band_correct(udpslas_last):
    return int(map(lambda x: x.Bandwidth_mean_Mbps, udpslas_last))

def udpsla4_aggregate_capability(ip4addr):
    cap = mplane.model.Capability(label="udpsla-average-ip4", when = "now ... future / 1s")
    cap.add_parameter("source.ip4",ip4addr)
    cap.add_parameter("destination.ip4")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.min")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.mean")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.max")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.jitter")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.error") 
    cap.add_result_column("mSLA-Bandwidth_mean_Mbps-Correct-UDP")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.timecountseconds")
    return cap

def udpsla4_singleton_capability(ip4addr):
    cap = mplane.model.Capability(label="udpsla-detail-ip4", when = "now ... future / 1s")
    cap.add_parameter("source.ip4",ip4addr)
    cap.add_parameter("destination.ip4")
    cap.add_result_column("time")
    cap.add_result_column("mSLA.udpCapacity.download.iperf")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.jitter")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.error") 
    cap.add_result_column("mSLA-Bandwidth_mean_Mbps-Correct-UDP")
    return cap

def udpsla6_aggregate_capability(ip6addr):
    cap = mplane.model.Capability(label="udpsla-average-ip6", when = "now ... future / 1s")
    cap.add_parameter("source.ip6",ip6addr)
    cap.add_parameter("destination.ip6")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.min")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.mean")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.max")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.timecountseconds")
    return cap

def udpsla6_singleton_capability(ip6addr):
    cap = mplane.model.Capability(label="udpsla-detail-ip6", when = "now ... future / 1s")
    cap.add_parameter("source.ip6",ip6addr)
    cap.add_parameter("destination.ip6")
    cap.add_result_column("time")
    cap.add_result_column("mSLA.udpCapacity.download.iperf")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.jitter")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.error") 
    return cap

#definition of SLA field keys

def msla4_aggregate_capability(ip4addr):
    cap = mplane.model.Capability(label="msla-average-ip4", when = "now ... future / 1s")
    cap.add_parameter("source.ip4",ip4addr)
    cap.add_parameter("destination.ip4")
    cap.add_result_column("delay.twoway.icmp.us.min")
    cap.add_result_column("delay.twoway.icmp.us.mean")
    cap.add_result_column("delay.twoway.icmp.us.max")
    cap.add_result_column("delay.twoway.icmp.count")
    cap.add_result_column("mSLA.tcpBandwidth.download.iperf.min")
    cap.add_result_column("mSLA.tcpBandwidth.download.iperf.mean")
    cap.add_result_column("mSLA.tcpBandwidth.download.iperf.max")
    cap.add_result_column("mSLA.tcpBandwidth.download.iperf.timecountseconds")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.min")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.mean")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.max")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.timecountseconds")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.jitter")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.error") 
    cap.add_result_column("mSLA-Bandwidth_mean_Mbps-Correct-UDP")
    return cap

def msla4_singleton_capability(ip4addr):
    cap = mplane.model.Capability(label="msla-detail-ip4", when = "now ... future / 1s")
    cap.add_parameter("source.ip4",ip4addr)
    cap.add_parameter("destination.ip4")
    cap.add_result_column("time")
    cap.add_result_column("delay.twoway.icmp.us")
    cap.add_result_column("mSLA.tcpBandwidth.download.iperf")
    cap.add_result_column("mSLA.udpCapacity.download.iperf")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.jitter")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.error") 
    cap.add_result_column("mSLA-Bandwidth_mean_Mbps-Correct-UDP")
    return cap

def msla6_aggregate_capability(ip6addr):
    cap = mplane.model.Capability(label="msla-average-ip6", when = "now ... future / 1s")
    cap.add_parameter("source.ip6",ip6addr)
    cap.add_parameter("destination.ip6")
    cap.add_result_column("delay.twoway.icmp.us.min")
    cap.add_result_column("delay.twoway.icmp.us.mean")
    cap.add_result_column("delay.twoway.icmp.us.max")
    cap.add_result_column("delay.twoway.icmp.count")
    cap.add_result_column("mSLA.tcpBandwidth.download.iperf.min")
    cap.add_result_column("mSLA.tcpBandwidth.download.iperf.mean")
    cap.add_result_column("mSLA.tcpBandwidth.download.iperf.max")
    cap.add_result_column("mSLA.tcpBandwidth.download.iperf.timecountseconds")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.min")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.mean")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.max")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.timecountseconds")
    return cap

def msla6_singleton_capability(ip6addr):
    cap = mplane.model.Capability(label="msla-detail-ip6", when = "now ... future / 1s")
    cap.add_parameter("source.ip6",ip6addr)
    cap.add_parameter("destination.ip6")
    cap.add_result_column("time")
    cap.add_result_column("delay.twoway.icmp.us")
    cap.add_result_column("mSLA.tcpBandwidth.download.iperf")
    cap.add_result_column("mSLA.udpCapacity.download.iperf")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.jitter")
    cap.add_result_column("mSLA.udpCapacity.download.iperf.error")
    return cap



"""
Implements mSLAcert proxy for integration into 
the mPlane reference implementation.
(capability push, specification pull)

"""

class PingService(mplane.scheduler.Service):
    def __init__(self, cap):
        # verify the capability is acceptable
        if not ((cap.has_parameter("source.ip4") or 
                 cap.has_parameter("source.ip6")) and
                (cap.has_parameter("destination.ip4") or 
                 cap.has_parameter("destination.ip6")) and
                (cap.has_result_column("delay.twoway.icmp.us") or
                 cap.has_result_column("delay.twoway.icmp.us.min") or
                 cap.has_result_column("delay.twoway.icmp.us.mean") or                
                 cap.has_result_column("delay.twoway.icmp.us.max") or
                 cap.has_result_column("delay.twoway.icmp.count"))):
            raise ValueError("capability not acceptable")
        super(PingService, self).__init__(cap)

    def run(self, spec, check_interrupt):
         # unpack parameters
        period = spec.when().period().total_seconds()
        duration = spec.when().duration().total_seconds()
        if duration is not None and duration > 0:
            count = int(duration / period)
        else:
            count = None

        if spec.has_parameter("destination.ip4"):
            sipaddr = spec.get_parameter_value("source.ip4")
            dipaddr = spec.get_parameter_value("destination.ip4")
            ping_process = _ping4_process(sipaddr, dipaddr, period, count)
        elif spec.has_parameter("destination.ip6"):
            sipaddr = spec.get_parameter_value("source.ip6")
            dipaddr = spec.get_parameter_value("destination.ip6")
            ping_process = _ping6_process(sipaddr, dipaddr, period, count)
        else:
            raise ValueError("Missing destination")

        # read output from ping
        pings = []
        for line in ping_process.stdout:
            if check_interrupt():
                break
            oneping = _parse_ping_line(line.decode("utf-8"))
            if oneping is not None:
                print("ping "+repr(oneping))
                pings.append(oneping)
 
        # shut down and reap
        try:
            ping_process.kill()
        except OSError:
            pass
        ping_process.wait()

        # derive a result from the specification
        res = mplane.model.Result(specification=spec)
        out_file = open("./results/pingtest.txt","w")
        # put actual start and end time into result
        res.set_when(mplane.model.When(a = pings_start_time(pings), b = pings_end_time(pings)))

        # are we returning aggregates or raw numbers?
        if res.has_result_column("delay.twoway.icmp.us"):
            # raw numbers
            for i, oneping in enumerate(pings):
                res.set_result_value("delay.twoway.icmp.us", oneping.usec, i)
                out_file.write("microsec.delay.twoway.icmp" + "	" + "RTT_in_(microsec)usec=" + repr(oneping.usec) + "	" + repr(i) + '\n')
            if res.has_result_column("time"):
                for i, oneping in enumerate(pings):
                    res.set_result_value("time", oneping.time, i)
                    out_file.write("time" + "	" + "RTT_test_duration_seconds=" + repr(oneping.time) + "	" + repr(i) + '\n')
        else:
            # aggregates. single row.
            if res.has_result_column("delay.twoway.icmp.us.min"):
                res.set_result_value("delay.twoway.icmp.us.min", pings_min_delay(pings))
                out_file.write("microsec.delay.twoway.icmp.min" + "	" + "RTT_min_in_(microsec)usec=" + repr(pings_min_delay(pings)) + '\n')
            if res.has_result_column("delay.twoway.icmp.us.mean"):
                res.set_result_value("delay.twoway.icmp.us.mean", pings_mean_delay(pings))
                out_file.write("microsec.delay.twoway.icmp.mean" + "	" + "RTT_mean_in_(microsec)usec=" + repr(pings_mean_delay(pings)) + '\n')
            if res.has_result_column("delay.twoway.icmp.us.median"):
                res.set_result_value("delay.twoway.icmp.us.median", pings_median_delay(pings))
                out_file.write("microsec.delay.twoway.icmp.median" + "	" + "RTT_media_in_(microsec)usec=" + repr(pings_median_delay(pings)) + '\n')
            if res.has_result_column("delay.twoway.icmp.us.max"):
                res.set_result_value("delay.twoway.icmp.us.max", pings_max_delay(pings))
                out_file.write("microsec.delay.twoway.icmp.max" + "	" + "RTT_max_in_(microsec)usec=" + repr(pings_max_delay(pings)) + '\n')
            if res.has_result_column("delay.twoway.icmp.count"):
                res.set_result_value("delay.twoway.icmp.count", len(pings))
                out_file.write("microsec.delay.twoway.icmp.count" + "	" + "RTT_test_duration_seconds=" + repr(len(pings)) + '\n')
                
                out_file.close()
                #os.system("scp ./pingtest.txt USER@Repository:/repository/temp/")
        return res
        
class tcpslaService(mplane.scheduler.Service):
    def __init__(self, cap):
        # verify the capability is acceptable
        if not ((cap.has_parameter("source.ip4") or 
                 cap.has_parameter("source.ip6")) and
                (cap.has_parameter("destination.ip4") or 
                 cap.has_parameter("destination.ip6")) and
                (cap.has_result_column("mSLA.tcpBandwidth.download.iperf") or
                 cap.has_result_column("mSLA.tcpBandwidth.download.iperf.min") or
                 cap.has_result_column("mSLA.tcpBandwidth.download.iperf.mean") or                
                 cap.has_result_column("mSLA.tcpBandwidth.download.iperf.max") or
                 cap.has_result_column("mSLA.tcpBandwidth.download.iperf.timecountseconds"))):
            raise ValueError("capability not acceptable")
        super(tcpslaService, self).__init__(cap)

    def run(self, spec, check_interrupt):
         # unpack parameters
        period = spec.when().period().total_seconds()
        duration = spec.when().duration().total_seconds()
        if duration is not None and duration > 0:
            count = int(duration / period)
        else:
            count = None

        if spec.has_parameter("destination.ip4"):
            sipaddr = spec.get_parameter_value("source.ip4")
            dipaddr = spec.get_parameter_value("destination.ip4")
            tcpsla_process = _tcpsla4_process(sipaddr, dipaddr, period, count)
        elif spec.has_parameter("destination.ip6"):
            sipaddr = spec.get_parameter_value("source.ip6")
            dipaddr = spec.get_parameter_value("destination.ip6")
            tcpsla_process = _tcpsla6_process(sipaddr, dipaddr, period, count)
        else:
            raise ValueError("Missing destination")

        # read output from tcpsla
        tcpslas = []
        for line in tcpsla_process.stdout:
            if check_interrupt():
                break
            onetcpsla = _parse_tcpsla_line(line.decode("utf-8"))
            if onetcpsla is None:
               onetcpsla = _parse_tcpsla_line_after_9(line.decode("utf-8"))
            if onetcpsla is not None:
                print("tcpsla "+repr(onetcpsla))
                tcpslas.append(onetcpsla)


        # shut down and reap
        try:
            tcpsla_process.kill()
        except OSError:
            pass
        tcpsla_process.wait()

        # derive a result from the specification
        res = mplane.model.Result(specification=spec)
        out_file = open("./results/TCPtest.txt","w")
        # put actual start and end time into result
        res.set_when(mplane.model.When(a = tcpslas_start_time(tcpslas), b = tcpslas_end_time(tcpslas)))

        # are we returning aggregates or raw numbers?
        if res.has_result_column("mSLA.tcpBandwidth.download.iperf"):
            # raw numbers
            for i, onetcpsla in enumerate(tcpslas):
                res.set_result_value("mSLA.tcpBandwidth.download.iperf", onetcpsla.Bandwidth_Mbps, i)
                out_file.write("mSLA.tcpBandwidth.download.iperf" + "	" + "TCP-Bandwidth_Mbps=" + repr(onetcpsla.Bandwidth_Mbps) + "	" + repr(i) + '\n')
            if res.has_result_column("time"):
                for i, onetcpsla in enumerate(tcpslas):
                    res.set_result_value("time", onetcpsla.time, i)
                    out_file.write("time" + "	" + "TCP-test_duration_in_seconds=" + repr(onetcpsla.time) + "	" + repr(i) + '\n')
        else:
            # aggregates. single row.
            if res.has_result_column("mSLA.tcpBandwidth.download.iperf.min"):
                res.set_result_value("mSLA.tcpBandwidth.download.iperf.min", tcpslas_min_tcpBandwidth(tcpslas))
                out_file.write("mSLA.tcpBandwidth.download.iperf.min" + "	" + "TCP-Bandwidth_Mbps_min_sended="  + repr(tcpslas_min_tcpBandwidth(tcpslas)) + '\n')
            if res.has_result_column("mSLA.tcpBandwidth.download.iperf.mean"):
                res.set_result_value("mSLA.tcpBandwidth.download.iperf.mean", tcpslas_mean_tcpBandwidth(tcpslas))
                out_file.write("mSLA.tcpBandwidth.download.iperf.mean" + "	" + "TCP-Bandwidth_Mbps_mean_sended="  +repr(tcpslas_mean_tcpBandwidth(tcpslas)) + '\n')
            if res.has_result_column("mSLA.tcpBandwidth.download.iperf.median"):
                res.set_result_value("mSLA.tcpBandwidth.download.iperf.median", tcpslas_median_tcpBandwidth(tcpslas))
                out_file.write("mSLA.tcpBandwidth.download.iperf.median" + "	" + "TCP-Bandwidth_Mbps_median_sended="  +repr(tcpslas_median_tcpBandwidth(tcpslas)) + '\n')
            if res.has_result_column("mSLA.tcpBandwidth.download.iperf.max"):
                res.set_result_value("mSLA.tcpBandwidth.download.iperf.max", tcpslas_max_tcpBandwidth(tcpslas))
                out_file.write("mSLA.tcpBandwidth.download.iperf.max" + "	" + "TCP-Bandwidth_Mbps_max_sended="  +repr(tcpslas_max_tcpBandwidth(tcpslas)) + '\n')
            if res.has_result_column("mSLA.tcpBandwidth.download.iperf.timecountseconds"):
                res.set_result_value("mSLA.tcpBandwidth.download.iperf.timecountseconds", len(tcpslas))
                out_file.write("mSLA.tcpBandwidth.download.iperf.timecountseconds" + "	" + "TCP_test_duration_in_seconds"  +repr(len(tcpslas)) + '\n')
                #os.system("scp ./TCPtest.txt USER@Repository:/repository/temp/")
                out_file.close()
        return res
        
class udpslaService(mplane.scheduler.Service):
    def __init__(self, cap):
        # verify the capability is acceptable
        if not ((cap.has_parameter("source.ip4") or 
                 cap.has_parameter("source.ip6")) and
                (cap.has_parameter("destination.ip4") or 
                 cap.has_parameter("destination.ip6")) and
                (cap.has_result_column("mSLA.udpCapacity.download.iperf") or
                 cap.has_result_column("mSLA.udpCapacity.download.iperf.min") or
                 cap.has_result_column("mSLA.udpCapacity.download.iperf.mean") or                
                 cap.has_result_column("mSLA.udpCapacity.download.iperf.max") or
                 cap.has_result_column("mSLA.udpCapacity.download.iperf.jitter") or
                 cap.has_result_column("mSLA.udpCapacity.download.iperf.error") or
                 cap.add_result_column("mSLA-Bandwidth_mean_Mbps-Correct-UDP") or
                 cap.has_result_column("mSLA.udpCapacity.download.iperf.timecountseconds"))):
            raise ValueError("capability not acceptable")
        super(udpslaService, self).__init__(cap)

    def run(self, spec, check_interrupt):
         # unpack parameters
        period = spec.when().period().total_seconds()
        duration = spec.when().duration().total_seconds()
        if duration is not None and duration > 0:
            count = int(duration / period)
        else:
            count = None

        if spec.has_parameter("destination.ip4"):
            sipaddr = spec.get_parameter_value("source.ip4")
            dipaddr = spec.get_parameter_value("destination.ip4")
            udpsla_process = _udpsla4_process(sipaddr, dipaddr, period, count=round(int((count / 1)-2)))
        elif spec.has_parameter("destination.ip6"):
            sipaddr = spec.get_parameter_value("source.ip6")
            dipaddr = spec.get_parameter_value("destination.ip6")
            udpsla_process = _udpsla6_process(sipaddr, dipaddr, period, count=round(int((count / 1)-2)))
        else:
            raise ValueError("Missing destination")

        # read output from udpsla
        udpslas = []
        Jitter_ms = -1
        Bandwidth_mean_Mbps = -1
        Error_prc = -1
        for line in udpsla_process.stdout:
            if check_interrupt():
                break
            oneudpsla = _parse_udpsla_line(line.decode("utf-8"))
#            print("udpsla "+repr(oneudpsla))
            if oneudpsla is None:
               oneudpsla = _parse_udpsla_line_after_9(line.decode("utf-8"))
            oneudpsla_last =_parse_udpsla_last_line(line.decode("utf-8"))
#            print("udpsla_last "+repr(oneudpsla))
            if oneudpsla_last is None:
               oneudpsla_last = _parse_udpsla_last_line_after_9(line.decode("utf-8"))
            if oneudpsla is not None:
                print("udpsla "+repr(oneudpsla))
                udpslas.append(oneudpsla)
            if oneudpsla_last is not None:
                print("udpslareport "+repr(oneudpsla_last))
                Jitter_ms=oneudpsla_last.Jitter_ms
                Error_prc=oneudpsla_last.Error_prc
                Bandwidth_mean_Mbps=oneudpsla_last.Bandwidth_mean_Mbps

        try:
            udpsla_process.kill()
        except OSError:
            pass
        udpsla_process.wait()
        res = mplane.model.Result(specification=spec)
        out_file = open("./results/UDPtest.txt","w")

        # put actual start and end time into result
        res.set_when(mplane.model.When(a = udpslas_start_time(udpslas), b = udpslas_end_time(udpslas)))

        if Jitter_ms is None:
           Jitter_ms = -1
        if Error_prc is None:
           Error_prc = -1
        if Bandwidth_mean_Mbps is None:
           Bandwidth_mean_Mbps = -1
        if res.has_result_column("mSLA.udpCapacity.download.iperf"):
            # raw numbers
            for i, oneudpsla in enumerate(udpslas):

                res.set_result_value("mSLA.udpCapacity.download.iperf", oneudpsla.Bandwidth_Mbps, i)
                out_file.write("mSLA.udpCapacity.download.iperf" + "	" + "UDP-Bandwidth_Mbps=" + repr(oneudpsla.Bandwidth_Mbps) + "	" + repr(i) + '\n')
                res.set_result_value("mSLA.udpCapacity.download.iperf.jitter", Jitter_ms)
                out_file.write("mSLA.udpCapacity.download.iperf.jitter" + "	" + "UDP-Jitter_in_ms=" + repr(Jitter_ms) + "	" + repr(i) + '\n')
                res.set_result_value("mSLA.udpCapacity.download.iperf.error", Error_prc)
                out_file.write("mSLA.udpCapacity.download.iperf.error" + "	" + "UDP-dagram_Error_in_perc=" + repr(Error_prc) + "	" + repr(i) + '\n')
                res.set_result_value("mSLA-Bandwidth_mean_Mbps-Correct-UDP", Bandwidth_mean_Mbps)
                out_file.write("mSLA-Bandwidth_mean_Mbps-Correct-UDP" + "	" + "UDP-Bandwidth_mean_Mbps_Correct=" + repr(Bandwidth_mean_Mbps) + "	" + repr(i) + '\n')
            if res.has_result_column("time"):
                for i, oneudpsla in enumerate(udpslas):
                    res.set_result_value("time", oneudpsla.time, i)
                    out_file.write("time" + "	" + repr(oneudpsla.time) + "	" + repr(i) + '\n')
        else:
            # aggregates. single row.
            if res.has_result_column("mSLA.udpCapacity.download.iperf.min"):
                res.set_result_value("mSLA.udpCapacity.download.iperf.min", udpslas_min_udpCapacity(udpslas))
                out_file.write("mSLA.udpCapacity.download.iperf.min" + "	" + "UDP-Bandwidth_Mbps_min_sended="  + repr(udpslas_min_udpCapacity(udpslas)) + '\n')
            if res.has_result_column("mSLA.udpCapacity.download.iperf.mean"):
                res.set_result_value("mSLA.udpCapacity.download.iperf.mean", udpslas_mean_udpCapacity(udpslas))
                out_file.write("mSLA.udpCapacity.download.iperf.mean" + "	" + "UDP-Bandwidth_Mbps_mean_sended=" + repr(udpslas_mean_udpCapacity(udpslas)) + '\n')
            if res.has_result_column("mSLA.udpCapacity.download.iperf.median"):
                res.set_result_value("mSLA.udpCapacity.download.iperf.median", udpslas_median_udpCapacity(udpslas))
                out_file.write("mSLA.udpCapacity.download.iperf.median" + "	" + "UDP-Bandwidth_Mbps_median_sended=" + repr(udpslas_median_udpCapacity(udpslas)) + '\n')
            if res.has_result_column("mSLA.udpCapacity.download.iperf.max"):
                res.set_result_value("mSLA.udpCapacity.download.iperf.max", udpslas_max_udpCapacity(udpslas))
                out_file.write("mSLA.udpCapacity.download.iperf.max" + "	" + "UDP-Bandwidth_Mbps_max_sended=" + repr(udpslas_max_udpCapacity(udpslas)) + '\n')
            if res.has_result_column("mSLA.udpCapacity.download.iperf.timecountseconds"):
                res.set_result_value("mSLA.udpCapacity.download.iperf.timecountseconds", udpslas_max_time_udpCapacity(udpslas))
                out_file.write("mSLA.udpCapacity.download.iperf.timecountseconds" + "	" + "UDP-number_of_Seconds=" +  repr(udpslas_max_time_udpCapacity(udpslas)) + '\n')
            if res.has_result_column("mSLA.udpCapacity.download.iperf.jitter"):
                res.set_result_value("mSLA.udpCapacity.download.iperf.jitter",Jitter_ms)
                out_file.write("mSLA.udpCapacity.download.iperf.jitter" + "	" + "UDP-Jitter_in_ms=" +  repr(Jitter_ms) + '\n')
            if res.has_result_column("mSLA.udpCapacity.download.iperf.error"):
                res.set_result_value("mSLA.udpCapacity.download.iperf.error", Error_prc)
                out_file.write("mSLA.udpCapacity.download.iperf.error" + "	" + "UDP-dagram_Error_in_perc=" +  repr(Error_prc) + '\n')
            if res.has_result_column("mSLA-Bandwidth_mean_Mbps-Correct-UDP"):
                res.set_result_value("mSLA-Bandwidth_mean_Mbps-Correct-UDP", Bandwidth_mean_Mbps)
                out_file.write("mSLA-Bandwidth_mean_Mbps-Correct-UDP" + "	" + "UDP-Bandwidth_mean_Mbps_Correct=" +  repr(Bandwidth_mean_Mbps) + '\n')

                #os.system("scp ./UDPtest.txt USER@Repository:/repository/temp/")
                out_file.close()
        return res

class mSLAcertService(mplane.scheduler.Service):
    def __init__(self, cap):
        # verify the capability is acceptable
        if not ((cap.has_parameter("source.ip4") or 
                 cap.has_parameter("source.ip6")) and
                (cap.has_parameter("destination.ip4") or 
                 cap.has_parameter("destination.ip6")) and
                (cap.has_result_column("delay.twoway.icmp.us") or
                 cap.has_result_column("delay.twoway.icmp.us.min") or
                 cap.has_result_column("delay.twoway.icmp.us.mean") or                
                 cap.has_result_column("delay.twoway.icmp.us.max") or
                 cap.has_result_column("delay.twoway.icmp.count") or
                 cap.has_result_column("mSLA.tcpBandwidth.download.iperf") or
                 cap.has_result_column("mSLA.tcpBandwidth.download.iperf.min") or
                 cap.has_result_column("mSLA.tcpBandwidth.download.iperf.mean") or                
                 cap.has_result_column("mSLA.tcpBandwidth.download.iperf.max") or
                 cap.has_result_column("mSLA.tcpBandwidth.download.iperf.timecountseconds") or
                 cap.has_result_column("mSLA.udpCapacity.download.iperf") or
                 cap.has_result_column("mSLA.udpCapacity.download.iperf.min") or
                 cap.has_result_column("mSLA.udpCapacity.download.iperf.mean") or                
                 cap.has_result_column("mSLA.udpCapacity.download.iperf.max") or
                 cap.has_result_column("mSLA.udpCapacity.download.iperf.jitter") or
                 cap.has_result_column("mSLA.udpCapacity.download.iperf.error") or
                 cap.add_result_column("mSLA-Bandwidth_mean_Mbps-Correct-UDP") or
                 cap.has_result_column("mSLA.udpCapacity.download.iperf.timecountseconds"))):
            raise ValueError("capability not acceptable")
        super(mSLAcertService, self).__init__(cap)

               
    def run(self, spec, check_interrupt):
         # unpack parameters
        period = spec.when().period().total_seconds()
        duration = spec.when().duration().total_seconds()
        if duration is not None and duration > 0:
            count = int(duration / period)

        else:
            count = None
        
        if spec.has_parameter("destination.ip4"):
            sipaddr = spec.get_parameter_value("source.ip4")
            dipaddr = spec.get_parameter_value("destination.ip4")
            ping_process = _ping4_process(sipaddr, dipaddr, period, count=round(int(count / 3)))
        elif spec.has_parameter("destination.ip6"):
            sipaddr = spec.get_parameter_value("source.ip6")
            dipaddr = spec.get_parameter_value("destination.ip6")
            ping_process = _ping6_process(sipaddr, dipaddr, period, count=round(int(count / 3)))
        else:
            raise ValueError("Missing destination")

        # read output from ping
        pings = []
        for line in ping_process.stdout:
            if check_interrupt():
                break
            oneping = _parse_ping_line(line.decode("utf-8"))
            if oneping is not None:
                print("ping "+repr(oneping))
                pings.append(oneping)
 
        # shut down and reap
        try:
            ping_process.kill()
        except OSError:
            pass
        ping_process.wait()

            
        
        if spec.has_parameter("destination.ip4"):
            sipaddr = spec.get_parameter_value("source.ip4")
            dipaddr = spec.get_parameter_value("destination.ip4")
            tcpsla_process = _tcpsla4_process(sipaddr, dipaddr, period, count=round(int(count / 3)))
        elif spec.has_parameter("destination.ip6"):
            sipaddr = spec.get_parameter_value("source.ip6")
            dipaddr = spec.get_parameter_value("destination.ip6")
            tcpsla_process = _tcpsla6_process(sipaddr, dipaddr, period, count=round(int(count / 3)))
        else:
            raise ValueError("Missing destination")

        # read output from tcpsla
        tcpslas = []
        for line in tcpsla_process.stdout:
            if check_interrupt():
                break
            onetcpsla = _parse_tcpsla_line(line.decode("utf-8"))
            if onetcpsla is None:
               onetcpsla = _parse_tcpsla_line_after_9(line.decode("utf-8"))
            if onetcpsla is not None:
                print("tcpsla "+repr(onetcpsla))
                tcpslas.append(onetcpsla)
 
        # shut down and reap
        try:
            tcpsla_process.kill()
        except OSError:
            pass
        tcpsla_process.wait()
                    
                    
                    
        if spec.has_parameter("destination.ip4"):
            sipaddr = spec.get_parameter_value("source.ip4")
            dipaddr = spec.get_parameter_value("destination.ip4")
            udpsla_process = _udpsla4_process(sipaddr, dipaddr, period, count=round(int((count / 3)-2)))
        elif spec.has_parameter("destination.ip6"):
            sipaddr = spec.get_parameter_value("source.ip6")
            dipaddr = spec.get_parameter_value("destination.ip6")
            udpsla_process = _udpsla6_process(sipaddr, dipaddr, period, count=round(int((count / 3)-2)))
        else:
            raise ValueError("Missing destination")
            
        udpslas = []
        Jitter_ms = -1
        Bandwidth_mean_Mbps = -1
        Error_prc = -1
        for line in udpsla_process.stdout:
            if check_interrupt():
                break
            oneudpsla = _parse_udpsla_line(line.decode("utf-8"))
            if oneudpsla is None:
               oneudpsla = _parse_udpsla_line_after_9(line.decode("utf-8"))
            oneudpsla_last =_parse_udpsla_last_line(line.decode("utf-8"))
            if oneudpsla_last is None:
               oneudpsla_last = _parse_udpsla_last_line_after_9(line.decode("utf-8"))
            if oneudpsla is not None:
                print("udpsla "+repr(oneudpsla))
                udpslas.append(oneudpsla)
            if oneudpsla_last is not None:
                print("udpslareport "+repr(oneudpsla_last))
                Jitter_ms=oneudpsla_last.Jitter_ms
                Error_prc=oneudpsla_last.Error_prc
                Bandwidth_mean_Mbps=oneudpsla_last.Bandwidth_mean_Mbps

        try:
            udpsla_process.kill()
        except OSError:
            pass
        udpsla_process.wait()

        # are we returning aggregates or raw numbers?
        if Jitter_ms is None:
           Jitter_ms = -1
        if Error_prc is None:
           Error_prc = -1
        if Bandwidth_mean_Mbps is None:
           Bandwidth_mean_Mbps = -1

 # derive a result from the specification
        res = mplane.model.Result(specification=spec)
        out_file = open("./results/100ms_msla.txt","w")
        # put actual start and end time into result
        res.set_when(mplane.model.When(a = pings_start_time(pings), b = pings_end_time(pings)))

        # are we returning aggregates or raw numbers?
        if res.has_result_column("delay.twoway.icmp.us"):
            # raw numbers
            for i, oneping in enumerate(pings):
                res.set_result_value("delay.twoway.icmp.us", oneping.usec, i)
                out_file.write("microsec.delay.twoway.icmp" + "	" + "RTT_in_(microsec)usec=" + repr(oneping.usec) + "	" + repr(i) + '\n')
            if res.has_result_column("time"):
                for i, oneping in enumerate(pings):
                    res.set_result_value("time", oneping.time, i)
                    out_file.write("time" + "	" + "RTT_test_duration_seconds=" + repr(oneping.time) + "	" + repr(i) + '\n')
                    
        # derive a result from the specification
        res = mplane.model.Result(specification=spec)
#        out_file = open("./TCPtest.txt","w")
        # put actual start and end time into result
        res.set_when(mplane.model.When(a = tcpslas_start_time(tcpslas), b = tcpslas_end_time(tcpslas)))

        # are we returning aggregates or raw numbers?
        if res.has_result_column("mSLA.tcpBandwidth.download.iperf"):
            # raw numbers
            for i, onetcpsla in enumerate(tcpslas):
                res.set_result_value("mSLA.tcpBandwidth.download.iperf", onetcpsla.Bandwidth_Mbps, i)
                out_file.write("mSLA.tcpBandwidth.download.iperf" + "	" + "TCP-Bandwidth_Mbps=" + repr(onetcpsla.Bandwidth_Mbps) + "	" + repr(i) + '\n')
            if res.has_result_column("time"):
                for i, onetcpsla in enumerate(tcpslas):
                    res.set_result_value("time", onetcpsla.time, i)
                    out_file.write("time" + "	" + "TCP-test_duration_in_seconds=" + repr(onetcpsla.time) + "	" + repr(i) + '\n')
        
        # derive a result from the specification
        res = mplane.model.Result(specification=spec)
#        out_file = open("./UDPtest.txt","w")

        # put actual start and end time into result
        res.set_when(mplane.model.When(a = udpslas_start_time(udpslas), b = udpslas_end_time(udpslas)))

        # are we returning aggregates or raw numbers?
        if res.has_result_column("mSLA.udpCapacity.download.iperf"):
            # raw numbers
            for i, oneudpsla in enumerate(udpslas):
                res.set_result_value("delay.twoway.icmp.us", oneping.usec, i)
                out_file.write("microsec.delay.twoway.icmp" + "	" + "RTT_in_(microsec)usec=" + repr(oneping.usec) + "	" + repr(i) + '\n')
                res.set_result_value("mSLA.tcpBandwidth.download.iperf", onetcpsla.Bandwidth_Mbps, i)
                out_file.write("mSLA.tcpBandwidth.download.iperf" + "	" + "TCP-Bandwidth_Mbps=" + repr(onetcpsla.Bandwidth_Mbps) + "	" + repr(i) + '\n')
                res.set_result_value("mSLA.udpCapacity.download.iperf", oneudpsla.Bandwidth_Mbps, i)
                out_file.write("mSLA.udpCapacity.download.iperf" + "	" + "UDP-Bandwidth_Mbps=" + repr(oneudpsla.Bandwidth_Mbps) + "	" + repr(i) + '\n')
                res.set_result_value("mSLA.udpCapacity.download.iperf.jitter", Jitter_ms)
                out_file.write("mSLA.udpCapacity.download.iperf.jitter" + "	" + "UDP-Jitter_in_ms=" + repr(Jitter_ms) + "	" + repr(i) + '\n')
                res.set_result_value("mSLA.udpCapacity.download.iperf.error", Error_prc)
                out_file.write("mSLA.udpCapacity.download.iperf.error" + "	" + "UDP-dagram_Error_in_prc=" + repr(Error_prc) + "	" + repr(i) + '\n')
                res.set_result_value("mSLA-Bandwidth_mean_Mbps-Correct-UDP", Bandwidth_mean_Mbps)
                out_file.write("mSLA-Bandwidth_mean_Mbps-Correct-UDP" + "	" + "UDP-Bandwidth_mean_Mbps_Correct=" + repr(Bandwidth_mean_Mbps) + "	" + repr(i) + '\n')

            if res.has_result_column("time"):
                for i, oneudpsla in enumerate(udpslas):
                    res.set_result_value("time", oneudpsla.time, i)
                    out_file.write("time" + "	" + "UDP_test_duration_in_seconds" + repr(oneudpsla.time) + "	" + repr(i) + '\n')
        else:
            # aggregates. single row.
            if res.has_result_column("delay.twoway.icmp.us.min"):
                res.set_result_value("delay.twoway.icmp.us.min", pings_min_delay(pings))
                out_file.write("microsec.delay.twoway.icmp.min" + "	" + "RTT_min_in_(microsec)usec=" + repr(pings_min_delay(pings)) + '\n')
            if res.has_result_column("delay.twoway.icmp.us.mean"):
                res.set_result_value("delay.twoway.icmp.us.mean", pings_mean_delay(pings))
                out_file.write("microsec.delay.twoway.icmp.mean" + "	" + "RTT_mean_in_(microsec)usec=" + repr(pings_mean_delay(pings)) + '\n')
            if res.has_result_column("delay.twoway.icmp.us.median"):
                res.set_result_value("delay.twoway.icmp.us.median", pings_median_delay(pings))
                out_file.write("microsec.delay.twoway.icmp.median" + "	" + "RTT_media_in_(microsec)usec=" + repr(pings_median_delay(pings)) + '\n')
            if res.has_result_column("delay.twoway.icmp.us.max"):
                res.set_result_value("delay.twoway.icmp.us.max", pings_max_delay(pings))
                out_file.write("microsec.delay.twoway.icmp.max" + "	" + "RTT_max_in_(microsec)usec=" + repr(pings_max_delay(pings)) + '\n')
            if res.has_result_column("delay.twoway.icmp.count"):
                res.set_result_value("delay.twoway.icmp.count", len(pings))
                out_file.write("microsec.delay.twoway.icmp.count" + "	" + "RTT_test_duration_seconds=" + repr(len(pings)) + '\n')
            if res.has_result_column("mSLA.tcpBandwidth.download.iperf.min"):
                res.set_result_value("mSLA.tcpBandwidth.download.iperf.min", tcpslas_min_tcpBandwidth(tcpslas))
                out_file.write("mSLA.tcpBandwidth.download.iperf.min" + "	" + "TCP-Bandwidth_Mbps_min_sended="  + repr(tcpslas_min_tcpBandwidth(tcpslas)) + '\n')
            if res.has_result_column("mSLA.tcpBandwidth.download.iperf.mean"):
                res.set_result_value("mSLA.tcpBandwidth.download.iperf.mean", tcpslas_mean_tcpBandwidth(tcpslas))
                out_file.write("mSLA.tcpBandwidth.download.iperf.mean" + "	" + "TCP-Bandwidth_Mbps_mean_sended="  +repr(tcpslas_mean_tcpBandwidth(tcpslas)) + '\n')
            if res.has_result_column("mSLA.tcpBandwidth.download.iperf.median"):
                res.set_result_value("mSLA.tcpBandwidth.download.iperf.median", tcpslas_median_tcpBandwidth(tcpslas))
                out_file.write("mSLA.tcpBandwidth.download.iperf.median" + "	" + "TCP-Bandwidth_Mbps_median_sended="  +repr(tcpslas_median_tcpBandwidth(tcpslas)) + '\n')
            if res.has_result_column("mSLA.tcpBandwidth.download.iperf.max"):
                res.set_result_value("mSLA.tcpBandwidth.download.iperf.max", tcpslas_max_tcpBandwidth(tcpslas))
                out_file.write("mSLA.tcpBandwidth.download.iperf.max" + "	" + "TCP-Bandwidth_Mbps_max_sended="  +repr(tcpslas_max_tcpBandwidth(tcpslas)) + '\n')
            if res.has_result_column("mSLA.tcpBandwidth.download.iperf.timecountseconds"):
                res.set_result_value("mSLA.tcpBandwidth.download.iperf.timecountseconds", len(tcpslas))
                out_file.write("mSLA.tcpBandwidth.download.iperf.timecountseconds" + "	" + "TCP_test_duration_in_seconds"  +repr(len(tcpslas)) + '\n')
            if res.has_result_column("mSLA.udpCapacity.download.iperf.min"):
                res.set_result_value("mSLA.udpCapacity.download.iperf.min", udpslas_min_udpCapacity(udpslas))
                out_file.write("mSLA.udpCapacity.download.iperf.min" + "	" + "UDP-Bandwidth_Mbps_min_sended="  + repr(udpslas_min_udpCapacity(udpslas)) + '\n')
            if res.has_result_column("mSLA.udpCapacity.download.iperf.mean"):
                res.set_result_value("mSLA.udpCapacity.download.iperf.mean", udpslas_mean_udpCapacity(udpslas))
                out_file.write("mSLA.udpCapacity.download.iperf.mean" + "	" + "UDP-Bandwidth_Mbps_mean_sended=" + repr(udpslas_mean_udpCapacity(udpslas)) + '\n')
            if res.has_result_column("mSLA.udpCapacity.download.iperf.median"):
                res.set_result_value("mSLA.udpCapacity.download.iperf.median", udpslas_median_udpCapacity(udpslas))
                out_file.write("mSLA.udpCapacity.download.iperf.median" + "	" + "UDP-Bandwidth_Mbps_median_sended=" + repr(udpslas_median_udpCapacity(udpslas)) + '\n')
            if res.has_result_column("mSLA.udpCapacity.download.iperf.max"):
                res.set_result_value("mSLA.udpCapacity.download.iperf.max", udpslas_max_udpCapacity(udpslas))
                out_file.write("mSLA.udpCapacity.download.iperf.max" + "	" + "UDP-Bandwidth_Mbps_max_sended=" + repr(udpslas_max_udpCapacity(udpslas)) + '\n')
            if res.has_result_column("mSLA.udpCapacity.download.iperf.timecountseconds"):
                res.set_result_value("mSLA.udpCapacity.download.iperf.timecountseconds", udpslas_max_time_udpCapacity(udpslas))
                out_file.write("mSLA.udpCapacity.download.iperf.timecountseconds" + "	" + "UDP_test_duration_in_seconds" +  repr(udpslas_max_time_udpCapacity(udpslas)) + '\n')
            if res.has_result_column("mSLA.udpCapacity.download.iperf.jitter"):
                res.set_result_value("mSLA.udpCapacity.download.iperf.jitter",Jitter_ms)
                out_file.write("mSLA.udpCapacity.download.iperf.jitter" + "	" + "UDP-Jitter_in_ms=" +  repr(Jitter_ms) + '\n')
            if res.has_result_column("mSLA.udpCapacity.download.iperf.error"):
                res.set_result_value("mSLA.udpCapacity.download.iperf.error", Error_prc)
                out_file.write("mSLA.udpCapacity.download.iperf.error" + "	" + "UDP-dagram_Error_in_perc=" +  repr(Error_prc) + '\n')
            if res.has_result_column("mSLA-Bandwidth_mean_Mbps-Correct-UDP"):
                res.set_result_value("mSLA-Bandwidth_mean_Mbps-Correct-UDP", Bandwidth_mean_Mbps)
                out_file.write("mSLA-Bandwidth_mean_Mbps-Correct-UDP" + "	" + "UDP-Bandwidth_mean_Mbps_Correct=" +  repr(Bandwidth_mean_Mbps) + '\n')
                #os.system("scp ./UDPtest.txt USER@Repository:/repository/temp/")
                out_file.close()
        return res
