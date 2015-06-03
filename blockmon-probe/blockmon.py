# mPlane Protocol Reference Implementation
# Blockmon component code
#
# (c) 2013-2014 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Maurizio Dusi
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

import sys
import os
import subprocess
import re
import configparser
import argparse
from datetime import datetime

pri = os.getenv('MPLANE_RI')
if pri is None:
    raise ValueError("environment variable MPLANE_RI has not been set")
sys.path.append(pri)

import mplane.model
import mplane.scheduler
import mplane.utils
import mplane.component

_blockmon_packets_re = re.compile("packets=(\d+),bytes=(\d+)")
_blockmon_flows_re = re.compile("packets=(\d+),bytes=(\d+),start=(\d+),end=(\d+),duration.ms=(\d+),source.ip4=(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}),source.port=(\d+),destination.ip4=(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}),destination.port=(\d+)")


_progpath = "."
_progname = "blockmon"

_module_path = os.path.dirname(os.path.abspath(__file__))
_capabilitypath = os.path.join(_module_path, "capabilities")

"""
Implements Blockmon capabilities and services

"""


def services():
    services = []
    services.append(blockmonService(packets_capability()))
    services.append(blockmonService(flows_capability()))
    services.append(blockmonService(tcpflows_capability()))
    services.append(blockmonService(tstat_capability()))
    return services


def packets_capability():
    cap = mplane.model.Capability(label="blockmon-packets", when="now ... future / 1s")
    cap.add_metadata("System_type", "blockmon")
    cap.add_metadata("System_ID", "blockmon-Proxy")
    cap.add_metadata("System_version", "0.1")

    cap.add_result_column("time")
    cap.add_result_column("packets.ip")
    return cap


def flows_capability():
    cap = mplane.model.Capability(label="blockmon-flows", when="now ... future / 1s")
    cap.add_metadata("System_type", "blockmon")
    cap.add_metadata("System_ID", "blockmon-Proxy")
    cap.add_metadata("System_version", "0.1")

    cap.add_result_column("time")
    cap.add_result_column("start")
    cap.add_result_column("end")
    cap.add_result_column("duration.ms")
    cap.add_result_column("packets.ip")
    cap.add_result_column("source.ip4")
    cap.add_result_column("source.port")
    cap.add_result_column("destination.ip4")
    cap.add_result_column("destination.port")
    return cap


def tcpflows_capability():
    cap = mplane.model.Capability(label="blockmon-flows-tcp", when="now ... future / 1s")
    cap.add_metadata("System_type", "blockmon")
    cap.add_metadata("System_ID", "blockmon-Proxy")
    cap.add_metadata("System_version", "0.1")

    cap.add_result_column("time")
    cap.add_result_column("start")
    cap.add_result_column("end")
    cap.add_result_column("duration.ms")
    cap.add_result_column("packets.tcp")
    cap.add_result_column("source.ip4")
    cap.add_result_column("source.port")
    cap.add_result_column("destination.ip4")
    cap.add_result_column("destination.port")
    return cap


def tstat_capability():
    cap = mplane.model.Capability(label="blockmon-tstat", when="now ... future / 1s")
    cap.add_metadata("System_type", "blockmon")
    cap.add_metadata("System_ID", "blockmon-Proxy")
    cap.add_metadata("System_version", "0.1")

    return cap


def _parse_blockmon_packets_line(line):
    m = _blockmon_packets_re.search(line)
    if m is None:
        print(line)
        return None
    mg = m.groups()
    ret = {'time': datetime.utcnow(),
           'packets.ip': int(mg[0]), 'bytes': int(mg[1])}
    return ret


def _parse_blockmon_flows_line(line):
    m = _blockmon_flows_re.search(line)
    if m is None:
        print(line)
        return None
    mg = m.groups()
    start = datetime.fromtimestamp(int(mg[2])/1e6)
    end = datetime.fromtimestamp(int(mg[3])/1e6)

    ret = {'time': datetime.utcnow(),
           'packets.ip': int(mg[0]), 'bytes': int(mg[1]),
           'start': start, 'end': end, 'duration.ms': int(mg[4]),
           'source.ip4': mg[5], 'source.port': int(mg[6]),
           'destination.ip4': mg[7], 'destination.port': int(mg[8])}
    return ret


