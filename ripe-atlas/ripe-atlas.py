#
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
# mPlane Protocol Reference Implementation
# ICMP Ping probe component code
#
# (c) 2013-2014 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Mirko Schiavone <schiavone@ftw.at>
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

"""
Implements a proxy for the RIPE Atlas Toolbox (https://github.com/pierdom/atlas-toolbox) 
for integration into the mPlane reference implementation.

"""

import subprocess
from datetime import datetime
import mplane.model
import mplane.scheduler

import shlex
import psycopg2

def ripeatlas_list_probe_capability(db_connect_params = None):
    cap = mplane.model.Capability(label="ripeatlas-list-probe", when = "now")
    cap.add_parameter("ripeatlas.db_connect_params", db_connect_params)
    cap.add_parameter("ripeatlas.optionsline")
    cap.add_result_column("ripeatlas.list.probe.resultline")
    return cap

def ripeatlas_udm_lookup_capability(db_connect_params = None):
    cap = mplane.model.Capability(label="ripeatlas-udm-lookup", when = "now")
    cap.add_parameter("ripeatlas.db_connect_params", db_connect_params)
    cap.add_parameter("ripeatlas.optionsline")
    cap.add_result_column("ripeatlas.udm.lookup.resultline")
    return cap

def ripeatlas_udm_create_capability(db_connect_params = None):
    cap = mplane.model.Capability(label="ripeatlas-udm-create", when = "now")
    cap.add_parameter("ripeatlas.db_connect_params", db_connect_params)
    cap.add_parameter("ripeatlas.optionsline")
    cap.add_result_column("ripeatlas.udm.create.resultline")
    return cap

def ripeatlas_udm_status_capability(db_connect_params = None):
    cap = mplane.model.Capability(label="ripeatlas-udm-status", when = "now")
    cap.add_parameter("ripeatlas.db_connect_params", db_connect_params)
    cap.add_parameter("ripeatlas.optionsline")
    cap.add_result_column("ripeatlas.udm.status.resultline")
    return cap

def ripeatlas_udm_result_capability(db_connect_params = None):
    cap = mplane.model.Capability(label="ripeatlas-udm-result", when = "now")
    cap.add_parameter("ripeatlas.db_connect_params", db_connect_params)
    cap.add_parameter("ripeatlas.optionsline")
    cap.add_result_column("ripeatlas.udm.result.resultline")
    return cap

def ripeatlas_udm_stop_capability(db_connect_params = None):
    cap = mplane.model.Capability(label="ripeatlas-udm-stop", when = "now")
    cap.add_parameter("ripeatlas.db_connect_params", db_connect_params)
    cap.add_parameter("ripeatlas.optionsline")
    cap.add_result_column("ripeatlas.udm.stop.resultline")
    return cap


def services(db_connect_params):
    services = []
    services.append(RipeAtlasService(ripeatlas_list_probe_capability(db_connect_params)))
    services.append(RipeAtlasService(ripeatlas_udm_lookup_capability(db_connect_params)))
    services.append(RipeAtlasService(ripeatlas_udm_create_capability(db_connect_params)))
    services.append(RipeAtlasService(ripeatlas_udm_status_capability(db_connect_params)))
    services.append(RipeAtlasService(ripeatlas_udm_result_capability(db_connect_params)))
    services.append(RipeAtlasService(ripeatlas_udm_stop_capability(db_connect_params)))
    return services

class RipeAtlasService(mplane.scheduler.Service):
    def __init__(self, cap):
        super(RipeAtlasService, self).__init__(cap)

    def run(self, spec, check_interrupt):
        # set command
        cmd_argv = []
        # manage db connection
        pg_con = None
        pg_cur = None
        result_column_name = ""
        start_time = str(datetime.utcnow())
        if "ripeatlas-list-probe" in spec.get_label():
            cmd_argv = ["mplane/components/ripe-atlas/atlas-toolbox/probe-list.pl"]
            # different capability must have different result_column name
            result_column_name = "ripeatlas.list.probe.resultline"
        elif "ripeatlas-udm-lookup" in spec.get_label():
            cmd_argv = ["mplane/components/ripe-atlas/atlas-toolbox/udm-lookup.pl"]
            result_column_name = "ripeatlas.udm.lookup.resultline" 
        elif "ripeatlas-udm-create" in spec.get_label():
            cmd_argv = ["mplane/components/ripe-atlas/atlas-toolbox/udm-create.pl"]
            result_column_name = "ripeatlas.udm.create.resultline"
        elif "ripeatlas-udm-status" in spec.get_label():
            cmd_argv = ["mplane/components/ripe-atlas/atlas-toolbox/udm-status.pl"]
            result_column_name = "ripeatlas.udm.status.resultline"
        elif "ripeatlas-udm-result" in spec.get_label():
            cmd_argv = ["mplane/components/ripe-atlas/atlas-toolbox/udm-result.pl"]
            result_column_name = "ripeatlas.udm.result.resultline"
        elif "ripeatlas-udm-stop" in spec.get_label():
            cmd_argv = ["mplane/components/ripe-atlas/atlas-toolbox/udm-stop.pl"]
            result_column_name = "ripeatlas.udm.stop.resultline"
        else:
            ValueError("Capability not supported")

        # set command options
        if spec.has_parameter("ripeatlas.optionsline"):
            cmd_argv += shlex.split(spec.get_parameter_value("ripeatlas.optionsline"))
        if spec.has_parameter("ripeatlas.db_connect_params"):
            pg_con = psycopg2.connect(spec.get_parameter_value("ripeatlas.db_connect_params"))
            pg_cur = pg_con.cursor()
             
        
        # run command
        ripe_atlas_process = subprocess.Popen(cmd_argv, stdout=subprocess.PIPE)

        # derive a result from the specification
        res = mplane.model.Result(specification=spec)

        # set results values
        res_cnt = 0
        for line in ripe_atlas_process.stdout:
            line_dec = line.decode("utf-8")
            line_dec = line_dec.rstrip("\n")
            res.set_result_value(result_column_name, line_dec, res_cnt)
            if pg_cur is not None:
                pg_cur.execute("INSERT INTO ripe_results VALUES ('"
                    + str(start_time) + "','"
                    + str(spec.get_label()) + "',"
                    + str(res_cnt) + ",'"
                    + str(line_dec) + "'"
                    + ")")
            res_cnt += 1

        # set endtime
        end_time = str(datetime.utcnow())
        # put actual start and end time into result
        res.set_when(mplane.model.When(start_time, end_time))

        # shut down and reap
        try:
            ripe_atlas_process.kill()
        except OSError:
            pass
        ripe_atlas_process.wait()
        
        if pg_con is not None:
            pg_con.commit()
            pg_con.close()
            pg_cur.close()
        return res
