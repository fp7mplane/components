# mPlane Protocol Reference Implementation
# Blockmon controller code
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
import configparser
import argparse
from datetime import datetime

from txjsonrpc.web.jsonrpc import Proxy
import jsonpickle
from twisted.internet import reactor, defer

from core.returnvalue import *

pri = os.getenv('MPLANE_RI')
if pri is None:
    raise ValueError("environment variable MPLANE_RI has not been set")
sys.path.append(pri)

import mplane.model
import mplane.scheduler
import mplane.utils
import mplane.component

_module_path = os.path.dirname(os.path.abspath(__file__))
_capabilitypath = os.path.join(_module_path, "capabilities")

_controller_address = "127.0.0.1"
_controller_port = 7070
_controller_daemon = Proxy('http://%s:%d/' % (_controller_address,
                                              _controller_port))

"""
Implements Blockmon Controller capabilities and services

"""


def services():
    services = []
    services.append(blockmonControllerService(packets_capability()))
    return services


def packets_capability():
    cap = mplane.model.Capability(label="blockmon-controller-packets",
                                  when="now ... future / 1s")
    cap.add_metadata("System_type", "blockmon-controller")
    cap.add_metadata("System_ID", "blockmon-controller-Proxy")
    cap.add_metadata("System_version", "0.1")

    cap.add_result_column("time")
    return cap


def print_results(value):
    r = jsonpickle.decode(value)
    print(str(r))
    reactor.callFromThread(reactor.stop)
    return value


def print_error(error):
    print(error)
    reactor.callFromThread(reactor.stop)
    return error


@defer.inlineCallbacks
def _blockmon_process(composition):
    print('running', composition)
    idx = composition.rfind('-')
    composition = composition[:idx]
    composition += '.xml'
    blockmon_comp = open(os.path.join(_capabilitypath, composition), "r")
    fxml = blockmon_comp.read()
    blockmon_comp.close()
    d = _controller_daemon.callRemote('invoke_template', fxml)
    d.addCallback(print_results).addErrback(print_error)
    try:
        ret = yield d
        r = jsonpickle.decode(ret)
    except Exception:
        r = -1

    defer.returnValue(r)


class blockmonControllerService(mplane.scheduler.Service):
    """
    This class handles the capabilities exposed by the proxy:
    executes them, and fills the results

    """

    def __init__(self, cap):
        super(blockmonControllerService, self).__init__(cap)

    def run(self, spec, check_interrupt):
        """
        Execute this Service

        """

        start_time = datetime.utcnow()

        measure_process = _blockmon_process(spec._label)
        reactor.run(installSignalHandlers=0)

        print("returning with", measure_process.result)
        ret = {'time': datetime.utcnow()}

        end_time = datetime.utcnow()
        print("specification {0}: start = {1} end = {2}".format(
            spec._label, start_time, end_time))

        res = mplane.model.Result(specification=spec)
        res.set_when(mplane.model.When(a=start_time, b=end_time))

        labels = ["time"]
        for label in labels:
            if res.has_result_column(label):
                res.set_result_value(label, ret[label])
        # print(mplane.model.unparse_json(res))
        return res


def main():
    """docstring for main"""
    global args
    parser = argparse.ArgumentParser(
        description='run a Blockmon Controller mPlane proxy')
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
        error = "workflow setting in " + args.CONF + \
            " can only be 'client-initiated' or 'component-initiated'"
        raise ValueError(error)


if __name__ == '__main__':
    main()
