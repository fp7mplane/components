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
import json
import logging
import collections
import csv
import os

logger = logging.getLogger('JSONClient')


class JSONClient():
    def __init__(self, config, dbcli):
        self.srv_ip = config.get_jsonserver_configuration()['ip']
        self.srv_port = int(config.get_jsonserver_configuration()['port'])
        self.flumedir = config.get_flume_configuration()['outdir']
        #self.json_file = config.get_flume_configuration()['outfile']  # TODO remove (os.path.join(flumedir, fname)
        #self.csv_file = config.get_flume_configuration()['outfilecsv']  # TODO remove
        self.db = dbcli
        self.probeid = self._get_client_id_from_db()

    def _get_client_id_from_db(self):
        q = "select distinct probe_id from {0}".format(self.db.tables['probe'])
        r = self.db.execute(q)
        assert len(r) == 1
        return int(r[0][0])

    def prepare_data(self):
        probedata = {}
        query = '''select username, probe_id, first_start, location from {0}'''.format(self.db.tables['probe'])
        res = self.db.execute(query)
        assert len(res) == 1
        user, probe_id, first_start, location_str = res[0]

        location_dic = json.loads(location_str)
        location_dic["loc"] = location_dic["loc"].replace(",", ";")

        assert self.probeid == probe_id
        probedata.update({'username': user, 'probe_id': probe_id,
                          'first_start': first_start, 'location': location_dic})

        query = '''select sid, session_url, session_start, server_ip,
        full_load_time, page_dim, cpu_percent, mem_percent from {0} where not is_sent'''.\
            format(self.db.tables['aggr_sum'])
        res = self.db.execute(query)
        if len(res) == 0:
            logger.warning("Nothing to send. All flags are valid.")
            return

        sessions_list = []
        for row in res:
            r = collections.OrderedDict()
            r['probeid'] = probedata
            r['sid'] = row[0]
            r['session_url'] = row[1]
            r['session_start'] = str(row[2])  # convert to string to be json-serializable
            r['server_ip'] = row[3]
            r['full_load_time'] = row[4]
            r['page_dim'] = row[5]
            r['cpu_percent'] = row[6]
            r['mem_percent'] = row[7]
            r['services'] = []
            r['active_measurements'] = {}
            r['local_diagnosis'] = {}

            query = '''select base_url, ip, netw_bytes, nr_obj, sum_syn, sum_http, sum_rcv_time
            from {0} where sid = {1}'''.format(self.db.tables['aggr_det'], row[0])
            det = self.db.execute(query)

            for det_row in det:
                d = collections.OrderedDict()
                d['base_url'] = det_row[0]
                d['ip'] = det_row[1]
                d['netw_bytes'] = det_row[2]
                d['nr_obj'] = det_row[3]
                d['sum_syn'] = det_row[4]
                d['sum_http'] = det_row[5]
                d['sum_rcv_time'] = det_row[6]
                r['services'].append(d)

            query = '''select remote_ip, ping, trace
            from {0} where sid = {1}'''.format(self.db.tables['active'], row[0])
            active = self.db.execute(query)

            for active_row in active:
                a = collections.OrderedDict()
                a[active_row[0]] = {'ping': active_row[1], 'trace': active_row[2]}
                r['active_measurements'].update(a)      # dictionary!

            query = '''select diagnosis from {0} where sid = {1} and url = '{2}' '''\
                .format(self.db.tables['diag_result'], r['sid'], r['session_url'])

            res = self.db.execute(query)
            r['local_diagnosis'] = json.loads(res[0][0])

            sessions_list.append(r)

        #j = json.dumps(sessions_list)
        return sessions_list

    def save_json_file(self, measurements):
        # measurements is a list of dictionaries
        # one for each session: ['passive', 'active', 'ts', 'clientid', 'sid']
        logger.info('Saving json file...')
        with open(self.json_file, 'w') as out:
            out.write(json.dumps([m for m in measurements]))

        return self.json_file

    def save_csv_files(self, measurements):
        """
        :param measurements: a list of OrderedDict, one for each session
        :return:
        """
        from utils import utils
        csvfiles = []
        csvnum = 0
        for session in measurements:
            expanded_session = utils.prepare_for_csv(session)
            max_len = 0
            mapping = {}
            result = []
            for k, v in sorted(list(expanded_session.items())):
                if v is []:
                    continue
                if (isinstance(v, list) or isinstance(v, dict) or isinstance(v, collections.OrderedDict)) and \
                                len(v) > max_len:
                    max_len = len(v)
                if isinstance(v, list):
                    try:
                        tmp = collections.OrderedDict(v[0])
                        mapping[k] = sorted([k1 for k1 in tmp])
                    except (TypeError, IndexError):
                        continue
                elif isinstance(v, dict) or isinstance(v, collections.OrderedDict):
                    mapping[k] = sorted([k1 for k1 in v])
                else:
                    continue

            for i in range(max_len):
                tmp = collections.OrderedDict()
                for k, v in sorted(list(expanded_session.items())):
                    if not isinstance(v, list):
                        tmp.update({k: v})
                    else:
                        if k in mapping and i < len(v):
                            if isinstance(v[i], list):
                                for tup in v[i]:
                                    tmp.update({tup[0]: tup[1]})
                        elif k in mapping and i >= len(v):
                            for mk in mapping[k]:
                                tmp.update({mk: ''})
                        else:
                            try:
                                tmp.update({k: v[i]})
                            except IndexError:
                                tmp.update({k: ''})
                result.append(tmp)

            fname = os.path.join(self.flumedir, "{0}.csv".format(csvnum))
            with open(fname, "w", newline='') as csvfile:
                writer = csv.DictWriter(csvfile, result[0].keys())
                #writer.writeheader()
                #writer.writerows(result)
                for el in result:
                    try:
                        writer.writerow(el)
                    except ValueError:
                        logger.error("not written: {0}".format(el))

            if not os.path.exists(fname):
                logger.error("No csv saved")
            else:
                logger.error("Saved: {0}".format(fname))
                csvfiles.append(fname)
            csvnum += 1

        return csvfiles

    def send_csv(self):
        import socket
        HOST = self.srv_ip
        PORT = self.srv_port
        for root, dirs, files in os.walk(self.flumedir):
            for file in files:
                with open(os.path.join(root, file), 'r') as f:
                    data = ''.join(f.readlines())

                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                    try:
                        sock.connect((HOST, PORT))
                        tosend = json.dumps(data)
                        sock.sendall(bytes(tosend + "\n", "utf-8"))
                        received = str(sock.recv(1024), "utf-8")
                    finally:
                        sock.close()

                    logger.debug("Sent:     {}".format(len(tosend)))
                    logger.debug("Received: {}".format(received))

    # def send_json_to_srv(self, measurements):
    #     logger.info('Contacting server...')
    #     try:
    #         s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #         s.connect((self.srv_ip, self.srv_port))
    #     except socket.error as e:
    #         logger.error('Socket error({0}): {1}'.format(e.errno, e.strerror))
    #         return False
    #
    #     data = json.dumps([m for m in measurements])
    #     logger.info("Sending %d bytes" % len(data))
    #     s.sendall(data + '\n')
    #     result = json.loads(s.recv(1024))
    #     s.close()
    #     logger.info("Received %s" % str(result))
    #
    #     for sid in result['sids']:
    #         q = '''update %s set is_sent = 1 where sid = %d''' % (self.db.tables['aggr_sum'], int(sid))
    #         self.db.execute(q)
    #     logger.debug("Set is_sent flag on summary table for sids {0}.".format(result['sids']))
    #
    #     return True
