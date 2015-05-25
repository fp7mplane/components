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

import socket
import time
from socket import error as SocketError
import datetime
from datetime import datetime

def establish_connection(IP, PORT):
    established = False
    sock = socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    while not established:
        try:
            sock.bind((IP, PORT))
            established = True
            sock.settimeout(None)
            sock.listen(1)
            print("Listening...")
        except SocketError as e:
            print(str(e) + ". Retrying soon...")
            sock.close()
            established = False
            time.sleep(2)
        except socket.timeout as e:
            print(str(e) + ". Listening timed out.")
            return None
    return sock

def readlines(conn, s, TCP_IP, TCP_PORT, recv_buffer=4096, delim='\n'):
    buffer = ''
    data = True
    while data:
        data = conn.recv(recv_buffer)
        if len(data) == 0:
            time.sleep(1)
            # s.shutdown(socket.SHUT_RDWR)
            s.close()
            time.sleep(2)
            s = establish_connection(TCP_IP, TCP_PORT)
            conn, addr = s.accept()
            time.sleep(1)
            data = True
        else:
            buffer += data.decode("utf-8")
            #print(buffer)
            while buffer.find(delim) != -1:
                line, buffer = buffer.split('\n', 1)
                yield line
    return


def run(repoip, repoport):
    TCP_IP = repoip
    TCP_PORT = int(repoport)
    BUFFER_SIZE = 4096  # Normally 1024, but we want fast response
    s = establish_connection(TCP_IP, TCP_PORT)
    if s != None:
        try:
            conn, addr = s.accept()
            print('Connection address:', addr)
            for line in readlines(conn, s, TCP_IP, TCP_PORT):
                print(line)
            conn.close()
        except socket.timeout as e:
            print(str(e) + ". Accepting connections timed out.")
            return None
    else:
        print('Exit')