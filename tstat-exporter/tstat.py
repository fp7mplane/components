# mPlane Protocol Reference Implementation
# tStat component code
#
# (c) 2013-2014 mPlane Consortium (http://www.ict-mplane.eu)
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

from datetime import datetime
from time import sleep
import mplane.model
import mplane.scheduler
import mplane.utils


"""
Implements tStat capabilities and services

"""

def services(runtimeconf):
    services = []
    if runtimeconf is not None:
        services.append(tStatService(tcp_flows_capability(), mplane.utils.search_path(runtimeconf)))
        services.append(tStatService(e2e_tcp_flows_capability(), mplane.utils.search_path(runtimeconf)))
        services.append(tStatService(tcp_options_capability(), mplane.utils.search_path(runtimeconf)))
        services.append(tStatService(tcp_p2p_stats_capability(), mplane.utils.search_path(runtimeconf)))
        services.append(tStatService(tcp_layer7_capability(), mplane.utils.search_path(runtimeconf)))
    else:
        raise ValueError("missing 'runtimeconf' parameter for tStat capabilities")
    return services

def tcp_flows_capability():
    cap = mplane.model.Capability(label="tstat-log_tcp_complete-core", when = "now ... future")
    cap.add_metadata("System_type", "tStat")
    cap.add_metadata("System_ID", "tStat-Proxy")
    cap.add_metadata("System_version", "0.1")
    cap.add_result_column("initiator.ip4")
    cap.add_result_column("initiator.port")
    cap.add_result_column("packets.forward")
    cap.add_result_column("packets.forward.syn")
    cap.add_result_column("packets.forward.fin")
    cap.add_result_column("packets.forward.rst")
    cap.add_result_column("packets.forward.ack")
    cap.add_result_column("packets.forward.pure_ack")
    cap.add_result_column("packets.forward.with_payload")
    cap.add_result_column("packets.forward.rxmit")
    cap.add_result_column("packets.forward.outseq")
    cap.add_result_column("bytes.forward")
    cap.add_result_column("bytes.forward.unique")
    cap.add_result_column("bytes.forward.rxmit")
    
    cap.add_result_column("responder.ip4")
    cap.add_result_column("responder.port")
    cap.add_result_column("packets.backward")
    cap.add_result_column("packets.backward.syn")
    cap.add_result_column("packets.backward.fin")
    cap.add_result_column("packets.backward.rst")
    cap.add_result_column("packets.backward.ack")
    cap.add_result_column("packets.backward.pure_ack")
    cap.add_result_column("packets.backward.with_payload")
    cap.add_result_column("packets.backward.rxmit")
    cap.add_result_column("packets.backward.outseq")
    cap.add_result_column("bytes.backward")
    cap.add_result_column("bytes.backward.unique")
    cap.add_result_column("bytes.backward.rxmit")
    
    cap.add_result_column("start")
    cap.add_result_column("end")
    cap.add_result_column("duration.ms")
    cap.add_result_column("initiator.TTFP.ms")
    cap.add_result_column("responder.TTFP.ms")
    cap.add_result_column("initiator.TTLP.ms")
    cap.add_result_column("responder.TTLP.ms")
    cap.add_result_column("initiator.TTFA.ms")
    cap.add_result_column("responder.TTFA.ms")
    cap.add_result_column("initiator.ip4.isinternal")
    cap.add_result_column("responder.ip4.isinternal")
    cap.add_result_column("tstat.flow.class.conn")
    cap.add_result_column("tstat.flow.class.p2p")
    cap.add_result_column("tstat.flow.class.http")
    return cap

def e2e_tcp_flows_capability():
    cap = mplane.model.Capability(label="tstat-log_tcp_complete-end_to_end", when = "now ... future")
    cap.add_metadata("System_type", "tStat")
    cap.add_metadata("System_ID", "tStat-Proxy")
    cap.add_metadata("System_version", "0.1")
    cap.add_result_column("rtt.average.ms")
    cap.add_result_column("rtt.min.ms")
    cap.add_result_column("rtt.max.ms")
    cap.add_result_column("rtt.stddev")
    cap.add_result_column("rtt.samples")
    cap.add_result_column("ttl.min")
    cap.add_result_column("ttl.max")
    return cap
    
