#!/usr/bin/python3
import sys
import os
import shutil
import subprocess
import threading
import tarfile
import logging
import logging.config
import urllib.request
import json
import time
import datetime

from .probe.configuration import Configuration
from .probe.phantomjsmanager import PJSLauncher, PhantomjsNotFoundError
from .probe.activemeasure import ActiveMonitor
from .probe.sender import JSONClient
from .probe.utils import clean_tmp_files

from .db.dbclient import DBClient
from .diagnosis.localdiagnosis import LocalDiagnosisManager



package_directory = os.path.dirname(os.path.abspath(__file__))

logging.config.fileConfig(os.path.join(package_directory, 'conf/logging.conf'))


class TstatThread(threading.Thread):

    def __init__(self, config, flag):
        self.flag = flag
        if self.flag == 'start':
            self.script = config.get_tstat_configuration()['start']
            self.tstatpath = os.path.join(config.get_tstat_configuration()['dir'], 'tstat/tstat')
            self.interface = config.get_tstat_configuration()['netinterface']
            self.netfile = config.get_tstat_configuration()['netfile']
            self.outdir = config.get_tstat_configuration()['tstatout']
            self.is_daemon = True
        else:
            self.script = config.get_tstat_configuration()['stop']
            self.is_daemon = False

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = self.is_daemon
        logger.debug("TstatThread running [%s] is_daemon = %s..." % (os.path.basename(self.script), str(self.is_daemon)))
        thread.start()

    def run(self):
        if self.flag == 'start':
            cmd = "%s %s %s %s %s" % (self.script, self.tstatpath, self.interface, self.netfile, self.outdir)
            p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False).wait()
        else:
            p = subprocess.Popen(self.script, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False).wait()


class FlumeNotFoundError(FileNotFoundError):
    pass


def start_flume_process(config):
    ex = "{0}{1}".format(config.get_flume_configuration()['flumedir'], "/bin/flume-ng")
    if not os.path.exists(ex):
        raise FlumeNotFoundError

    confdir = config.get_flume_configuration()['confdir']
    conffile = config.get_flume_configuration()['conffile']
    agentname = config.get_flume_configuration()['agentname']
    #flumelogging = "-Dflume.root.logger=INFO,console"
    cmd = "{0} agent -c {1} -f {2} -n {3}".format(ex, confdir, conffile, agentname) #, flumelogging)
    proc = subprocess.Popen(cmd.split())
    return proc


def stop_flume_process():
    import signal
    ps = subprocess.Popen(('ps', 'aux'), stdout=subprocess.PIPE)
    output = subprocess.check_output(('grep', 'flume'), stdin=ps.stdout)
    ps.wait()
    pid = int(output.split()[1])
    os.kill(pid, signal.SIGKILL)

###mplane component needs to call this
logger = logging.getLogger('probe')


