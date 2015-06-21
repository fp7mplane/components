#!/usr/bin/python
#
# mPlane QoE Server
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
import math


class Cusum():
    def __init__(self, cusum_name, th, i, alpha=0.875, c=0.5):
        self.name = cusum_name
        self.th = th
        self.alpha = alpha
        self.c = c
        self.m = 0.0
        self.var = 0.0
        self.cusum = 0.0
        self.i = i  # keep track of count, locally

    def compute(self, list_):
        for sample in list_:
            self.i += 1
            if self.i == 1:
                self.m = sample
                self.cusum = sample
                cusum_p = self.cusum
                self.adjust_th(cusum_p)
            else:
                m_p = self.alpha * self.m + (1 - self.alpha) * sample   #EWMA
                var_p = self.alpha * self.var + (1 - self.alpha) * pow((sample - m_p), 2)
                L = sample - (m_p + self.c * math.sqrt(var_p))  # incremento cusum
                cusum_p = self.cusum + L
                if cusum_p < 0:
                    cusum_p = 0.0

                if cusum_p > self.th:
                    if self.i < 100:  # FIXME end of training
                        self.adjust_th(self.cusum)
                    return cusum_p
                else:
                    self.m = m_p
                    self.var = var_p
                    self.cusum = cusum_p
        return None

    def get_mean_var(self):
        return self.m, self.var

    def adjust_th(self, computed_cusum):
        if self.i == 1:
            self.th = computed_cusum
        self.th = (1 - self.alpha) * computed_cusum + self.alpha * self.th

    def get_cusum_value(self):
        return self.cusum

    # N-1 volte
    # N-esima : new_th = new_th + 3 [ self.alpha * var + (1 - self.alpha) * pow((sample - m_p), 2)]
    #def save_new_th(self, computed_cusum):
    #    new_th = (1 - self.alpha) * computed_cusum + self.alpha * self.th
        #self.dbconfig.set('cusum', 'th', new_th)
        #with open(cusum_conf, 'wb') as configfile:
        #    self.dbconfig.write(configfile)
    #    return new_th

    def get_th(self):
        return self.th

    def compute_new_threshold(self, cusum_name):
        new_th = self.m + 3 * self.var
        return new_th

