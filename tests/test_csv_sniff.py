"""
Tests for the CSV file sniffer
"""
# Author: Ilan Schnell <ischnell@enthought.com>
# Copyright (c) 2008, Ilan Schnell, Enthought, Inc.
# License: BSD Style.
import glob
import os
import os.path
import unittest
from test.test_support import TESTFN, TestFailed

from numpy import array, ndarray

from enthought.mayavi.tools.wizards.csv_sniff import \
     Sniff, loadtxt, loadtxt_unknown, array2dict


CSV_PATH = os.path.join(os.path.dirname(__file__), 'csv_files')


class Util(object):

    def assertNamedClose(self, x, y):
        self.assertEqual(x.shape, y.shape)
        self.assertEqual(x.dtype.names, y.dtype.names)
        for name in x.dtype.names:
            self.assertAllClose(x[name], y[name])

    def assertAllClose(self, x, y):
        self.assertEqual(len(x), len(y))
        for a, b in zip(x, y):
            self.assertClose(a, b)

    def assertClose(self, a, b):
        if isinstance(a, (int, float)):
            if repr(a) == 'nan':
                self.assert_(repr(b) == 'nan')
            else:
                self.assert_(abs(a - b) < 1e-6 * max(1, abs(a)),
                             '%r != %r  %r' % (a, b, abs(a - b)))
                
        elif isinstance(a, str):
            self.assertEqual(a, b)

        else:
            raise TestFailed("Hmm, did not expect: %r" % a)


class Test(unittest.TestCase, Util):

    def test_methods(self):
        fo = open(TESTFN, 'wb')
        fo.write(''' "A", "B", "C"
                     1, 2, 3.2
                     7, 4, 1.87''')
        fo.close()
        
        s = Sniff(TESTFN)
        self.assertEqual(s.comments(), '#')
        self.assertEqual(s.delimiter(), ',')
        self.assertEqual(s.skiprows(), 1)
        self.assertEqual(s.dtype(), {'names': ('A', 'B', 'C'),
                                     'formats': (float, float, float)})
        x = s.loadtxt()
        y = array([(1.0, 2.0, 3.20),
                   (7.0, 4.0, 1.87)], 
                  dtype=[('A', float), ('B', float), ('C', float)])
        self.assertNamedClose(x, y)

        y = loadtxt(TESTFN, **s.kwds())
        self.assertNamedClose(x, y)
        
        d = array2dict(loadtxt_unknown(TESTFN))
        self.assertEqual(type(d), type({}))
        self.assertAllClose(x['A'], [1, 7])
        self.assertAllClose(x['B'], [2, 4])
        self.assertAllClose(x['C'], [3.2, 1.87])


    def test_comment(self):
        fo = open(TESTFN, 'wb')
        fo.write('''
        % "A"  "B"  "C"
           1    2   4.2   % comment''')
        fo.close()
        
        s = Sniff(TESTFN)
        self.assertEqual(s.kwds(),
          {'dtype': {'names': ('A', 'B', 'C'),
                     'formats': (float, float, float)},
           'delimiter': None,
           'skiprows': 0,   # FIXME
           'comments': '%'})

        
    def test_tabs(self):
        fo = open(TESTFN, 'wb')
        fo.write('''54\t87\n21\t32''')
        fo.close()
        
        s = Sniff(TESTFN)
        self.assertEqual(s.delimiter(), None)
        self.assertEqual(s.skiprows(), 0)


    def test_nohead(self):
        fo = open(TESTFN, 'wb')
        fo.write('''Hello;54;87\nWorld;42;86.5''')
        fo.close()
        
        s = Sniff(TESTFN)
        self.assertEqual(s.kwds(),
          {'comments': '#',
           'delimiter': ';',
           'skiprows': 0,
           'dtype': {'names': ('Column 1', 'Column 2', 'Column 3'),
                     'formats': ('S5', float, float)}})

        
    def test_empty_file(self):
        fo = open(TESTFN, 'wb')
        fo.write('')
        fo.close()
        
        self.assertRaises(IndexError, Sniff, TESTFN)


    def tearDown(self):
        os.unlink(TESTFN)


class Test_csv_py_files(unittest.TestCase, Util):
    """
        These tests require files in csv_files/
    """
    def test_csv_files(self):
        """
            Check if the output array from csv_files/<name>.csv
            (which is of unkown format)
            is the same as the array in csv_files/<name>.py
        """
        count = 0
        for csv_file in glob.glob(os.path.join(CSV_PATH, '*.csv')):
            count += 1
            #print 'Running:', csv_file
            s = Sniff(csv_file)
            
            py_file = csv_file[:-4] + '.py'
            
            nan = float('nan') # must be in namespace for some .py files
            d = eval(open(py_file).read())
            
            self.assertEqual(d['kwds'], s.kwds())
            self.assertNamedClose(d['array'], s.loadtxt())

        self.assert_(count > 10)


if __name__ == '__main__':
    unittest.main()
