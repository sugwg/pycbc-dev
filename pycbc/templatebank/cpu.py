# Copyright (C) 2011 Karsten Wiesner
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


#
# =============================================================================
#
#                                   Preamble
#
# =============================================================================
#
"""
Cpu version of the template bank. Status: Very prototyping
"""

from pycbc.templatebank.base import TemplateBankBase
from pycbc.datavector.clayer.cpu import complex_vector_single_cpu_t as WaveformFrequencySeries

import logging


class TemplateBankCpu(TemplateBankBase):

    def __init__(self, n_templates, waveform_length, waveform_delta_x):
        self.__logger= logging.getLogger('pycbc.TemplateBankCpu')
        super(TemplateBankCpu, self).__init__(n_templates, waveform_length,
                                  waveform_delta_x, WaveformFrequencySeries)

    #def __del__(self): 
    #    print "called TemplateBankCpu destructor"
                                