def tcp_options_capability():
    cap = mplane.model.Capability(label="tstat-log_tcp_complete-tcp_options", when = "now ... future")
    cap.add_metadata("System_type", "tStat")
    cap.add_metadata("System_ID", "tStat-Proxy")
    cap.add_metadata("System_version", "0.1")
    cap.add_result_column("initiator.RFC1323.ws")
    cap.add_result_column("initiator.RFC1323.ts")
    cap.add_result_column("initiator.win_scale")
    cap.add_result_column("initiator.SACK_set")
    cap.add_result_column("initiator.SACK")
    cap.add_result_column("initiator.MSS.bytes")
    cap.add_result_column("initiator.segment.max.bytes")
    cap.add_result_column("initiator.segment.min.bytes")
    cap.add_result_column("initiator.window.max.bytes")
    cap.add_result_column("initiator.window.min.bytes")
    cap.add_result_column("initiator.window.zero")
    cap.add_result_column("initiator.cwin.max.bytes")
    cap.add_result_column("initiator.cwin.min.bytes")
    cap.add_result_column("initiator.cwin.first.bytes")
    cap.add_result_column("initiator.rxmit.RTO")
    cap.add_result_column("initiator.rxmit.RTO.unnecessary")
    cap.add_result_column("initiator.rxmit.FR")
    cap.add_result_column("initiator.rxmit.FR.unnecessary")
    cap.add_result_column("initiator.reordering")
    cap.add_result_column("initiator.net_dup")
    cap.add_result_column("initiator.unknown")
    cap.add_result_column("initiator.flow_control")
    cap.add_result_column("initiator.SYN.equal_seqno")
    
    cap.add_result_column("responder.RFC1323.ws")
    cap.add_result_column("responder.RFC1323.ts")
    cap.add_result_column("responder.win_scale")
    cap.add_result_column("responder.SACK_set")
    cap.add_result_column("responder.SACK")
    cap.add_result_column("responder.MSS.bytes")
    cap.add_result_column("responder.segment.max.bytes")
    cap.add_result_column("responder.segment.min.bytes")
    cap.add_result_column("responder.window.max.bytes")
    cap.add_result_column("responder.window.min.bytes")
    cap.add_result_column("responder.window.zero")
    cap.add_result_column("responder.cwin.max.bytes")
    cap.add_result_column("responder.cwin.min.bytes")
    cap.add_result_column("responder.cwin.first.bytes")
    cap.add_result_column("responder.rxmit.RTO")
    cap.add_result_column("responder.rxmit.RTO.unnecessary")
    cap.add_result_column("responder.rxmit.FR")
    cap.add_result_column("responder.rxmit.FR.unnecessary")
    cap.add_result_column("responder.reordering")
    cap.add_result_column("responder.net_dup")
    cap.add_result_column("responder.unknown")
    cap.add_result_column("responder.flow_control")
    cap.add_result_column("responder.SYN.equal_seqno")
    return cap
    
def tcp_p2p_stats_capability():
    cap = mplane.model.Capability(label="tstat-log_tcp_complete-p2p_stats", when = "now ... future")
    cap.add_metadata("System_type", "tStat")
    cap.add_metadata("System_ID", "tStat-Proxy")
    cap.add_metadata("System_version", "0.1")
    cap.add_result_column("p2p.subtype")
    cap.add_result_column("ed2k.data")
    cap.add_result_column("ed2k.signaling")
    cap.add_result_column("ed2k.i2r")
    cap.add_result_column("ed2k.r2i")
    cap.add_result_column("ed2k.chat")
    return cap    

def tcp_layer7_capability():
    cap = mplane.model.Capability(label="tstat-log_tcp_complete-layer7", when = "now ... future")
    cap.add_metadata("System_type", "tStat")
    cap.add_metadata("System_ID", "tStat-Proxy")
    cap.add_metadata("System_version", "0.1")
    cap.add_result_column("initiator.psh_separated")
    cap.add_result_column("responder.psh_separated")
    cap.add_result_column("ssl.hello.client")
    cap.add_result_column("ssl.hello.server")
    return cap
    
