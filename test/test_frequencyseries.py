# Copyright (C) 2012  Alex Nitz, Andrew Miller
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
These are the unittests for the pycbc frequencyseries type
'''

import pycbc
import unittest
from pycbc.types import *
from pycbc.scheme import *
import numpy
import lal
import base_test
import sys

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

# By importing the current schemes array type, it will make it easier to check the  array types later
if _options['scheme'] == 'cuda':
    import pycuda
    import pycuda.gpuarray
    from pycuda.gpuarray import GPUArray as SchemeArray
elif _options['scheme'] == 'opencl':
    import pyopencl
    import pyopencl.array
    from pyopencl.array import Array as SchemeArray
elif _options['scheme'] == 'cpu':
    from numpy import ndarray as SchemeArray

class TestFrequencySeriesBase(base_test.array_base):

    def checkCurrentState(self, inputs, results, places):
        super(TestFrequencySeriesBase,self).checkCurrentState(inputs, results, places)
        for a in inputs:
            if isinstance(a,pycbc.types.Array):
                self.assertEqual(a.delta_f, self.delta_f)
                self.assertEqual(a._epoch, self.epoch)

    def setUp(self):

        # We need to check for correct creation from all dtypes,
        # and errors from incorrect operations so the other precision of
        # odtype needs to be available as well
        self.other_precision = {numpy.complex64 : numpy.complex128,
                            numpy.complex128 : numpy.complex64,
                            numpy.float32 : numpy.float64,
                            numpy.float64 : numpy.float32}

        # Number of decimal places to compare for single precision
        if self.dtype == numpy.float32 or self.dtype == numpy.complex64:
            self.places = 5
        # Number of decimal places to compare for double precision
        else:
            self.places = 13

        # We will also need to check whether dtype and odtype are real or complex,
        # so that we can test non-zero imaginary parts.
        if self.dtype == numpy.float32 or self.dtype == numpy.float64:
            self.kind = 'real'
        else:
            self.kind = 'complex'
        if self.odtype == numpy.float32 or self.odtype == numpy.float64:
            self.okind = 'real'
        else:
            self.okind = 'complex'

        # Now that the kinds are set, we need to call our parent method to set up all the
        # inputs and answers for our functions
        self.setNumbers()

        # Here our test FrequencySeries are created.
        self.delta_f = 0.1
        self.a1 = FrequencySeries(self.alist, self.delta_f, epoch=self.epoch, dtype=self.dtype)
        self.a2 = FrequencySeries(self.alist, self.delta_f, epoch=self.epoch, dtype=self.dtype)
        self.a3 = FrequencySeries(self.alist, self.delta_f, epoch=self.epoch, dtype=self.dtype)

        self.w = Array(self.wlist, dtype=self.dtype)

        self.b1 = FrequencySeries(self.blist, self.delta_f, epoch=self.epoch, dtype=self.odtype)
        self.b2 = FrequencySeries(self.blist, self.delta_f, epoch=self.epoch, dtype=self.odtype)

        # We will need to also test a non-zero imaginary part scalar.
        self.s = self.scalar

        # Finally, we want to have an array that we shouldn't be able to operate on,
        # because the precision is wrong, and one where the length is wrong.
        self.bad = FrequencySeries([1,1,1], 0.1, epoch=self.epoch, dtype = self.other_precision[self.odtype])
        self.bad2 = FrequencySeries([1,1,1,1], 0.1, epoch=self.epoch, dtype = self.dtype)

        # These are FrequencySeries that have problems specific to FrequencySeries
        self.bad3 = FrequencySeries([1,1,1], 0.2, epoch=self.epoch, dtype = self.dtype)
        # This next one is actually okay for frequencyseries
        if self.epoch == lal.LIGOTimeGPS(0,0):
            self.bad4 = FrequencySeries([1,1,1], 0.1, epoch = lal.LIGOTimeGPS(1000, 1000), dtype = self.dtype)
        else:
            self.bad4 = FrequencySeries([1,1,1], 0.1, epoch=None, dtype = self.dtype)

    def test_numpy_init(self):
        with self.context:
            in1 = numpy.array([5,3,1],dtype=self.odtype)
            in2 = numpy.array([5,3,1],dtype=self.other_precision[self.odtype])

            #We don't want to cast complex as real
            if not (self.kind == 'real' and self.okind == 'complex'):
                #First we must check that the dtype is correct when specified
                out1 = FrequencySeries(in1,0.1, dtype=self.dtype)
                out2 = FrequencySeries(in2,0.1, dtype=self.dtype)
                #to be sure that it is copied
                in1 += 1
                in2 += 1
                self.assertTrue(type(out1._scheme) == self.scheme)
                self.assertTrue(type(out1._data) is SchemeArray)
                self.assertEqual(out1[0],5)
                self.assertEqual(out1[1],3)
                self.assertEqual(out1[2],1)
                self.assertTrue(out1.dtype==self.dtype)
                self.assertEqual(out1.delta_f, 0.1)
                self.assertEqual(out1._epoch, lal.LIGOTimeGPS(0,0))


                self.assertTrue(type(out2._scheme) == self.scheme)
                self.assertTrue(type(out2._data) is SchemeArray)
                self.assertEqual(out2[0],5)
                self.assertEqual(out2[1],3)
                self.assertEqual(out2[2],1)
                self.assertTrue(out2.dtype==self.dtype)
                self.assertEqual(out2.delta_f,0.1)
                self.assertEqual(out2._epoch, lal.LIGOTimeGPS(0,0))

                in1-=1
                in2-=1

            # Also, when it is unspecified
            out3 = FrequencySeries(in1,0.1,epoch=self.epoch)
            in1 += 1
            self.assertTrue(type(out3._scheme) == self.scheme)
            self.assertTrue(type(out3._data) is SchemeArray)
            self.assertEqual(out3[0],5)
            self.assertEqual(out3[1],3)
            self.assertEqual(out3[2],1)
            self.assertTrue(out3.dtype==self.odtype)
            self.assertEqual(out3.delta_f,0.1)
            self.assertEqual(out3._epoch, self.epoch)

            # Check for copy=false
            # On the CPU, this should be possible
            in3 = numpy.array([5,3,1],dtype=self.dtype)
            if _options['scheme'] == 'cpu':
                out4 = FrequencySeries(in3,0.1,copy=False)
                in3 += 1

                self.assertTrue(out4.dtype==self.dtype)
                self.assertTrue(type(out4._scheme) == self.scheme)
                self.assertEqual(out4[0],6)
                self.assertEqual(out4[1],4)
                self.assertEqual(out4[2],2)
                self.assertEqual(out4.delta_f,0.1)
                self.assertEqual(out4._epoch, lal.LIGOTimeGPS(0,0))

            # If we're in different scheme, this should raise an error
            else:
                self.assertRaises(TypeError, FrequencySeries, in3, 0.1, copy=False)

            # We also need to check initialization using GPU arrays
            if _options['scheme'] == 'cuda':
                in4 = pycuda.gpuarray.zeros(3,self.dtype)
            elif _options['scheme'] == 'opencl':
                in4 = pyopencl.array.zeros(pycbc.scheme.mgr.state.queue,3, self.dtype)
            if _options['scheme'] != 'cpu':
                out4 = FrequencySeries(in4,0.1, copy=False)
                in4 += 1
                self.assertTrue(type(out4._scheme) == self.scheme)
                self.assertTrue(type(out4._data) is SchemeArray)
                self.assertEqual(out4[0],1)
                self.assertEqual(out4[1],1)
                self.assertEqual(out4[2],1)
                self.assertTrue(out4.dtype==self.dtype)
                self.assertEqual(out4.delta_f,0.1)
                self.assertEqual(out4._epoch, lal.LIGOTimeGPS(0,0))

            # We should be able to create an array from the wrong dtype, and
            # it should be cast as float64
            in5 = numpy.array([1,2,3],dtype=numpy.int32)
            out5 = FrequencySeries(in5,0.1)
            in5 += 1
            self.assertTrue(type(out5._scheme) == self.scheme)
            self.assertTrue(type(out5._data) is SchemeArray)
            self.assertEqual(out5[0],1)
            self.assertEqual(out5[1],2)
            self.assertEqual(out5[2],3)
            self.assertTrue(out5.dtype==numpy.float64)
            self.assertEqual(out5.delta_f,0.1)
            self.assertEqual(out5._epoch, lal.LIGOTimeGPS(0,0))

            # We shouldn't be able to copy it though
            self.assertRaises(TypeError,FrequencySeries,in5, 0.1, copy=False)

            # Finally, just checking a few things specific to FrequencySeries
            inbad = numpy.array([],dtype=float64)
            self.assertRaises(ValueError, FrequencySeries, in1, -1)
            self.assertRaises(ValueError, FrequencySeries, inbad, .1)
            self.assertRaises(TypeError, FrequencySeries, in1, .1, epoch=5)

        if _options['scheme'] != 'cpu':
            self.assertRaises(TypeError, FrequencySeries, in4, 0.1, copy=False)
        self.assertRaises(TypeError, FrequencySeries, in5,0.1, copy=False)


    def test_array_init(self):
        # this array is made outside the context so we can check that an error is raised when copy = false in a GPU scheme
        cpuarray = Array([1,2,3])
        with self.context:
            in1 = Array([5,3,1],dtype=self.odtype)
            in2 = Array([5,3,1],dtype=self.other_precision[self.odtype])
            self.assertTrue(type(in1._scheme) == self.scheme)
            self.assertTrue(type(in1._data) is SchemeArray)
            self.assertTrue(type(in2._scheme) == self.scheme)
            self.assertTrue(type(in2._data) is SchemeArray)
            # We don't want to cast complex as real
            if not (self.kind=='real' and self.okind == 'complex'):
                # First we must check that the dtype is correct when specified
                out1 = FrequencySeries(in1, 0.1, epoch=None, dtype=self.dtype)
                out2 = FrequencySeries(in2, 0.1, epoch=None, dtype=self.dtype)
                # to be sure that it is copied
                in1 += 1
                in2 += 1

                self.assertTrue(type(out1._scheme) == self.scheme)
                self.assertTrue(type(out1._data) is SchemeArray)
                self.assertEqual(out1[0],5)
                self.assertEqual(out1[1],3)
                self.assertEqual(out1[2],1)
                self.assertTrue(out1.dtype==self.dtype)
                self.assertEqual(out1.delta_f, 0.1)
                self.assertEqual(out1._epoch, lal.LIGOTimeGPS(0,0))

                if out1.dtype == numpy.float32:
                    self.assertTrue(out1.precision == 'single')
                    #self.assertTrue(out1.kind == 'real')
                if out1.dtype == numpy.float64:
                    self.assertTrue(out1.precision == 'double')
                    #self.assertTrue(out1.kind == 'real')
                if out1.dtype == numpy.complex64:
                    self.assertTrue(out1.precision == 'single')
                    #self.assertTrue(out1.kind == 'complex')
                if out1.dtype == numpy.complex128:
                    self.assertTrue(out1.precision == 'double')
                    #self.assertTrue(out1.kind == 'complex')

                self.assertTrue(type(out2._scheme) == self.scheme)
                self.assertTrue(type(out2._data) is SchemeArray)
                self.assertEqual(out2[0],5)
                self.assertEqual(out2[1],3)
                self.assertEqual(out2[2],1)
                self.assertTrue(out2.dtype==self.dtype)
                self.assertEqual(out2.delta_f, 0.1)
                self.assertEqual(out2._epoch, lal.LIGOTimeGPS(0,0))

                in1-=1
                in2-=1
            # Giving complex input and specifying a real dtype should raise an error
            else:
                self.assertRaises(TypeError, FrequencySeries, in1,0.1, dtype = self.dtype)
                self.assertRaises(TypeError, FrequencySeries, in2,0.1, dtype = self.dtype)

            # Also, when it is unspecified
            out3 = FrequencySeries(in1,0.1,epoch=self.epoch)
            in1 += 1

            self.assertTrue(type(out3._scheme) == self.scheme)
            self.assertTrue(type(out3._data) is SchemeArray)
            self.assertEqual(out3[0],5)
            self.assertEqual(out3[1],3)
            self.assertEqual(out3[2],1)
            self.assertTrue(out3.dtype==self.odtype)
            self.assertEqual(out3.delta_f, 0.1)
            self.assertEqual(out3._epoch, self.epoch)

            # We should also be able to create from a CPU Array
            out4 = FrequencySeries(cpuarray,0.1, dtype=self.dtype)

            self.assertTrue(type(out4._scheme) == self.scheme)
            self.assertTrue(type(out4._data) is SchemeArray)
            self.assertEqual(out4[0],1)
            self.assertEqual(out4[1],2)
            self.assertEqual(out4[2],3)
            self.assertTrue(out4.dtype==self.dtype)
            self.assertEqual(out4.delta_f, 0.1)
            self.assertEqual(out4._epoch, lal.LIGOTimeGPS(0,0))

            self.assertRaises(TypeError, FrequencySeries,in1,0.1, dtype=numpy.int32)

            # Check for copy=false
            in3 = Array([5,3,1],dtype=self.dtype)
            out5 = FrequencySeries(in3,0.1,copy=False)
            in3 += 1

            self.assertTrue(type(out5._scheme) == self.scheme)
            self.assertTrue(type(out5._data) is SchemeArray)
            self.assertEqual(out5[0],6)
            self.assertEqual(out5[1],4)
            self.assertEqual(out5[2],2)
            self.assertTrue(out5.dtype==self.dtype)
            self.assertEqual(out5.delta_f, 0.1)
            self.assertEqual(out5._epoch, lal.LIGOTimeGPS(0,0))

            if _options['scheme'] != 'cpu':
                self.assertRaises(TypeError,FrequencySeries,0.1,cpuarray,copy=False)
            # Things specific to FrequencySeries
            inbad = Array(numpy.array([],dtype=float64))
            self.assertRaises(ValueError, FrequencySeries, in1, -1)
            self.assertRaises(ValueError, FrequencySeries, inbad, .1)
            self.assertRaises(TypeError, FrequencySeries, in1, .1, epoch=5)

        # Also checking that a cpu array can't be made out of another scheme without copying
        if _options['scheme'] != 'cpu':
            self.assertRaises(TypeError, FrequencySeries, out4, 0.1, copy=False)
            out6 = FrequencySeries(out4, 0.1, dtype=self.dtype)
            self.assertTrue(type(out6._scheme) == type(None))
            self.assertTrue(type(out6._data) is numpy.ndarray)
            self.assertEqual(out6[0],1)
            self.assertEqual(out6[1],2)
            self.assertEqual(out6[2],3)
            self.assertTrue(out6.dtype==self.dtype)
            self.assertEqual(out6.delta_f, 0.1)
            self.assertEqual(out6._epoch, lal.LIGOTimeGPS(0,0))

    def test_list_init(self):
        with self.context:
            # When specified
            out1 = FrequencySeries([5,3,1],0.1, dtype=self.dtype)

            self.assertTrue(type(out1._scheme) == self.scheme)
            self.assertTrue(type(out1._data) is SchemeArray)
            self.assertEqual(out1[0],5)
            self.assertEqual(out1[1],3)
            self.assertEqual(out1[2],1)
            self.assertTrue(out1.dtype==self.dtype)
            self.assertEqual(out1.delta_f, 0.1)
            self.assertEqual(out1._epoch, lal.LIGOTimeGPS(0,0))

            if out1.dtype == numpy.float32:
                self.assertTrue(out1.precision == 'single')
                #self.assertTrue(out1.kind == 'real')
            if out1.dtype == numpy.float64:
                self.assertTrue(out1.precision == 'double')
                #self.assertTrue(out1.kind == 'real')
            if out1.dtype == numpy.complex64:
                self.assertTrue(out1.precision == 'single')
                #self.assertTrue(out1.kind == 'complex')
            if out1.dtype == numpy.complex128:
                self.assertTrue(out1.precision == 'double')
                #self.assertTrue(out1.kind == 'complex')

            if self.kind == 'complex':
                out2 = FrequencySeries([5+0j,3+0j,1+0j], 0.1, dtype=self.dtype)

                self.assertTrue(type(out2._scheme) == self.scheme)
                self.assertTrue(type(out2._data) is SchemeArray)
                self.assertEqual(out2[0],5)
                self.assertEqual(out2[1],3)
                self.assertEqual(out2[2],1)
                self.assertTrue(out2.dtype==self.dtype)
                self.assertEqual(out2.delta_f, 0.1)
                self.assertEqual(out2._epoch, lal.LIGOTimeGPS(0,0))

            else:
                self.assertRaises(TypeError, FrequencySeries,[5+0j, 3+0j, 1+0j], 0.1, dtype=self.dtype)
            self.assertRaises(TypeError, FrequencySeries,[1,2,3],0.1, dtype=numpy.int32)

            #Also, when it is unspecified
            out3 = FrequencySeries([5,3,1],0.1,epoch=self.epoch)

            self.assertTrue(type(out3._scheme) == self.scheme)
            self.assertTrue(type(out3._data) is SchemeArray)
            self.assertEqual(out3[0],5)
            self.assertEqual(out3[1],3)
            self.assertEqual(out3[2],1)
            self.assertTrue(out3.dtype==numpy.float64)
            self.assertEqual(out3.delta_f, 0.1)
            self.assertEqual(out3._epoch, self.epoch)

            out4 = FrequencySeries([5+0j,3+0j,1+0j],0.1,epoch = self.epoch)

            self.assertTrue(type(out4._scheme) == self.scheme)
            self.assertTrue(type(out4._data) is SchemeArray)
            self.assertEqual(out4[0],5)
            self.assertEqual(out4[1],3)
            self.assertEqual(out4[2],1)
            self.assertTrue(out4.dtype==numpy.complex128)
            self.assertEqual(out4.delta_f, 0.1)
            self.assertEqual(out4._epoch, self.epoch)

            self.assertRaises(TypeError,FrequencySeries,[1,2,3],copy=False)

            # Things specific to FrequencySeries
            self.assertRaises(ValueError, FrequencySeries, [1,2,3], -1)
            self.assertRaises(ValueError, FrequencySeries, [], .1)
            self.assertRaises(TypeError, FrequencySeries, [1,2,3], .1, epoch=5)

    def test_mul(self):
        super(TestFrequencySeriesBase,self).test_mul()
        self.assertRaises(ValueError, self.a1.__mul__,self.bad3)
        c = self.a1 * self.bad4
        self.assertTrue(c._epoch==self.epoch)

    def test_rmul(self):
        super(TestFrequencySeriesBase,self).test_rmul()
        self.assertRaises(ValueError, self.a1.__rmul__,self.bad3)
        c = self.a1.__rmul__(self.bad4)
        self.assertTrue(c._epoch==self.epoch)

    def test_imul(self):
        super(TestFrequencySeriesBase,self).test_imul()
        self.assertRaises(ValueError, self.a1.__imul__,self.bad3)
        self.a1 *= self.bad4
        self.assertTrue(self.a1._epoch==self.epoch)

    def test_add(self):
        super(TestFrequencySeriesBase,self).test_add()
        self.assertRaises(ValueError, self.a1.__add__,self.bad3)
        c = self.a1 + self.bad4
        self.assertTrue(c._epoch==self.epoch)

    def test_radd(self):
        super(TestFrequencySeriesBase,self).test_radd()
        self.assertRaises(ValueError, self.a1.__radd__,self.bad3)
        c = self.a1.__radd__(self.bad4)
        self.assertTrue(c._epoch==self.epoch)

    def test_iadd(self):
        super(TestFrequencySeriesBase,self).test_iadd()
        self.assertRaises(ValueError, self.a1.__iadd__,self.bad3)
        self.a1 += self.bad4
        self.assertTrue(self.a1._epoch==self.epoch)

    def test_sub(self):
        super(TestFrequencySeriesBase,self).test_sub()
        self.assertRaises(ValueError, self.a1.__sub__,self.bad3)
        c = self.a1 - self.bad4
        self.assertTrue(c._epoch==self.epoch)

    def test_rsub(self):
        super(TestFrequencySeriesBase,self).test_rsub()
        self.assertRaises(ValueError, self.a1.__rsub__,self.bad3)
        c = self.a1.__rsub__(self.bad4)
        self.assertTrue(c._epoch==self.epoch)

    def test_isub(self):
        super(TestFrequencySeriesBase,self).test_isub()
        self.assertRaises(ValueError, self.a1.__isub__,self.bad3)
        self.a1 -= self.bad4
        self.assertTrue(self.a1._epoch==self.epoch)

    def test_div(self):
        super(TestFrequencySeriesBase,self).test_div()
        self.assertRaises(ValueError, self.a1.__div__,self.bad3)
        c = self.a1 / self.bad4
        self.assertTrue(c._epoch==self.epoch)

    def test_rdiv(self):
        super(TestFrequencySeriesBase,self).test_rdiv()
        self.assertRaises(ValueError, self.a1.__rdiv__,self.bad3)
        c = self.a1.__rdiv__(self.bad4)
        self.assertTrue(c._epoch==self.epoch)

    def test_idiv(self):
        super(TestFrequencySeriesBase,self).test_idiv()
        self.assertRaises(ValueError, self.a1.__idiv__,self.bad3)
        self.a1 /= self.bad4
        self.assertTrue(self.a1._epoch==self.epoch)

    def test_dot(self):
        super(TestFrequencySeriesBase,self).test_dot()
        self.assertRaises(ValueError, self.a1.dot,self.bad3)
        self.a1.dot(self.bad4)
        self.assertTrue(self.a1._epoch==self.epoch)

    def test_sample_frequencies(self):
        with self.context:
            # Moving these to the current scheme
            self.a1*=1
            self.b1*=1
            self.bad3*=1
            self.assertEqual(len(self.a1.sample_frequencies), 3)
            self.assertAlmostEqual(self.a1.sample_frequencies[-1] - self.a1.sample_frequencies[0], 0.2)
            self.assertEqual(len(self.b1.sample_frequencies), 3)
            self.assertAlmostEqual(self.b1.sample_frequencies[-1] - self.b1.sample_frequencies[0], 0.2)
            self.assertEqual(len(self.bad3.sample_frequencies), 3)
            self.assertAlmostEqual(self.bad3.sample_frequencies[-1] - self.bad3.sample_frequencies[0], 0.4)

def test_maker(context, dtype, odtype, epoch):
    class TestFrequencySeries(TestFrequencySeriesBase, unittest.TestCase):
        def __init__(self, *args):
            self.context = context
            self.dtype = dtype
            self.odtype = odtype
            if _options['scheme'] == 'cpu':
                self.scheme = type(None)
            elif _options['scheme'] == 'cuda':
                self.scheme = pycbc.scheme.CUDAScheme
            else:
                self.scheme = pycbc.scheme.OpenCLScheme
            if epoch is None:
                self.epoch = lal.LIGOTimeGPS(0,0)
            else:
                self.epoch = epoch
            unittest.TestCase.__init__(self, *args)
    TestFrequencySeries.__name__ = _options['scheme'] + " " + dtype.__name__ + " with " + odtype.__name__
    return TestFrequencySeries

types = [ (float32,[float32,complex64]), (float64,[float64,complex128]),
        (complex64,[complex64,float32]), (complex128,[float64,complex128]) ]

suite = unittest.TestSuite()

# Unlike the regular array tests, we will need to test with an epoch, and with none
epochs = [lal.LIGOTimeGPS(1000, 1000),None]

schemes = []

if _options['scheme'] == 'cpu':
    schemes.append(DefaultScheme())
if _options['scheme'] == 'cuda':
    schemes.append(CUDAScheme(device_num=_options['devicenum']))
if _options['scheme'] == 'opencl':
    schemes.append(OpenCLScheme(device_num=_options['devicenum']))

i = 0
for s in schemes:
    for t,otypes in types:
        for ot in otypes:
            for epoch in epochs:
                na = 'test' + str(i)
                vars()[na] = test_maker(s, t, ot, epoch)
                suite.addTest(unittest.TestLoader().loadTestsFromTestCase(vars()[na]))
                i += 1

if __name__ == '__main__':
    results = unittest.TextTestRunner(verbosity=2).run(suite)

    NotImpErrors = 0
    for error in results.errors:
        for errormsg in error:
            if type(errormsg) is str:
                if 'NotImplemented' in errormsg:
                    NotImpErrors +=1
                    break
    if results.wasSuccessful():
        sys.exit(0)
    elif len(results.failures)==0 and len(results.errors)==NotImpErrors:
        sys.exit(1)
    else:
        sys.exit(2)
