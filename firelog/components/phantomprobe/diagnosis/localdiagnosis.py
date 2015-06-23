#!/usr/bin/python
#
# mPlane QoE Probe
#
# (c) 2013-2014 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Marco Milanesio <milanesio.marco@gmail.com>
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
import logging
import json
from .cusum import Cusum

logger = logging.getLogger('LocalDiagnosisManager')


class LocalDiagnosisManager():
    def __init__(self, db, url):
        self.url = url
        self.db = db
        self.table_values = self.db.tables['diag_values']
        self.table_result = self.db.tables['diag_result']

    def get_local_data(self):
        q = '''select flt, http, tcp, dim, t1, d1, d2, dh, count
        from {0} where url like '%{1}%' '''.format(self.table_values, self.url)
        try:
            res = self.db.execute(q)
            data = res[0]
            return {'full_load_time_th': data[0], 'http_th': data[1], 'tcp_th': data[2], 'dim_th': data[3],
                    't1': data[4], 'd1': data[5], 'd2': data[6], 'dh': data[7], 'count': data[8]}
        except:
            return None

    def prepare_for_diagnosis(self, passive, active):
        try:
            assert len(passive) == 1
        except AssertionError as e:
            logger.error("len(passive) = {0} ".format(len(passive)))
            logger.error(e)
            exit(1)
        sid = list(passive.keys())[0]
        locals = self.get_local_data()
        if not locals:
            logger.warning("First time hitting {0}: using default values.".format(self.url))
            # TODO: find a way to have threshold setting
            cusumT1 = Cusum('cusumT1', 0, 0)
            cusumT2T1 = Cusum('cusumT2T1', 0, 0)
            cusumT3T2 = Cusum('cusumT3T2', 0, 0)
            cusumTHTTPTTCP = Cusum('cusumTHTTPTTCP', 0, 0)
            time_th = passive[sid]['full_load_time'] + 1000
            dim_th = passive[sid]['page_dim'] + 1500 * 5
            http_th = sum([x['sum_http'] for x in passive[sid]['browser']]) + 50
            tcp_th = sum([x['sum_syn'] for x in passive[sid]['browser']]) + 50
            self.insert_first_locals(time_th, dim_th, http_th, tcp_th)
        else:
            num_hits = locals['count']
            cusumT1 = Cusum('cusumT1', locals['t1'], num_hits)
            cusumT2T1 = Cusum('cusumT2T1', locals['d1'], num_hits)
            cusumT3T2 = Cusum('cusumT3T2', locals['d2'], num_hits)
            cusumTHTTPTTCP = Cusum('cusumTHTTPTTCP', locals['dh'], num_hits)
            time_th = locals['full_load_time_th']
            dim_th = locals['dim_th']
            http_th = locals['http_th']
            tcp_th = locals['tcp_th']

        mem_th = cpu_th = 50

        tools = {'cusums':
                     {'cusumT1': cusumT1,
                      'cusumT2T1': cusumT2T1,
                      'cusumT3T2': cusumT3T2,
                      'cusumTHTTPTTCP': cusumTHTTPTTCP},
                 'time_th': time_th,
                 'dim_th': dim_th,
                 'http_th': http_th,
                 'tcp_th': tcp_th,
                 'mem_th': mem_th,
                 'cpu_th': cpu_th}

        return sid, passive[sid], active[sid], tools

    def run_diagnosis(self, passive, active):
        diagnosis = {'result': None, 'details': None}
        sid, cs_p, cs_a, tools = self.prepare_for_diagnosis(passive, active)

        if cs_p['full_load_time'] < tools['time_th']:
            diagnosis['result'] = 'No problem found'
        else:
            if cs_p['mem_percent'] > tools['mem_th'] or cs_p['cpu_percent'] > tools['cpu_th']:
                diagnosis['result'] = 'Client overloaded'
                diagnosis['details'] = "mem = {0}%, cpu = {1}%".format(cs_p['mem_percent'], cs_p['cpu_percent'])
                return diagnosis

            t_http = sum([x['sum_http'] for x in cs_p['browser']])
            t_tcp = sum([x['sum_syn'] for x in cs_p['browser']])
            if t_http < tools['http_th']:
                if cs_p['page_dim'] > tools['dim_th']:
                    diagnosis['result'] = 'Page too big'
                    diagnosis['details'] = "page_dim = {0} bytes".format(cs_p['page_dim'])
                elif t_tcp > tools['tcp_th']:
                    diagnosis['result'] = 'Web server too far'
                    diagnosis['details'] = "sum_syn = {0} ms".format(t_tcp)
                else:
                    diagnosis['result'] = 'No problem found'
                    diagnosis['details'] = "Unable to get more details"
            else:
                diff = t_http - t_tcp
                diagnosis['result'], diagnosis['details'] = self._check_network(cs_a, tools, diff)

        q = "update {0} set count = count + 1 where url like '%{1}%'"\
            .format(self.table_values, self.url)
        self.db.execute(q)
        logger.info(diagnosis)
        self.store_diagnosis_result(sid, diagnosis)
        return diagnosis

    def _check_network(self, active, tools, diff):
        new_thresholds = {'t1': 0, 'd1': 0, 'd2': 0, 'dh': 0}
        result = details = None
        for measure in active:
            if 'trace' in measure.keys():
                el = measure['trace']
                list_ = json.loads(el)
                first_hop = [x for x in list_ if x['hop_nr'] == 1][0]
                second_hop = [x for x in list_ if x['hop_nr'] == 2][0]
                third_hop = [x for x in list_ if x['hop_nr'] == 3][0]

        gw_addr = first_hop['ip_addr']
        gw_rtt = first_hop['rtt']['avg']
        c_t1 = tools['cusums']['cusumT1']
        second_addr = second_hop['ip_addr']
        second_rtt = second_hop['rtt']['avg']
        third_addr = third_hop['ip_addr']
        try:
            third_rtt = third_hop['rtt']['avg']
        except TypeError:
            third_rtt = second_rtt * 2  # FIXME: case when third hop does not answer ping

        if c_t1.compute([gw_rtt]):
            result = 'Local congestion (LAN/GW)'
            details = "cusum on RTT to 1st hop {0}".format(gw_addr)
            new_thresholds['t1'] = c_t1.get_th()
        else:
            d1 = [x-y for x, y in zip([second_rtt], [gw_rtt])]
            d2 = [x-y for x, y in zip([third_rtt], [second_rtt])]
            c_d1 = tools['cusums']['cusumT2T1']
            c_d2 = tools['cusums']['cusumT3T2']
            if c_d1.compute(d1):
                new_thresholds['d1'] = c_d1.get_th()
                if c_d2.compute(d2):
                    new_thresholds['d2'] = c_d2.get_th()
                    result = 'Network congestion'
                    details = "cusum on Delta1 [{0},{1}] and Delta2 [{1},{2}]".format(gw_addr, second_addr, third_addr)
                else:
                    result = 'Gateway congestion'
                    details = "cusum on Delta1 [{0},{1}]".format(gw_addr, second_addr)

        if not result:
            c_t = tools['cusums']['cusumTHTTPTTCP']
            if c_t.compute([diff]):
                new_thresholds['dh'] = c_t.get_th()
                result = 'Remote Web Server'
                details = "cusum on t_http - t_tcp"
            else:
                result = 'Network generic (far)'
                details = "unable to get more details"

        alternative = {'t1': gw_rtt, 'd1': second_rtt, 'd2': third_rtt, 'dh': diff}
        for k, v in new_thresholds.items():
            if v == 0:
                v = alternative[k]
        self.update_cusum_threshold(new_thresholds, alternative)
        return result, details

    def update_cusum_threshold(self, new, alt):
        q = "update {0} set ".format(self.table_values)
        for k, v in new.items():
            if v > 0:
                q += "{0} = {1}, ".format(k, v)
            else:
                q += "{0} = {1}, ".format(k, alt[k])
        q = q[:-2] + " where url = '{0}'".format(self.url)
        self.db.execute(q)
        logger.debug("Updated thresholds in diagnosis table")

    def insert_first_locals(self, flt, http, tcp, dim):
        q = "insert into {0}(url, flt, http, tcp, dim, t1, d1, d2, dh, count) values "\
            .format(self.table_values)
        q += "('{0}', {1}, {2}, {3}, {4}, 0, 0, 0, 0, 0)".format(self.url, flt, http, tcp, dim)
        self.db.execute(q)

    def store_diagnosis_result(self, sid, diagnosis):
        q = "select session_start, session_url from {0} where sid = {1}".\
            format(self.db.tables['aggr_sum'], sid)
        res = self.db.execute(q)
        when = res[0][0]
        url = res[0][1]
        q = "insert into {0} (sid, url, when_browsed, diagnosis) values".format(self.table_result)
        q += " ({0}, '{1}', '{2}', '{3}')".format(sid, url, when, json.dumps(diagnosis))
        self.db.execute(q)
        logger.debug("Diagnosis result saved.")