def _parse_blockmon_flowstcp_line(line):
    m = _blockmon_flows_re.search(line)
    if m is None:
        print(line)
        return None
    mg = m.groups()
    start = datetime.fromtimestamp(int(mg[2])/1e6)
    end = datetime.fromtimestamp(int(mg[3])/1e6)

    ret = {'time': datetime.utcnow(),
           'packets.tcp': int(mg[0]), 'bytes': int(mg[1]),
           'start': start, 'end': end, 'duration.ms': int(mg[4]),
           'source.ip4': mg[5], 'source.port': int(mg[6]),
           'destination.ip4': mg[7], 'destination.port': int(mg[8])}
    return ret


def _parse_blockmon_tstat_line(line):
    print(line)
    return {}


def _parse_blockmon_line(line, spec):
    out = line.rstrip('\n').split('\t')
    if len(out) != 3:
        return None
    block_name, log_level, msg = out
    if spec == "blockmon-packets":
        ret = _parse_blockmon_packets_line(msg)
    elif spec == "blockmon-flows":
        ret = _parse_blockmon_flows_line(msg)
    elif spec == "blockmon-flows-tcp":
        ret = _parse_blockmon_flowstcp_line(msg)
    elif spec == "blockmon-tstat":
        ret = _parse_blockmon_tstat_line(msg)
    else:
        print("capability {0} is not implemented".format(spec))
        return None
    return ret


def _blockmon_process(composition):
    composition += '.xml'
    blockmon_argv = [os.path.join(_progpath, _progname)]
    blockmon_argv += [os.path.join(_capabilitypath, composition)]
    print("running " + " ".join(blockmon_argv))
    return subprocess.Popen(blockmon_argv, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)


class blockmonService(mplane.scheduler.Service):
    """
    This class handles the capabilities exposed by the proxy:
    executes them, and fills the results

    """

    def __init__(self, cap):
        super(blockmonService, self).__init__(cap)

    def run(self, spec, check_interrupt):
        """
        Execute this Service

        """

        start_time = datetime.utcnow()

        measure_process = _blockmon_process(spec._label)

        rets = []
        for line in measure_process.stdout:
            if check_interrupt():
                break
            # print(line.decode("utf-8"))
            ret = _parse_blockmon_line(line.decode("utf-8"), spec._label)
            if ret is None:
                continue
            rets.append(ret)

        measure_process.terminate()

        end_time = datetime.utcnow()
        print("specification {0}: start = {1} end = {2}".format(spec._label, start_time, end_time))

        res = mplane.model.Result(specification=spec)
        res.set_when(mplane.model.When(a=start_time, b=end_time))

        labels = ["time", "start", "end", "duration.ms",
                  "packets.ip", "packets.tcp",
                  "source.ip4", "source.port",
                  "destination.ip4", "destination.port"]
        for label in labels:
            if res.has_result_column(label):
                for i, ret in enumerate(rets):
                    print(label, ret[label])
                    res.set_result_value(label, ret[label], i)
        # print(mplane.model.unparse_json(res))
        return res


def main():
    """docstring for main"""
    global args
    parser = argparse.ArgumentParser(description='run a Blockmon mPlane proxy')
    parser.add_argument('--config', metavar='conf-file', dest='CONF',
                        help='Configuration file for the component')
    args = parser.parse_args()
    # check if conf file parameter has been inserted in the command line
    if not args.CONF:
        print('\nERROR: missing --config\n')
        parser.print_help()
        exit(1)

    # Read the configuration file
    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(mplane.utils.search_path(args.CONF))

    if config["component"]["workflow"] == "component-initiated":
        component = mplane.component.InitiatorHttpComponent(config)
    elif config["component"]["workflow"] == "client-initiated":
        component = mplane.component.ListenerHttpComponent(config)
    else:
        raise ValueError("workflow setting in " + args.CONF + " can only be 'client-initiated' or 'component-initiated'")

if __name__ == '__main__':
    main()