class PhantomProbe():
        
    def __init__(self, conffile, url):
        self.config = Configuration(conffile)
        self.url = url
        self.__prepare()
        self.diagnosis = {}

    def __prepare(self):
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d-%H%M%S')
        self.backup_dir = os.path.join(self.config.get_base_configuration()['backupdir'], st)
        logger.info("Launching the probe...")
        if not os.path.isdir(self.config.get_flume_configuration()['outdir']):
            os.makedirs(self.config.get_flume_configuration()['outdir'])
        if not os.path.isdir(self.backup_dir):
            os.makedirs(self.backup_dir)
        self.tstat_out_file = self.config.get_database_configuration()['tstatfile']
        self.harfile = self.config.get_database_configuration()['harfile']
        try:
            self.launcher = PJSLauncher(self.config)
        except PhantomjsNotFoundError:
            logger.error("PhantomJS browser not found. Exiting.")
            sys.exit(-1)

        logger.debug('Backup dir set at: %s' % self.backup_dir)
        self.loc_info = self._get_location()
        if not self.loc_info:
            logger.warning("No info on location retrieved.")
        self.dbcli = DBClient(self.config, self.loc_info, create=True)
        try:
            self.flumeprocess = start_flume_process(self.config)
        except FlumeNotFoundError:
            self.flumeprocess = None
            logger.warning("Flume not found, sending to server instead.")

        self.pjs_config = self.config.get_phantomjs_configuration()
        t = TstatThread(self.config, 'start')
        logger.info("Ready to browse: {0}".format(self.url))
        
    def _get_location(self):
        loc_request = urllib.request.Request('http://ipinfo.io')
        loc_request.add_header('User-Agent', 'curl/7.30.0')
        response = urllib.request.urlopen(loc_request)
        return json.loads(response.read().decode('utf-8'))

    def browse(self):
        try:
            logger.debug("self.launcher.browse_url")
            stats = self.launcher.browse_url(self.url)
            logger.debug("self.launcher.browse_url: done")
        except AttributeError:
            logger.error("Problems in browser thread. Aborting session...")
            logger.error("Forcing tstat to stop.")
            s = TstatThread(self.config, 'stop')  # TODO check if tstat really quit
            sys.exit("Problems in browser thread. Aborting session...")
        if not stats:
            logger.warning('Problem in session to [%s].. skipping' % (self.url))
            clean_tmp_files(self.backup_dir, [self.tstat_out_file, self.harfile], self.url, True)
            sys.exit("Problems in stats collecting. Quitting...")
        if not os.path.exists(self.tstat_out_file):
            logger.error('tstat outfile missing. Check your network configuration.')
            sys.exit("tstat outfile missing. Check your network configuration.")
            
        s = TstatThread(self.config, 'stop')  # TODO check if tstat really quit
        self.dbcli.load_to_db(stats)
        logger.info('Ended browsing to %s' % (self.url))
        self.passive = self.dbcli.pre_process_raw_table()
        clean_tmp_files(self.backup_dir, [self.tstat_out_file, self.harfile], self.url, False)
        logger.debug('Saved backup files.')
        return True

    def execute(self):
        logger.info("Starting browsing...")
        if self.browse():
            logger.info("Browsing done.")
            monitor = ActiveMonitor(self.config, self.dbcli)
            self.active = monitor.run_active_measurement()
            logger.debug('Ended Active probing to url %s' % (self.url))
            for tracefile in [f for f in os.listdir('.') if f.endswith('.traceroute')]:
                os.remove(tracefile)
            l = LocalDiagnosisManager(self.dbcli, self.url)
            self.diagnosis = l.run_diagnosis(self.passive, self.active)
        else:
            self.diagnosis = {"Warning": "Unable to perform browsing"}
        self.send_results()

    def send_results(self):
        jc = JSONClient(self.config, self.dbcli)
        measurements = jc.prepare_data()
        to_update = [el['sid'] for el in measurements]
        csv_path_fname_list = jc.save_csv_files(measurements)
        if self.flumeprocess:
            logger.info("Waiting for flume to stop...")
            time.sleep(5)
            stop_flume_process()
        else:
            logger.info("Sending data to server...")
            try:
                jc.send_csv()
            except TimeoutError:
                logger.error("Timeout in server connection")
                pass
            finally:
                logger.info("Done.")
        self.dbcli.update_sent(to_update)
        try:
            for csv_path_fname in csv_path_fname_list:
                shutil.copyfile(csv_path_fname, os.path.join(self.backup_dir, os.path.basename(csv_path_fname)))
        except FileNotFoundError:
            pass

        logger.info("Packing backups...")
        for root, _, files in os.walk(self.backup_dir):
            if len(files) > 0:
                tar = tarfile.open("%s.tar.gz" % self.backup_dir, "w:gz")
                tar.add(self.backup_dir)
                tar.close()
                logger.info('tar.gz backup file created.')
        shutil.rmtree(self.backup_dir)
        logger.info('Done.')
        
    def get_result(self):
        return self.diagnosis
        
if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-c", "--conf", dest="conf_file", type="string", help="specify a configuration file", metavar="FILE")
    parser.add_option("-u", "--url", dest="url", type="string", help="specify a url", metavar="URL")
    (options, args) = parser.parse_args()
    if not options.url:
        print("Use -h for complete list of options")
        print("Usage: {} -u url_to_browse [-c conf_file] ".format(__file__))
        sys.exit(0)

    url = options.url

    if not options.conf_file:
        conffile = os.path.join(package_directory, 'conf/firelog.conf')
    else:
        if not os.path.isfile(options.conf_file):
            print("Use -h for complete list of options: wrong configuration file")
            sys.exit(0)
        conffile = options.conf_file

    f = PhantomProbe(conffile, url)
    f.execute()
    print(f.get_result())
