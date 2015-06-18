# (c) 2013-2014 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Ali Safari Khatouni
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
from time import sleep, time
from socket import socket
from socket import error as SocketError


import mplane.utils

from collections import OrderedDict
from threading import Thread
import tornado.web
import tornado.httpserver
import json

from mplane.components.tstat.repository_importers.rrd_file_grouping import rrd_file_classification



RESULT_PATH_INDIRECT = "register/result/indirect_export"

# These are default carbon IP and PORT address
CARBON_SERVER = '127.0.0.1'
CARBON_PORT = 2003


def carbonconnection():

    """ 
    This function open a socket connection to the Graphite server

    """
    global  sock
    established = False
    sock = socket()
    while not established:
        try:
            sock.connect((CARBON_SERVER, CARBON_PORT))
            established = True
            print("Connected to CARBON server...")
        except SocketError as e:
            print(str(e) + ". Retry to connect in 5 seconds...")
            established = False
            sleep(5)


def add_result(msg, dn):
    """Add a result. Check for duplicates and if result is expected."""

    if len(msg) == 0:
        print("Received Empty list")
        return True

    send_result_to_graphite(dn ,msg)
    return True

def send_result_to_graphite (d, metric):

    """
        Implements the data renaming and sendin to Graphite 
        Server

    """
    carbonconnection()
    message_carbon = ""

    for field in metric:

        readable_name = rrd_file_classification (field[0])
        timestamp = field[1]
        value = field[2]

        Component_Id = d.split("-")

        lines   = ['tstat.%s.%s %f %f' % (str(Component_Id[-1]), str(readable_name), float(value), float(timestamp))]

        message_carbon += '\n'.join(lines) + '\n'


    sock.sendall(bytes(message_carbon,'UTF-8')) 

    return

class HttpServer(object):
    """
    Implements an mPlane HTTP serverpoint for component-push workflows. 
    This server endpoint can register capabilities sent by components, then expose 
    Specifications for which the component will periodically check, and receive Results or Receipts
 
    This HttpServer aggregates capabilities of the same type.
    Also, it exposes Capabilities to a Client, receives Specifications from it, and returns Results.
    
    Performs Authentication (both with Probes and Client) and Authorization (with Client)
    Caches retrieved Capabilities, Receipts, and Results.
    """
    def __init__(self,listen_ip4, listen_port, config):
        self.tls = mplane.tls.TlsState(config)
        application = tornado.web.Application([
            (r"/" + RESULT_PATH_INDIRECT, IndirectResultHandler, {'tlsState': self.tls}),
            (r"/" + RESULT_PATH_INDIRECT + "/", IndirectResultHandler, {'tlsState': self.tls})
        ])
        http_server = tornado.httpserver.HTTPServer(application, ssl_options=self.tls.get_ssl_options())
        http_server.listen(listen_port, listen_ip4)
        t = Thread(target=self.listen_in_background)
        t.setDaemon(True)
        t.start()

        print("new Repository: "+str(listen_ip4)+":"+str(listen_port))
   
        # structures for storing Results
        self._results = OrderedDict()
    
    def listen_in_background(self):
        """
        The server listens for requests in background, while 
        the Repository remains accessible
        """
        tornado.ioloop.IOLoop.instance().start()

    def _handle_exception(self, exc):
        print(repr(exc))






class MPlaneHandler(tornado.web.RequestHandler):
    """
    Abstract tornado RequestHandler that allows a
    handler to respond with an mPlane Message.

    """

    def _respond_message(self, msg):
        """
        Returns an HTTP response containing a JSON message

        """
        self.set_status(200)
        self.set_header("Content-Type", "application/x-mplane+json")
        self.write(mplane.model.unparse_json(msg))
        self.finish()

    def _respond_plain_text(self, code, text = None):
        """
        Returns an HTTP response containing a plain text message

        """
        self.set_status(code)
        if text is not None:
            self.set_header("Content-Type", "text/plain")
            self.write(text)
        self.finish()

    def _respond_json_text(self, code, text = None):
        """
        Returns an HTTP response containing a plain text message

        """
        self.set_status(code)
        if text is not None:
            self.set_header("Content-Type", "application/x-mplane+json")
            self.write(text)
        self.finish()


class IndirectResultHandler(MPlaneHandler):
    """
    Receives results of specifications
    """

    def initialize(self, tlsState):
        self.tls = tlsState

    def post(self):
        peer_dn = self.tls.extract_peer_identity(self.request)
        # check the class of the certificate (Client, Component, Repository).
        # this function can only be used by components
        if (peer_dn.find("Components") == -1):
            self._respond_plain_text(401, "Not Authorized. Only Components can use this function")
            return
        
        # unwrap json message from body
        if (self.request.headers["Content-Type"] == "application/json"):
            msg = json.loads(self.request.body.decode("utf-8"))
        else:
            self._respond_plain_text(400, "Invalid format")
            return

        if isinstance(msg, list):
            
            # hand message to repository
            if add_result(msg, peer_dn):
                mplane.utils.print_then_prompt("Result received by " + peer_dn)
                self._respond_plain_text(200)
                return
            else:
                self._respond_plain_text(403, "Unexpected result")
                return
        else:
            self._respond_plain_text(400, "Not a result (or exception)")
            return
