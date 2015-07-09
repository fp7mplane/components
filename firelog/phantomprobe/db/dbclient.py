import random
import datetime
import time
import logging
import sqlite3
import json

from .dbconnector import DBConnector
import db.createqueries as cq
from probe.parser import Parser
import sys

logger = logging.getLogger('DBClient')

class DBClient():

    def __init__(self, configuration, loc_info=None, create=False):
        self.dbconfig = configuration.get_database_configuration()
        try:
            self.conn = DBConnector(self.dbconfig['dbfile'])
        except sqlite3.OperationalError:
            print("Unable to open the database file. Quitting")
            print(self.dbconfig['dbfile'])
            exit(1)
        self.loc_info = loc_info
        self.tables = {'raw': self.dbconfig['table_raw'],
                       'active': self.dbconfig['table_active'],
                       'probe': self.dbconfig['table_probe'],
                       'aggr_sum': self.dbconfig['table_aggr_sum'],
                       'aggr_det': self.dbconfig['table_aggr_det'],
                       'diag_values': self.dbconfig['table_diag_values'],
                       'diag_result': self.dbconfig['table_diag_result']}
        if create:
            self.create_tables()

    def create_tables(self):
        q = [cq.create_id_table.format(self.tables['probe']),
             cq.create_raw_table.format(self.tables['raw']),
             cq.create_active_table.format(self.tables['active']),
             cq.create_aggregate_summary.format(self.tables['aggr_sum']),
             cq.create_aggregate_details.format(self.tables['aggr_det']),
             cq.create_local_diagnosis.format(self.tables['diag_values']),
             cq.create_local_diagnosis_result.format(self.tables['diag_result'])]
        for query in q:
            try:
                self.conn.execute_query(query)
            except sqlite3.OperationalError:
                logger.error(query)
                sys.exit(1)

    def get_probe_id(self):
        query = "SELECT probe_id FROM %s " % self.tables['probe']
        res = self.conn.execute_query(query)
        if res:
            return int(res[0][0])
        else:
            return self._create_probe_id()

    def _create_probe_id(self):
        ran = 2**31 - 1  # int4
        probe_id = int(random.random()*ran)
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        user = self.dbconfig['username']
        for k in ['city', 'region']:
            self.loc_info.update({k: self.loc_info[k].replace("'", "''")})
        q = "INSERT INTO {0} VALUES ('{1}', {2}, '{3}', '{4}')".format(self.tables['probe'], user, probe_id, st,
                                                                       json.dumps(self.loc_info))
        self.conn.execute_query(q)
        return probe_id

    def load_to_db(self, stats):
        probe_id = self.get_probe_id()
        logger.debug("Got client %s" % probe_id)
        p = Parser(self.dbconfig['tstatfile'], self.dbconfig['harfile'], probe_id)
        to_insert = p.parse()
        self.write_plugin_into_db(to_insert, stats)

    def write_plugin_into_db(self, session_dic, stats):
        table_name = self.tables['raw']
        insert_query = 'INSERT OR IGNORE INTO ' + table_name + ' (%s) values'
        httpid_inserted = []  # FIXME keep track of duplicates

        session = {'session_url': session_dic['session_url'],
                   'session_start': session_dic['session_start'],
                   'probe_id': session_dic['probe_id'],
                   'full_load_time': session_dic['full_load_time'],
                   'mem': int(stats[session_dic['session_url']]['mem']),
                   'cpu': int(stats[session_dic['session_url']]['cpu'])
                   }
        objects = {}

        metacolumns = ['uri', 'first_bytes_rcv', 'rcv_time', 'local_port', 'local_ip', 'remote_port', 'remote_ip',
                       'syn_time', 'app_rtt', 'request_ts', 'end_time', 'content_type', 'body_bytes']

        for httpid, obj in session_dic['entries'].items():
            if httpid in httpid_inserted:
                continue
            objects[httpid] = dict.fromkeys(metacolumns)
            for key in metacolumns:
                try:
                    if key == 'uri' and len(obj[key]) > 255:
                        logger.warning("Truncating uri: {0}".format(obj[key]))
                        objects[httpid][key] = obj[key][:254]
                    objects[httpid][key] = obj[key]
                except KeyError:
                    logger.error("KeyError: {}".format(key))
                    logger.error(obj)
                    objects[httpid][key] = None

        logger.debug("Found {0} objects for session to {1}".format(len(objects), session['session_url']))
        columns = '''httpid, session_url, session_start, probe_id, full_load_time, uri, first_bytes_rcv, rcv_time,
        local_port, local_ip, remote_port, remote_ip, syn_time, app_rtt, request_ts, end_time, content_type,
        body_bytes, cpu_percent, mem_percent'''

        for k, v in objects.items():
            q = insert_query % columns
            q += "(" + ",".join(["?"]*len(columns.split(","))) + ")"

            tup = (k, session['session_url'], session['session_start'], session['probe_id'], session['full_load_time'],
                   v['uri'], v['first_bytes_rcv'], v['rcv_time'], v['local_port'], v['local_ip'], v['remote_port'],
                   v['remote_ip'], v['syn_time'], v['app_rtt'], v['request_ts'], v['end_time'], v['content_type'],
                   v['body_bytes'], session['cpu'], session['mem'])

            '''
            q += "(%s, '%s', '%s', %d, %d, '%s', '%s', %d," % (k, session['session_url'], session['session_start'],
                                                               session['probe_id'], session['full_load_time'], v['uri'],
                                                               v['first_bytes_rcv'], v['rcv_time'])
            q += "'%s', '%s', '%s', '%s'," % (v['local_port'], v['local_ip'], v['remote_port'], v['remote_ip'])


            q += "%s, %s, '%s', '%s', '%s', %d, %d, %d)" % (v['syn_time'], v['app_rtt'], v['request_ts'], v['end_time'],
                                                            v['content_type'], v['body_bytes'], session['cpu'],
                                                            session['mem'])
            '''
            try:
                row_id = self.conn.execute_query(q, tup)
                httpid_inserted.append(k)
            except sqlite3.Error as e:
                logger.error("Failed to insert: {}".format(v))
                logger.error("sqlite3 ({0})".format(e))
                continue

        self._generate_sid_on_table()

    def old_write_plugin_into_db(self, session_dic, stats):
        table_name = self.tables['raw']
        insert_query = 'INSERT OR IGNORE INTO ' + table_name + ' (%s) values (%s)'
        update_query = 'UPDATE ' + table_name + ' SET mem_percent = %d, cpu_percent = %d where rowid = %d'
        httpid_inserted = []  # FIXME keep track of duplicates

        session_url = session_dic['session_url']
        session_start = session_dic['session_start']
        probe_id = session_dic['probe_id']
        full_load_time = session_dic['full_load_time']

        entries = session_dic['entries']
        local_port = None
        local_ip = None
        remote_port = None
        remote_ip = None
        syn_time = None
        app_rtt = None
        request_ts = None
        end_time = None
        content_type = None
        body_bytes = None
        vars = [local_port, local_ip, remote_port, remote_ip, syn_time, app_rtt, request_ts, end_time, content_type, body_bytes]
        #var_names = [k for k, v in locals().items() if v in vars]
        for httpid, obj in entries.items():
            if httpid in httpid_inserted:
                continue
            uri = obj['uri']
            first_bytes_rcv = obj['first_bytes_rcv']
            rcv_time = obj['rcv_time']
            for var in vars:
                v_name = [k for k, v in locals().items() if v is var][0]
                try:
                    var = obj[v_name]
                except KeyError:
                    logger.error("KeyError: {} not found".format(v_name))
                    logger.error("KeyError: {}".format(obj))
                    #sys.exit(1)
            #local_port = obj['local_port']
            #local_ip = obj['local_ip']
            #remote_port = obj['remote_port']
            #remote_ip = obj['remote_ip']
            #syn_time = obj['syn_time']
            #app_rtt = obj['app_rtt']
            #request_ts = obj['request_ts']
            #end_time = obj['end_time']
            #content_type = obj['content_type']
            #body_bytes = obj['body_bytes']

            mem = int(stats[session_url]['mem'])
            cpu = int(stats[session_url]['cpu'])

            if len(uri) > 255:
                logger.warning("Truncating uri: {0}".format(uri))
                uri = uri[:254]

            cols = '''httpid, session_url, session_start, probe_id, full_load_time, uri, first_bytes_rcv, rcv_time,
            local_port, local_ip, remote_port, remote_ip, syn_time, app_rtt, request_ts, end_time, content_type,
            body_bytes, cpu_percent, mem_percent'''

            values = '''{0}, '{1}', '{2}', {3}, {4}, '{5}',
            '{6}', {7}, {8}, '{9}', {10}, '{11}',
            {12}, {13}, '{14}', '{15}', '{16}', {17},
            {18}, {19}
            '''.format(httpid, session_url, session_start, probe_id, full_load_time, uri,
                       first_bytes_rcv, rcv_time, local_port, local_ip, remote_port, remote_ip,
                       syn_time, app_rtt, request_ts, end_time, content_type, body_bytes,
                       cpu, mem)

            to_execute = insert_query % (cols, values)
            try:
                row_id = self.conn.execute_query(to_execute)
            except sqlite3.Error as e:
                logger.error("Failed: ", to_execute)
                logger.error("sqlite3 ({0})".format(e))
                continue

            httpid_inserted.append(httpid)

        self._generate_sid_on_table()

    def _generate_sid_on_table(self):
        q = "select max(sid) from {0}".format(self.tables['raw'])
        res = self.conn.execute_query(q)
        max_sid = 0
        if res[0] != (None,):
            max_sid = int(res[0][0])

        query = '''select distinct probe_id, session_start from {0} where sid is NULL
        order by session_start'''.format(self.tables['raw'])
        res = self.conn.execute_query(query)
        logger.debug('Found {0} sessions to insert'.format(len(res)))
        for tup in res:
            probe_id = tup[0]
            session_start = tup[1]
            max_sid += 1
            query = '''update {0} set sid = {1} where
            session_start = '{2}' and probe_id = {3}'''.format(self.tables['raw'], max_sid, session_start, probe_id)
            try:
                self.conn.execute_query(query)
            except sqlite3.Error:
                logger.error(query)

    def get_inserted_sid_addresses(self):
        result = {}
        q = '''select distinct a.sid, a.ip, b.server_ip, b.session_url
        from {0} a, {1} b
        where a.sid = b.sid and not b.is_sent
        and b.sid not in (select distinct sid from {2});'''\
            .format(self.tables['aggr_det'], self.tables['aggr_sum'], self.tables['active'])

        res = self.conn.execute_query(q)
        for tup in res:
            sid = str(tup[0])
            ip = tup[1]
            server_ip = tup[2]
            url = tup[3]
            if sid not in result.keys():
                result[sid] = {'url': url}

            if url != result[sid]['url']:
                logger.error("Misleading url in fetched data.")
                logger.error("{0} -> {1}".format(res, tup))

            if ip == server_ip:
                result[sid].update({'complete': server_ip})
            else:
                if 'addresses' not in result[sid].keys():
                    result[sid]['addresses'] = []
                result[sid]['addresses'].append(ip)

        return result

    def insert_active_measurement(self, sid, ip_dest, to_insert_list):
        #data['ping'] = json obj
        #data['trace'] = json obj
        for dic in to_insert_list:
            url = dic['url']
            ip = dic['ip']
            ping = dic['ping']
            if 'trace' in dic.keys():
                trace = dic['trace']
                query = '''INSERT OR IGNORE into %s (ip_dest, sid, session_url, remote_ip, ping, trace) values
                ('%s', %d, '%s', '%s', '%s','%s') ''' % (self.tables['active'], ip_dest, int(sid), url,
                                                         ip, ping, trace)
            else:
                query = '''INSERT OR IGNORE into %s (ip_dest, sid, session_url, remote_ip, ping) values
                ('%s', %d, '%s', '%s', '%s') ''' % (self.tables['active'], ip_dest, int(sid), url, ip, ping)

            self.conn.execute_query(query)
        logger.info('inserted active measurements for sid %s: ' % sid)

    def pre_process_raw_table(self):
        # TODO: page_dim as sum of netw_bytes in summary
        logger.info('Pre-processing data from raw table...')
        # eliminate redirection (e.g., http://www.google.fr/?gfe_rd=cr&ei=W8c_VLu9OcjQ8geqsIGQDA)
        q = '''select distinct sid, full_load_time from {0}
            where sid not in (select distinct sid from {1})
            group by sid, full_load_time
            having count(sid) > 1'''.format(self.tables['raw'], self.tables['aggr_sum'])
        res = self.conn.execute_query(q)
        if len(res) == 0:
            logger.warning('pre_process: no sids found')
            return None

        d = dict(res)
        logger.debug("{0} session(s) to preprocess: sids {1} ".format(len(d), d.keys()))
        dic = {}
        for sid in d.keys():
            q = '''select distinct remote_ip, session_url, session_start, cpu_percent, mem_percent from %s
            where sid = %d and session_url = uri group by remote_ip, session_url, session_start,
            cpu_percent, mem_percent''' % (self.tables['raw'], sid)

            res = self.conn.execute_query(q)

            if len(res) == 0:  # all uri come from different servers (pisa testbed): something bad happened
                logger.warning("Unable to find a match session_url = uri in session {0}".format(sid))
                q = '''select distinct remote_ip, session_url, session_start, cpu_percent, mem_percent from %s
                where sid = %d group by remote_ip, session_url, session_start, cpu_percent, mem_percent''' \
                    % (self.tables['raw'], sid)
                res = self.conn.execute_query(q)
                logger.warning("Found {0} urls relaxing the constraint.".format(len(res)))
                logger.warning("Session {0} will not be inserted in {1}".format(sid, self.tables['aggr_sum']))
                continue

            if len(res) > 1:
                logger.warning("Multiple tuples for sid {0}: {1}".format(sid, res))

            try:
                dic[str(sid)] = {'server_ip': res[0][0], 'full_load_time': d[sid],
                                 'session_start': res[0][2], 'session_url': res[0][1],
                                 'cpu_percent': res[0][3], 'mem_percent': res[0][4],
                                 'browser': []}
            except IndexError:
                logger.error(q)
                logger.error(res)
                continue

            q = '''select distinct remote_ip, count(*) as cnt, sum(app_rtt) as s_app,
            sum(rcv_time) as s_rcv, sum(body_bytes) as s_body, sum(syn_time) as s_syn from %s where sid = %d
            group by remote_ip;''' % (self.tables['raw'], sid)
            res = self.conn.execute_query(q)
            logger.debug("Found {} rows for passive measurements".format(len(res)))
            page_dim = 0
            count_error = 0
            for tup in res:
                #ip, nr_obj, sum_http, sum_rcv_time, netw_bytes, sum_syn
                test_for_none = list(tup)
                ip = test_for_none[0]
                if not ip:
                    logger.error("Unable to get passive data for sid: {}".format(sid))
                    logger.error("skipping...")
                    count_error += 1
                    logger.error("count_error = {0}, len(res) = {1}".format(count_error, len(res)))
                    logger.error("count_error == len(res): ".format(count_error == len(res)))
                    if count_error == len(res):
                        logger.error("Unable to get ANY passive data for sid: {}".format(sid))
                        logger.error("Aborting.")
                        return None
                    continue

                ok = [ip]  # ip
                for el in test_for_none[1:]:
                    try:
                        ok.append(int(el))
                    except TypeError:
                        logger.error("TypeError on test_for_none: {}".format(test_for_none))
                        ok.append(None)
                        pass

                dic[str(sid)]['browser'].append({'ip': ok[0], 'nr_obj': ok[1], 'sum_http': ok[2],
                                                 'sum_rcv_time': ok[3], 'netw_bytes': ok[4],
                                                 'sum_syn': ok[5]})
                page_dim += ok[4]
                #dic[str(sid)]['browser'].append({'ip': tup[0], 'nr_obj': int(tup[1]), 'sum_http': int(tup[2]),
                #                                 'sum_rcv_time': int(tup[3]), 'netw_bytes': int(tup[4]),
                #                                 'sum_syn': int(tup[5])})
                #page_dim += int(tup[4])

            dic[str(sid)].update({'page_dim': page_dim})

            for el in dic[str(sid)]['browser']:
                ip = el['ip']
                q = '''select uri from %s where remote_ip = \'%s\'''' % (self.tables['raw'], ip)
                res = self.conn.execute_query(q)
                el.update({'base_url': '/'.join(res[0][0].split('/')[:3])})
                #if len(res) > 1:
                #    el.update({'base_url': os.path.commonprefix([x[0] for x in res])})
                #else:
                #    el.update({'base_url': '/'.join(res[0][0].split('/')[:3])})

        if self.insert_to_aggregate(dic):
            return dic
        else:
            logger.error("Something bad happened.")
            return None

    def insert_to_aggregate(self, pre_processed):
        logger.debug("received at insert_to_aggregate: {0} sessions".format(len(pre_processed)))
        table_name_summary = self.tables['aggr_sum']
        table_name_details = self.tables['aggr_det']
        stub = 'INSERT INTO ' + table_name_summary + ' (%s) values (%s)'
        stub2 = 'INSERT INTO ' + table_name_details + ' (%s) values (%s)'
        for sid, obj in pre_processed.items():
            url = obj['session_url']
            start = obj['session_start']
            flt = obj['full_load_time']
            page_dim = obj['page_dim']
            ip = obj['server_ip']
            cpu_percent = obj['cpu_percent']
            mem_percent = obj['mem_percent']
            q = stub % ('''sid, session_url, session_start, full_load_time,
            page_dim, server_ip, cpu_percent, mem_percent, is_sent''',
                        "{0}, '{1}', '{2}', {3}, {4}, '{5}', {6}, {7}, {8}".format(int(sid), url, start, flt,
                                                                                   page_dim, ip,
                                                                                   cpu_percent, mem_percent, 0))
            try:
                self.conn.execute_query(q)
            except sqlite3.Error as e:
                logger.error("Error in insert to aggregate {0}".format(e))
                logger.error(q)
                continue

            #if reference:
            for dic in (obj['browser']):
                s = 'sid, base_url, ip, netw_bytes, nr_obj, sum_syn, sum_http, sum_rcv_time'
                v = '%d, \'%s\', \'%s\', %d, %d, %d, %d, %d' % (int(sid), dic['base_url'], dic['ip'],
                                                                dic['netw_bytes'], dic['nr_obj'],
                                                                dic['sum_syn'], dic['sum_http'],
                                                                dic['sum_rcv_time'])
                q = stub2 % (s, v)
                try:
                    self.conn.execute_query(q)
                except sqlite3.Error as e:
                    logger.error("Error in insert to aggregate {0}".format(e))
                    logger.error(q)
                    continue

        logger.info('Aggregate tables populated.')
        return True

    def execute(self, query):
        return self.conn.execute_query(query)

    def update_sent(self, arr):
        if len(arr) > 1:
            q = '''update {0} set is_sent = 1 where sid in {1}'''.format(self.tables['aggr_sum'], tuple(arr))
        else:
            q = '''update {0} set is_sent = 1 where sid = {1}'''.format(self.tables['aggr_sum'], arr[0])
        self.execute(q)
        logger.debug("Updated is_sent for sessions {0}".format(tuple(arr)))

