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
import configparser


class Configuration():
    def __init__(self, conf_file):
        self.config = configparser.RawConfigParser()
        self.config._interpolation = configparser.ExtendedInterpolation()
        self.config.read(conf_file)

    def __extract_values_to_dictionary(self, list_of_params):
        res = {}
        for tup in list_of_params:
            res[tup[0]] = tup[1]
        return res
        
    def get_database_configuration(self):
        return self.__extract_values_to_dictionary(self.config.items('database'))

    def get_phantomjs_configuration(self):
        return self.__extract_values_to_dictionary(self.config.items('phantomjs'))

    def get_tstat_configuration(self):
        return self.__extract_values_to_dictionary(self.config.items('tstat'))

    def get_jsonserver_configuration(self):
        return self.__extract_values_to_dictionary(self.config.items('server'))

    def get_flume_configuration(self):
        return self.__extract_values_to_dictionary(self.config.items('flume'))

    def get_base_configuration(self):
        return self.__extract_values_to_dictionary(self.config.items('base'))
