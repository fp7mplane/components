#!/usr/bin/python
#
# mPlane QoE Probe
#
# (c) 2013-2014 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Salvatore Balzano <balzano@eurecom.fr>
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
import datetime
import operator
import os

logger = logging.getLogger("Parser")

class Parser():
    def __init__(self, tstatfile, harfile, client_id):
        self.tstatfile = tstatfile
        self.harfile = harfile
        self.client_id = client_id
        self.har_dict = {}

    def parseTstat(self, separator="\n"):
        log = open(self.tstatfile, 'r')
        from_tstat_lines = log.readlines()
        log.close()
        from_har = self.har_dict['entries'].keys()
        found = []
        #json_metrics = ''
        rows = [line[:-1].split(" ") for line in from_tstat_lines]
        for line in rows:
            if line[59] is not "":  # avoid HTTPS sessions
                line[59] = line[59][:-1]
                httpids = line[59].split(",")
                for elem in httpids:
                    if elem in from_har:
                        app_rtt = float(line[15])+float(line[26])
                        metrics = {'local_ip': line[0], 'local_port': line[1],
                                   'syn_time': line[13],
                                   'app_rtt': app_rtt,
                                   'remote_ip': line[30],
                                   'remote_port': line[31],
                                   }
                        self.har_dict['entries'][elem].update(metrics)
                        found.append(elem)

        # if elem is not found in tstat, then find the most similar uri and copy data from that
        remaining = [x for x in from_har if x not in found]
        if remaining:
            logger.warning("{0} elements from har file are not logged in tstat {1}".format(len(remaining), remaining))
            matches = {}
            for httpid in remaining:
                #logger.debug("from remaining: {0}".format(httpid))
                uri = self.har_dict['entries'][httpid]['uri']
                length = {}
                for k, v in self.har_dict['entries'].items():
                    #logger.debug("cycling har_dict = {0} - {1}".format(k, v['uri']))
                    if k not in remaining:
                        #logger.debug("not found in remaining = {0}".format(k))
                        length[k] = len(os.path.commonprefix([uri, v['uri']]))
                    #    logger.debug("common path with {0} ({1}) : {2}".format(httpid, length[k],
                    #                                                           os.path.commonprefix([uri, v['uri']])))
                    #else:
                    #    logger.debug("found in remaining = {0}.. proceed".format(k))

                if length:
                    #logger.debug("length = {0}".format(length))
                    candidate = max(length.items(), key=operator.itemgetter(1))[0]
                    #logger.debug("candidate = {0}".format(candidate))
                    matches[httpid] = candidate
                    #logger.debug("matches = {0}".format(matches))

            for k, v in matches.items():
                ref = self.har_dict['entries'][v]
                metrics = {'local_ip': ref['local_ip'], 'local_port': ref['local_port'],
                           'syn_time': ref['syn_time'],
                           'app_rtt': ref['app_rtt'],
                           'remote_ip': ref['remote_ip'],
                           'remote_port': ref['remote_port'],
                           }
                self.har_dict['entries'][k].update(metrics)

            if matches:
                logger.info("{0} objects ingested from similar objects (most similar uri).".format(len(matches)))
            else:
                pass
            #    logger.info("No data ingested.")
        else:
            logger.debug("No items in remaining array")

    @staticmethod
    def get_datetime(harstr):
        datetimestr = harstr.replace("T", " ")[:harstr.replace("T", " ").rfind("-")]
        return datetime.datetime.strptime(datetimestr, '%Y-%m-%d %H:%M:%S.%f')

    def parseHar(self):
        with open(self.harfile) as hf:
            json_data = json.load(hf)

        data = json_data['log']
        page = data['pages'][0]
        session_url = page['id']
        session_start = Parser.get_datetime(page["startedDateTime"])
        full_load_time = page["pageTimings"]["onLoad"]
        logger.info("Found {0} objects on in the har file.".format(len(data['entries'])))
        self.har_dict = {'session_url': session_url,
                         'probe_id': self.client_id,
                         'session_start': session_start,
                         'full_load_time': full_load_time,
                         'entries': None}
        har_metrics = {}
        for entry in data['entries']:
            request_ts = Parser.get_datetime(entry["startedDateTime"])
            firstByte = Parser.get_datetime(entry["TimeToFirstByte"])
            end_ts = Parser.get_datetime(entry["endtimeTS"])

            request = entry['request']
            url = request['url']
            for header in request['headers']:
                if header['name'] == "httpid":
                    httpid = header['value']

            if not httpid:
                logger.error("Unable to find httpid in Har file: skipping {0}".format(url))
                continue

            response = entry['response']
            content = response['content']
            size = content['size']
            try:
                mime = content['mimeType'].split(";")[0]  # eliminate charset utf-8 from text
            except AttributeError: #mimeType not present
                mime = ''

            time = entry['time']

            #har_metrics = {unicode('session_url'): session_url, unicode('full_load_time'): unicode(full_load_time),
            #               unicode('uri'): url, unicode('request_ts'): request_ts, unicode('content_type'): mime,
            #               unicode('session_start'): session_start, unicode('body_bytes'): unicode(size),
            #               unicode('first_bytes_rcv'): unicode(firstByte), unicode('end_time'): unicode(end_ts),
            #               unicode('rcv_time'): unicode(time), unicode('tab_id'): unicode('0'),
            #               unicode('httpid'): httpid,
            #               unicode('probe_id'): unicode(self.client_id)}
            har_metrics[str(httpid)] = {'uri': url, 'request_ts': request_ts,
                                        'content_type': mime, 'body_bytes': size,
                                        'first_bytes_rcv': firstByte,
                                        'end_time': end_ts, 'rcv_time': time}

            self.har_dict['entries'] = har_metrics

    def parse(self):
        self.parseHar()
        try:
            self.parseTstat()
        except Exception as e:
            logger.error(e)
        return self.har_dict

