# Copyright (C) 2012  Andrew Miller
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
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
'''
These are the unittests for the pycbc frame/cache reading functions
'''


import pycbc
import unittest
from pycbc.types import *
from pycbc.scheme import *
import pycbc.frame
import numpy
import base_test
import tempfile
import swiglal
from glue import lal
from pylal import frutils, Fr

import optparse
from optparse import OptionParser

_parser = OptionParser()

def _check_scheme(option, opt_str, scheme, parser):
    if scheme=='cuda' and not pycbc.HAVE_CUDA:
        raise optparse.OptionValueError("CUDA not found")

    if scheme=='opencl' and not pycbc.HAVE_OPENCL:
        raise optparse.OptionValueError("OpenCL not found")
    setattr (parser.values, option.dest, scheme)

_parser.add_option('--scheme','-s', action='callback', type = 'choice', choices = ('cpu','cuda','opencl'), 
                    default = 'cpu', dest = 'scheme', callback = _check_scheme,
                    help = 'specifies processing scheme, can be cpu [default], cuda, or opencl')

_parser.add_option('--device-num','-d', action='store', type = 'int', dest = 'devicenum', default=0,
                    help = 'specifies a GPU device to use for CUDA or OpenCL, 0 by default')

(_opt_list, _args) = _parser.parse_args()

#Changing the optvalues to a dict makes them easier to read
_options = vars(_opt_list)

# ********************GENERIC ARRAY TESTS ***********************

# By importing the current schemes array type, it will make it easier to check the  array types later

# Although these tests don't require CPU/GPU swapping of inputs, we will
# still inherit from the function_base so that we can use the check function.
class FrameTestBase(base_test.function_base):

    def checkCurrentState(self, inputs, results, places):
        super(FrameTestBase,self).checkCurrentState(inputs, results, places)
        for a in inputs:
            if isinstance(a,pycbc.types.Array):
                self.assertEqual(a.delta_t, self.delta_t)
                self.assertEqual(a.start_time, self.epoch)
                self.assertTrue(a.dtype == self.dtype)

    def setUp(self):
            
        # Number of decimal places to compare for single precision
        if self.dtype == numpy.float32 or self.dtype == numpy.complex64:
            self.places = 5
        # Number of decimal places to compare for double precision
        else:
            self.places = 13
            
        self.size = pow(2,10)

        if self.dtype == numpy.float32 or self.dtype == numpy.float64:
            self.kind = 'real'
        else:
            self.kind = 'complex'

        self.data1 = numpy.array(numpy.random.rand(self.size), dtype=self.dtype)
        self.data2 = numpy.array(numpy.random.rand(self.size), dtype=self.dtype)
        # If the dtype is complex, we should throw in some complex values as well
        if self.kind == 'complex':
            self.data1 += numpy.random.rand(self.size) * 1j
            self.data2 += numpy.random.rand(self.size) * 1j        
            
        self.delta_t = .5
        self.epoch = swiglal.LIGOTimeGPS(1234567,0)
        
    def test_frame(self):
        # This is a file in the temp directory that will be deleted when it is garbage collected
        frmfile = tempfile.NamedTemporaryFile()
        # We will need access to the actual filename.
        filename = frmfile.name        
        
        # Now we will create a frame file, specifiying that it is a timeseries
        Fr.frputvect(filename,[{'name':'channel1', 'data':self.data1, 'start':int(self.epoch), 'dx':self.delta_t,'type':1},
                                {'name':'channel2', 'data':self.data2, 'start':int(self.epoch), 'dx':self.delta_t,'type':1}])
        
        with self.context:
            if _options['scheme'] == 'cpu':
                # Reading just one channel first
                ts = pycbc.frame.read_frame(filename,'channel1')
                self.checkCurrentState(ts,self.data1,self.places)
                self.assertTrue(ts.end_time-ts.start_time == self.size*self.delta_t)
                
                # Now reading multiple channels
                ts = pycbc.frame.read_frame(filename,['channel1','channel2'])
                self.assertTrue(type(ts) is list)
                self.checkCurrentState(ts[0], self.data1, self.places)
                self.checkCurrentState(ts[1], self.data2, self.places)
                self.assertTrue(ts[0].end_time-ts[0].start_time == self.size*self.delta_t)
                self.assertTrue(ts[1].end_time-ts[1].start_time == self.size*self.delta_t)
                
                # Now reading in a specific segment with an integer
                ts = pycbc.frame.read_frame(filename, 'channel1', start=int(self.epoch+10), 
                                                                    end=int(self.epoch+50))
                self.checkCurrentState(ts, self.data1[int(10/self.delta_t):], self.places)
                self.assertTrue(40 - (ts.end_time-ts.start_time) < self.delta_t)
                self.assertTrue(ts.start_time == self.epoch+10)
                
                # The same, but with a LIGOTimeGPS for the start and end times
                ts = pycbc.frame.read_frame(filename, 'channel1', start=self.epoch+10, 
                                                                    end=self.epoch+50)
                self.checkCurrentState(ts, self.data1[int(10/self.delta_t):], self.places)
                self.assertTrue(40 - (ts.end_time-ts.start_time) < self.delta_t)
                self.assertTrue(ts.start_time == self.epoch+10)
                
                # And now some cases that should raise errors
                
                # There must be a span grater than 0
                self.assertRaises(ValueError, pycbc.frame.read_frame,filename,'channel1',
                                    start=self.epoch,end=self.epoch)
                # The start must be before the end
                self.assertRaises(ValueError, pycbc.frame.read_frame,filename,'channel1',
                                    start=self.epoch+1,end=self.epoch)
                # Non integer times should also raise an error
                badtime = swiglal.LIGOTimeGPS(int(self.epoch)+5,1000)
                
                self.assertRaises(ValueError, pycbc.frame.read_frame,filename,'channel1',
                                    start=self.epoch,end=badtime)
                self.assertRaises(ValueError, pycbc.frame.read_frame,filename,'channel1',
                                    start=float(self.epoch),end=float(badtime))
                
                
                
    def test_cache(self):
        pass
        
        
def frame_test_maker(context,dtype):
    class tests(FrameTestBase,unittest.TestCase):
        def __init__(self,*args):
            self.context=context
            self.dtype=dtype
            if _options['scheme'] == 'cpu':
                self.scheme = type(None)
            elif _options['scheme'] == 'cuda':
                self.scheme = pycbc.scheme.CUDAScheme
            else:
                self.scheme = pycbc.scheme.OpenCLScheme            
            unittest.TestCase.__init__(self,*args)
    tests.__name__ = _options['scheme'] + " " + dtype.__name__
    return tests

types = [numpy.float32, numpy.float64, numpy.complex64, numpy.complex128]

suite = unittest.TestSuite()

scs =[]
if _options['scheme'] == 'cpu':
    scs.append(DefaultScheme())
if _options['scheme'] == 'cuda':
    scs.append(CUDAScheme(device_num=_options['devicenum']))
if _options['scheme'] == 'opencl':
    scs.append(OpenCLScheme(device_num=_options['devicenum']))

ind = 0
for sc in scs:
    for ty in types:
        na = 'test' + str(ind)
        vars()[na] = frame_test_maker(sc,ty)
        suite.addTest(unittest.TestLoader().loadTestsFromTestCase(vars()[na]))
        ind += 1

if __name__ == '__main__':
    results = unittest.TextTestRunner(verbosity=2).run(suite)
        