class tStatService(mplane.scheduler.Service):
    """
    This class handles the capabilities exposed by the proxy:
    executes them, and fills the results
    
    """
    
    def __init__(self, cap, fileconf):
        super(tStatService, self).__init__(cap)
        self._fileconf = fileconf

    def run(self, spec, check_interrupt):
        """
        Execute this Service
        
        """
        start_time = datetime.utcnow()

        # start measurement changing the tstat conf file
        self.change_conf(spec._label, True)

        # wait for specification execution
        wait_time = spec._when.timer_delays()
        wait_seconds = wait_time[1]
        if wait_seconds != None:
            for i in range(0, round(wait_seconds)):
                sleep(1)
                if check_interrupt():
                    break
        end_time = datetime.utcnow()

        # terminate measurement changing the tstat conf file
        self.change_conf(spec._label, False)
        
        # fill result message from tStat log
        print("specification " + spec._label + ": start = " + str(start_time) + ", end = " + str(end_time))
        res = self.fill_res(spec, start_time, end_time)
        return res

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
                res.set_result_value(column_name, "1.2.3.4")
            elif prim == "url":
                res.set_result_value(column_name, "www.google.com")
        
        return res
        
    def change_conf(self, cap_label, enable):
        """
        Changes the needed flags in the tStat runtime.conf file
        
        """
        newlines = []
        f = open(self._fileconf, 'r')
        for line in f:
            
            # read parameter names and values (discard comments or empty lines)
            if (line[0] != '[' and line[0] != '#' and
                line[0] != '\n' and line[0] != ' '):    
                param = line.split('#')[0]
                param_name = param.split(' = ')[0]
                
                # change flags according to the measurement requested
                if enable == True:
                    
                    # in order to activate optional sets, the basic set (log_tcp_complete) must be active too
                    if (cap_label == "tstat-log_tcp_complete-core" and param_name == 'log_tcp_complete'):
                        newlines.append(line.replace('0', '1'))
                        
                    elif (cap_label == "tstat-log_tcp_complete-end_to_end" and (
                        param_name == 'tcplog_end_to_end' 
                        or param_name == 'log_tcp_complete')):
                        newlines.append(line.replace('0', '1'))

                    elif (cap_label == "tstat-log_tcp_complete-tcp_options" and (
                        param_name == 'tcplog_options' or
                        param_name == 'log_tcp_complete')):
                        newlines.append(line.replace('0', '1'))

                    elif (cap_label == "tstat-log_tcp_complete-p2p_stats" and (
                        param_name == 'tcplog_p2p' or
                        param_name == 'log_tcp_complete')):
                        newlines.append(line.replace('0', '1'))

                    elif (cap_label == "tstat-log_tcp_complete-layer7" and (
                        param_name == 'tcplog_layer7' or
                        param_name == 'log_tcp_complete')):
                        newlines.append(line.replace('0', '1'))
                    else:
                        newlines.append(line)
                else:
                    if (cap_label == "tstat-log_tcp_complete-end_to_end" and param_name == 'tcplog_end_to_end'):
                        newlines.append(line.replace('1', '0'))

                    elif (cap_label == "tstat-log_tcp_complete-tcp_options" and param_name == 'tcplog_options'):
                        newlines.append(line.replace('1', '0'))

                    elif (cap_label == "tstat-log_tcp_complete-p2p_stats" and param_name == 'tcplog_p2p'):
                        newlines.append(line.replace('1', '0'))

                    elif (cap_label == "tstat-log_tcp_complete-layer7" and param_name == 'tcplog_layer7'):
                        newlines.append(line.replace('1', '0'))

                    else:
                        newlines.append(line) 
            else:
                newlines.append(line)
        f.close()
        
        f = open(self._fileconf, 'w')
        f.writelines(newlines)
        f.close