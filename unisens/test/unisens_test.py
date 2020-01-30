# -*- coding: utf-8 -*-
"""
Created on Sat Jan  4 16:37:07 2020

@author: skjerns
"""
import os
import sys
from unisens.entry import CustomEntry, ValuesEntry, EventEntry, SignalEntry
from unisens.entry import MiscEntry, CustomAttributes
import unisens
import unittest
import shutil
import tempfile


def elements_equal(e1, e2):
    if e1.tag != e2.tag: return False
    if e1.text != e2.text: return False
    if e1.tail != e2.tail: return False
    if e1.attrib != e2.attrib: return False
    if len(e1) != len(e2): return False
    return all(elements_equal(c1, c2) for c1, c2 in zip(e1, e2))


class Testing(unittest.TestCase):
    
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix='unisens')
        
    def tearDown(self):
        shutil.rmtree(self.tmpdir)
    
    def test_unisens_creation(self):
        folder = os.path.join(self.tmpdir, 'data', 'record1')
        
        u = unisens.Unisens(folder)
        u.save()
        self.assertTrue(os.path.isdir(folder))
        self.assertTrue(os.path.isfile(os.path.join(folder, 'unisens.xml')))
        
        u.key1 = 'value1'
        u.set('key2', 'value2')
        u.set('key3', 3)
        
        self.assertTrue(hasattr(u, 'key1'))
        self.assertTrue(hasattr(u, 'key2'))
        self.assertTrue(hasattr(u, 'key3'))
        
        self.assertEqual(u.attrib['key1'], 'value1')
        self.assertEqual(u.attrib['key2'], 'value2')
        self.assertEqual(u.attrib['key3'], '3')
        
        self.assertEqual(u.key1, 'value1')
        self.assertEqual(u.key2, 'value2')
        self.assertEqual(u.key3, '3')
        
        
    def test_unisens_overwrite_load(self):
        folder = os.path.join(self.tmpdir, 'data', 'record2')
        u = unisens.Unisens(folder)
        u.key1 = 'value1'
        u.save()
        u = unisens.Unisens(folder)
        
        self.assertTrue(hasattr(u, 'key1'))
        self.assertEqual(u.key1, 'value1')
        self.assertEqual(u.attrib['key1'], 'value1')
        
        u = unisens.Unisens(folder, makenew=True)
        self.assertFalse(hasattr(u, 'key1'))
        self.assertNotIn('key1', u.attrib)        
        
        
    def test_entry_creation(self):
        folder = os.path.join(self.tmpdir, 'data', 'record2')
        for entrytype in [CustomEntry, ValuesEntry, SignalEntry, EventEntry]:
            
            with self.assertRaises(ValueError):
                entry = entrytype()
            
            entry = entrytype(folder=folder, id='test')
            entry.set('key1', 'value1')
            entry.key2 = 'value2'
            self.assertTrue(hasattr(entry, 'id'))
            self.assertTrue(hasattr(entry, 'key1'))
            self.assertTrue(hasattr(entry, 'key2'))

            self.assertEqual(entry.id, 'test')
            self.assertEqual(entry.key1, 'value1')
            self.assertEqual(entry.key2, 'value2')
            self.assertEqual(entry.attrib['id'], 'test')
            self.assertEqual(entry.attrib['key1'], 'value1')
            self.assertEqual(entry.attrib['key2'], 'value2')
            
            entry.remove_attr('key1')
            self.assertFalse(hasattr(entry, 'key1'))
            self.assertNotIn('key1', entry.attrib)
            
        with self.assertRaises(ValueError):
            misc = MiscEntry()
        with self.assertRaises(ValueError):
            misc = CustomAttributes()
        misc = MiscEntry(name='test')
        self.assertEqual(misc.tag, 'test')
        self.assertEqual(len(misc), 0)
        self.assertEqual(len(misc.attrib), 0)
        misc.set('key1', 'value1')
        self.assertEqual(len(misc), 0)
        self.assertEqual(len(misc.attrib), 1)
        self.assertEqual(misc.key1, 'value1')
        self.assertIn('key1', misc.attrib)
        self.assertEqual(misc.attrib['key1'], 'value1')
        # self.assertEqual(len(misc.attrib), 0)

        with self.assertRaises(ValueError):
            custom = CustomAttributes()
        custom = CustomAttributes('key1', 'value1')
        self.assertEqual(len(custom), 1)
        self.assertEqual(len(custom.attrib), 0)
        self.assertTrue(hasattr(custom, 'key1'))
        self.assertEqual(custom.key1, 'value1')
        for entry in custom:
            self.assertTrue(hasattr(entry, 'key'))
            self.assertTrue(hasattr(entry, 'value'))
            self.assertEqual(entry.key, 'key1')
            self.assertEqual(entry.value, 'value1')
            self.assertEqual(entry.attrib['key'], 'key1')
            self.assertEqual(entry.attrib['value'], 'value1')          
        custom.remove('key1')
        self.assertEqual(len(custom), 0)
        
        
    def test_unisens_add_entr(self):
        folder = os.path.join(self.tmpdir, 'data', 'record')
        u = unisens.Unisens(folder, makenew=True)
        
        for i,entrytype in enumerate([CustomEntry, ValuesEntry,
                                      SignalEntry, EventEntry]):
            entry = entrytype(folder=folder, id='test'+str(i))
            entry.set('key1', 'value1')
            entry.key2 = 'value2'
            u.append(entry)
        with self.assertRaises(ValueError):
            u.append(entry)
        self.assertEqual(len(u), 4)
        self.assertEqual(len(u.entries), 4)
        u.save()
        
        u = unisens.Unisens(folder)
        self.assertEqual(len(u), 4)
        
        u = unisens.Unisens(folder, makenew=True)
        self.assertEqual(len(u), 0)
        
        misc = MiscEntry(name='miscentry')
        misc.set('key2', 'value2')
        customattr = CustomAttributes('key1', 'value1')
        u.append(misc)
        u.append(customattr)
        self.assertEqual(len(u), 2)
        
        
        
    def test_boolean(self):
        a = True
        b = True
        self.assertEqual(a, b)
        
    def test_load_examples(self):
        if False:
            __file__ == 'C:/Users/Simon/Desktop/pyUnisens/unisens/test/unisens_test.py'
        example1 = os.path.join(os.path.dirname(__file__), 'Example_001')
        example2 = os.path.join(os.path.dirname(__file__), 'Example_002')
        example3 = os.path.join(os.path.dirname(__file__), 'Example_003')
        
        u = unisens.Unisens(example1)
        self.assertTrue(hasattr(u, 'entries'))
        self.assertTrue(hasattr(u, 'attrib'))
        for attr in ['version', 'measurementId', 'timestampStart']:
            self.assertIn(attr, u.attrib)
        self.assertEqual(u.attrib['version'], '2.0')
        self.assertEqual(u.attrib['measurementId'], 'Example_001')
        self.assertEqual(u.attrib['timestampStart'], '2008-07-08T13:32:51')
        self.assertEqual(len(u), 9)
        
        entry = u.entries['imp200.bin']
        self.assertEqual(entry.adcResolution, '16')
        self.assertEqual(entry.comment, 'Electrode Impedance')
        self.assertEqual(entry.contentClass, 'IMP')
        self.assertEqual(entry.dataType, 'int16')
        self.assertEqual(entry.id, 'imp200.bin')
        self.assertEqual(entry.lsbValue, '1')
        self.assertEqual(entry.sampleRate, '200')
        self.assertEqual(entry.unit, 'Ohm')
        
        # check if loading and saving will reproduce the same tree
        for example in [example1, example2, example3]:
            u1 = unisens.Unisens(example)
            entry = MiscEntry('test')
            u1.append(entry)
            u1.save(folder = self.tmpdir)
            u2 = unisens.Unisens(self.tmpdir)
            self.assertTrue(elements_equal(u1, u2))
            u2.append(MiscEntry('test2'))
            self.assertFalse(elements_equal(u1, u2))
        
        
        
if __name__ == '__main__':
    unittest.main()














