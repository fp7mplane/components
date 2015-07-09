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
import subprocess
import psutil
import time
import logging
import threading
import os
import re

logger = logging.getLogger('PJSLauncher')


class PhantomjsNotFoundError(FileNotFoundError):
    pass


class BrowserThread(threading.Thread):
    def __init__(self, cmd, outf, errf):
        self.cmd = cmd
        self.process = None
        self.outfile = outf
        self.errfile = errf
        self.mem = -1
        self.cpu = -1
        self.flag = False

    def run(self, timeout):
        def target():
            o = open(self.outfile, 'a')
            e = open(self.errfile, 'a')
            logger.debug('Browsing Thread started')
            FNULL = open(os.devnull, 'w')
            self.process = subprocess.Popen(self.cmd, stdout=FNULL, stderr=e, shell=True)
            memtable = []
            cputable = []
            while self.process.poll() is None:
                arr = psutil.cpu_percent(interval=0.1, percpu=True)
                cputable.append(sum(arr) / float(len(arr)))
                memtable.append(psutil.virtual_memory().percent)
                time.sleep(1)
            #if self.process.poll() == 0:
            self.mem = float(sum(memtable) / len(memtable))
            self.cpu = float(sum(cputable) / len(cputable))
            logger.debug('Browsing Thread finished')
            o.close()
            e.close()

        thread = threading.Thread(target=target)
        thread.start()

        thread.join(timeout)
        timeout_flag = False
        if thread.is_alive():
            logger.warning('Timeout expired: terminating process')
            self.process.terminate()
            logger.warning("retcode: {0}".format(self.process.returncode))
            thread.join()
            timeout_flag = True
        
        return self.flag, self.mem, self.cpu, timeout_flag
                

class PJSLauncher():
    def __init__(self, config):
        self.config = config
        self.pjs_config = self.config.get_phantomjs_configuration()
        if not os.path.exists(os.path.join(self.pjs_config['dir'], "bin/phantomjs")):
            raise PhantomjsNotFoundError('PhantomJS browser not found')
        self.osstats = {}
        logger.debug('Loaded configuration')

    #@staticmethod
    #def check_for_redirection(urlx):
    #    loc = urllib.request.Request(urlx)
    #    loc.add_header('User-Agent', 'curl/7.30.0')
    #    res = urllib.request.urlopen(loc)
    #    result = res.geturl()
    #    if result is not urlx:
    #        logger.debug("{0} was redirected to {1}".format(urlx, result))
    #    return result

    def browse_url(self, urlx):
        if not re.match('http://', urlx):
            url = 'http://' + urlx.strip()
        else:
            url = urlx.strip()
        if url[-1] != '\/':
            url += '/'

        #url = self.check_for_redirection(url)
        logger.info('Browsing %s', url)
        res = {'mem': 0.0, 'cpu': 0.0}
        cmdstr = "%s/bin/phantomjs %s %s" % (self.pjs_config['dir'], self.pjs_config['script'], url)
        cmd = BrowserThread(cmdstr, self.pjs_config['thread_outfile'], self.pjs_config['thread_errfile'])
        t = int(self.pjs_config['thread_timeout'])
        flag, mem, cpu, timeout_flag = cmd.run(timeout=t)
        if timeout_flag:
            logger.error('Error in browsing thread reported.')
            return None

        if not flag:
            res['mem'] = mem
            res['cpu'] = cpu
            logger.info('%s: mem = %.2f, cpu = %.2f' % (url, res['mem'], res['cpu']))
        else:
            logger.warning('Problems in browsing thread. Need to restart browser...')
            time.sleep(5)
        self.osstats[url] = res
        return self.osstats

