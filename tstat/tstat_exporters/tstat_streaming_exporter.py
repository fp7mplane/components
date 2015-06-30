# (c) 2013-2014 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Stefano Traverso
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
import multiprocessing as mp
import re
import time
import subprocess
import socket
import errno
import signal
from socket import error as SocketError
import logging
import datetime
from unidecode import unidecode

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

class TimeoutError(Exception):
    pass

class timeout:
    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message
    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)
    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)
    def __exit__(self, type, value, traceback):
        signal.alarm(0)

def establish_connection(IP, PORT, filename):
    established = False
    sock = socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_STREAM)
    while not established:
        try:
            sock.connect((IP, PORT))
            established = True
            logging.info("Connection established!!")
        except SocketError as e:
            logging.warning(str(e) + ". Retrying soon...")
            time.sleep(2)
            sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_STREAM)

            # sock.shutdown(socket.SHUT_RDWR)
            # sock.close()            
    logging.info("Transmitting %s" % filename)
    return sock

def tail_tstat_log(filename, address, port, timeoutset, pid):
    """This function is called for each detected tstat log present in the input folder. Each input log is
    handled by an independent subprocess, so that all the available cores are employed.
    """
    subp = None
    subp = subprocess.Popen('tail -f %s' % filename, stdout=subprocess.PIPE, shell=True)
    subpfile = open("/tmp/log_to_tcp_tail_pid.txt", "w")
    subpfile.write("%d\n" % subp.pid)
    subpfile.close()
    old_check_time = 0
    TCP_IP = address
    TCP_PORT = int(port)
    MESSAGE = "Hello"
    TIMEOUT = 10
    line = None
    sock = establish_connection(TCP_IP, TCP_PORT, filename)
    while True:
        try:
            with timeout(seconds=((int(timeoutset)+1)*60)):
                line = subp.stdout.readline().decode("ascii", 'ignore')
                # print(line)
                old_check_time = datetime.datetime.now()
                MESSAGE = unidecode(filename + " " + line[:-1] + "\n")
                try:
                    sock.sendall(bytes(MESSAGE, "utf-8"))
                except SocketError as e:
                    logging.warning(str(e) + ". Establishing again...")
                    time.sleep(1)
                    sock.close()
                    sock = establish_connection(TCP_IP, TCP_PORT, filename)
        except TimeoutError:
            logging.warning("Timeout! Log ended now. Closing the read process for %s..." % filename)
            subp.terminate()
            sock.close()
            return
    subp.terminate()
    return

def initializer(terminating_):
    """This places terminating in the global namespace of the worker subprocesses.
    This allows the worker function to access `terminating` even though it is
    not passed as an argument to the function. Good to terminate the script in any
    moment with Crtl+C."""
    global terminating
    terminating = terminating_  

def run(repoip, repoport, logtype, logtime, logfolder, start_time, duration):

    terminating = mp.Event()
    files_in_dir = None
    # current_dir = sorted(os.listdir(opt.read), key=os.path.getctime)[-1]
    current_dir = logfolder + sorted([f for f in os.listdir(logfolder) if ".out" in f])[-1]
    # current_dir = commands.getstatusoutput("ls -tr "+ opt.read +" | grep -v delete | grep -v stderr")[1].split("\n")[-1]
    logging.info("Going to transmit on %s:%s for %d" % (repoip, repoport, duration))
    logging.info("The current log is %s from %s" % (current_dir, logfolder))
    counter = 0
    subp = None
    # Launch exporter on current_dir
    p = mp.Process(target=tail_tstat_log, args=(os.path.abspath(current_dir+"/"+logtype), repoip, repoport, logtime, counter))
    p.start()

    while (start_time + datetime.timedelta(seconds=duration)) >= datetime.datetime.utcnow():
        # Get the latest log in the directory
        files_in_dir = sorted([f for f in os.listdir(logfolder) if ".out" in f])
        # files_in_dir = commands.getstatusoutput("ls -tr "+ opt.read +" | grep -v delete | grep -v stderr")[1].split("\n")
        if len(files_in_dir) == 0:
            raise OSError
        new_dir = logfolder + files_in_dir[-1]
        if new_dir != current_dir:
            # New File!!
            logging.info("New log found! %s " % (os.path.abspath(new_dir+"/"+logtype)))
            counter += 1
            p_old = p
            # Terminate last process
            logging.info("Kill old log reader! %s " % (os.path.abspath(current_dir+"/"+logtype)))
            subpfile = open("/tmp/log_to_tcp_tail_pid.txt", "r")
            subp_pid = int(subpfile.readline().strip())
            subpfile.close()
            p_old.terminate()
            try:
                os.kill(subp_pid, signal.SIGKILL)
            except OSError as e:
                logging.warning(str(e))
                logging.warning("Process not killed by OS!")
            # Start new one
            logging.info("Start new log reader! %s " % (os.path.abspath(new_dir+"/"+logtype)))
            p = mp.Process(target=tail_tstat_log, args=(os.path.abspath(new_dir+"/"+logtype), repoip, repoport, logtime, counter))
            p.start()
            # Update variables
            current_dir = new_dir            
        time.sleep(0.1)
 
    p.terminate()
    # for f in files_in_dir:
    #     print(f)
 
    print("End.")
