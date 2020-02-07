# -*- coding: utf-8 -*-
"""
Created on Sat Jan  4 16:37:07 2020

@author: skjerns
"""
import os
import sys; sys.path.append('..')
from entry import CustomEntry, ValuesEntry, EventEntry, SignalEntry
from entry import MiscEntry, CustomAttributes
import unisens
import unittest
import shutil
import tempfile




def elements_equal(e1, e2):
    if e1.tag != e2.tag: 
        print(f'tag not same {e1.tag}!={e2.tag}')
        return False
    if e1.text != e2.text: 
        print(f'text not same {e1.text}!={e2.text}')
        return False
    if e1.tail != e2.tail: 
        print(f'tail not same {e1.tail}!={e2.tail}')
        return False
    if e1.attrib != e2.attrib: 
        print(f'attrib not same {e1.attrib}!={e2.attrib}')
        return False
    if len(e1) != len(e2): 
        print(f'length not same {len(e1)}!={len(e2)}, {e1}, {e2}')
        return False
    return all([elements_equal(c1, c2) for c1, c2 in zip(e1, e2)])


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
        u.set_attr('key2', 'value2')
        u.set_attr('key3', 3)
        
        for i in range(2): # run it once, then save and reload and run again
            self.assertTrue(hasattr(u, 'key1'))
            self.assertTrue(hasattr(u, 'key2'))
            self.assertTrue(hasattr(u, 'key3'))
            
            self.assertEqual(u.attrib['key1'], 'value1')
            self.assertEqual(u.attrib['key2'], 'value2')
            self.assertEqual(u.attrib['key3'], '3')
            
            self.assertEqual(u.key1, 'value1')
            self.assertEqual(u.key2, 'value2')
            self.assertEqual(u.key3, '3')
            
            u.save()
    
        
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
            entry.set_attr('key1', 'value1')
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
            
        with self.assertRaises(TypeError):
            misc = MiscEntry()

            
        misc = MiscEntry(name='test')
        self.assertEqual(misc._name, 'test')
        self.assertEqual(len(misc.attrib), 0)
        misc.set_attr('key1', 'value1')
        self.assertEqual(len(misc.attrib), 1)
        self.assertEqual(misc.key1, 'value1')
        self.assertIn('key1', misc.attrib)
        self.assertEqual(misc.attrib['key1'], 'value1')
        self.assertEqual(len(misc.attrib), 1)
        self.assertEqual(len(misc), 0)

        # with self.assertRaises(TypeError):
        #     custom = CustomAttributes()
            
        custom = CustomAttributes(key = 'key1', value = 'value1')
        self.assertEqual(len(custom), 0)
        self.assertEqual(len(custom.attrib), 1)
        self.assertTrue(hasattr(custom, 'key1'))
        self.assertEqual(custom.key1, 'value1')
        custom.remove_attr('key1')
        self.assertEqual(len(custom.attrib), 0)
        custom = CustomAttributes(key = 'key1', value = 'value1')
        custom.set_attr('key2', 'value2')
        custom.set_attr('key1', 'value2')
        self.assertTrue(hasattr(custom, 'key1'))
        self.assertTrue(hasattr(custom, 'key2'))
        self.assertEqual(len(custom.attrib), 2)
        self.assertEqual(custom.key1, 'value2')
        self.assertEqual(custom.key2, 'value2')

        
    def test_unisens_add_entr(self):
        folder = os.path.join(self.tmpdir, 'data', 'record')
        u = unisens.Unisens(folder, makenew=True)
        
        for i,entrytype in enumerate([CustomEntry, ValuesEntry,
                                      SignalEntry, EventEntry]):
            entry = entrytype(folder=folder, id='test'+str(i))
            entry.set_attr('key1', 'value1')
            entry.key2 = 'value2'
            u.add_entry(entry)

        self.assertEqual(len(u), 4)
        self.assertEqual(len(u.entries), 4)
        u.save()
        
        u = unisens.Unisens(folder)
        self.assertEqual(len(u), 4)
        
        u = unisens.Unisens(folder, makenew=True)
        self.assertEqual(len(u), 0)
        
        misc = MiscEntry(name='miscentry')
        misc.set_attr('key2', 'value2')
        customattr = CustomAttributes('key1', 'value1')
        u.add_entry(misc)
        u.add_entry(customattr)
        self.assertEqual(len(u), 2)
        
        
    def test_load_examples(self):
        if False:
            __file__ == 'C:/Users/Simon/Desktop/pyUnisens/unisens/test/unisens_test.py'
        example1 = os.path.join(os.path.dirname(__file__), 'Example_001')
        
        u = unisens.Unisens(example1)
        self.assertTrue(hasattr(u, 'entries'))
        self.assertTrue(hasattr(u, 'attrib'))
        for attr in ['version', 'measurementId', 'timestampStart']:
            self.assertIn(attr, u.attrib)
        self.assertEqual(u.attrib['version'], '2.0')
        self.assertEqual(u.attrib['measurementId'], 'Example_001')
        self.assertEqual(u.attrib['timestampStart'], '2008-07-08T13:32:51')
        self.assertEqual(len(u), 9)
        
        for name in ['customAttributes', 'imp200.bin', 'ecg200.bin', 
                      'valid_signal.csv', 'trig_ref.csv', 'bp.csv',
                      'trig_test_osea_dry.csv', 'picture.jpg', 'default_ecg']:
            self.assertIn(name, u.entries)
        
        entry = u.entries['customAttributes']
        self.assertEqual(entry.weight, '73kg')
        self.assertEqual(entry.height, '1.74m')
        self.assertEqual(entry.gender, 'male')
        
        entry = u.entries['imp200.bin']
        self.assertEqual(entry.adcResolution, '16')
        self.assertEqual(entry.comment, 'Electrode Impedance')
        self.assertEqual(entry.contentClass, 'IMP')
        self.assertEqual(entry.dataType, 'int16')
        self.assertEqual(entry.id, 'imp200.bin')
        self.assertEqual(entry.lsbValue, '1')
        self.assertEqual(entry.sampleRate, '200')
        self.assertEqual(entry.unit, 'Ohm')
        self.assertEqual(entry.binFileFormat.endianess, 'LITTLE')
        self.assertEqual(entry.channel[0].name, 'imp_left') 
        self.assertEqual(entry.channel[1].name, 'imp_right') 
        self.assertEqual(len(entry.channel), 2)

        
        entry = u.entries['ecg200.bin']
        self.assertEqual(entry.adcResolution, '16')
        self.assertEqual(entry.comment, 'Filtered ECG Data 200Hz, Bandpass 3rd order Butterworth 0.5-35')
        self.assertEqual(entry.contentClass, 'ECG')
        self.assertEqual(entry.dataType, 'int16')
        self.assertEqual(entry.id, 'ecg200.bin')
        self.assertEqual(entry.lsbValue, '2.543E-6')
        self.assertEqual(entry.sampleRate, '200')
        self.assertEqual(entry.unit, 'V')
        self.assertEqual(entry.binFileFormat.endianess, 'LITTLE')
        self.assertEqual(entry.channel[0].name, 'dry electrodes') 
        self.assertEqual(entry.channel[1].name, 'ref1') 
        self.assertEqual(len(entry.channel), 3)
        
        entry = u.entries['valid_signal.csv']
        self.assertEqual(entry.id, 'valid_signal.csv')
        self.assertEqual(entry.comment, 'Valid signal regions for evaluation')
        self.assertEqual(entry.sampleRate, '1')
        self.assertEqual(entry.typeLength, '1')
        self.assertEqual(entry.csvFileFormat.decimalSeparator, '.') 
        self.assertEqual(entry.csvFileFormat.separator, ';') 
        self.assertEqual(len(entry), 1)

        entry = u.entries['trig_ref.csv']
        self.assertEqual(entry.id, 'trig_ref.csv')
        self.assertEqual(entry.comment, 'reference qrs trigger list, 200Hz, done with Padys')
        self.assertEqual(entry.sampleRate, '200')
        self.assertEqual(entry.typeLength, '1')
        self.assertEqual(entry.source, 'Padsy')
        self.assertEqual(entry.contentClass, 'TRIGGER')
        self.assertEqual(entry.csvFileFormat.decimalSeparator, '.') 
        self.assertEqual(entry.csvFileFormat.separator, ';') 
        self.assertEqual(len(entry), 1)

        entry = u.entries['trig_test_osea_dry.csv']
        self.assertEqual(entry.id, 'trig_test_osea_dry.csv')
        self.assertEqual(entry.comment, 'test qrs trigger list, 200Hz, done with osea on dry electrodes (ecg200.bin:dry electrodes)')
        self.assertEqual(entry.sampleRate, '200')
        self.assertEqual(entry.typeLength, '1')
        self.assertEqual(entry.source, 'osea')
        self.assertEqual(entry.contentClass, 'TRIGGER')
        self.assertEqual(entry.csvFileFormat.decimalSeparator, '.') 
        self.assertEqual(entry.csvFileFormat.separator, ';')    
        self.assertEqual(len(entry), 1)

        entry = u.entries['bp.csv']
        self.assertEqual(entry.id, 'bp.csv')
        self.assertEqual(entry.comment, 'Bloodpressure cuff left upper arm')
        self.assertEqual(entry.sampleRate, '1')
        self.assertEqual(entry.dataType, 'double')
        self.assertEqual(entry.unit, 'mmHg')
        self.assertEqual(entry.contentClass, 'RR')
        self.assertEqual(entry.csvFileFormat.decimalSeparator, '.') 
        self.assertEqual(entry.csvFileFormat.separator, ';')    
        self.assertEqual(entry.channel[0].name, 'systolisch') 
        self.assertEqual(entry.channel[1].name, 'diastolisch') 
        self.assertEqual(len(entry), 3)
        self.assertEqual(len(entry.channel), 2)

        entry = u.entries['picture.jpg']
        self.assertEqual(entry.id, 'picture.jpg')
        self.assertEqual(entry.type, 'picture')
        self.assertEqual(entry.customFileFormat.fileFormatName, 'custom')

        entry = u.entries['default_ecg']
        self.assertEqual(entry.id, 'default_ecg')
        self.assertEqual(entry.comment, 'ECG and reference trigger')
        self.assertEqual(entry.groupEntry[0].ref, 'trig_ref.csv')
        self.assertEqual(entry.groupEntry[1].ref, 'ecg200.bin')
        self.assertEqual(len(entry.groupEntry), 2)
        self.assertEqual(len(entry), 2)

        
        # check if loading and saving will reproduce the same tree
    def test_load_and_save(self):
        example1 = os.path.join(os.path.dirname(__file__), 'Example_001')
        example2 = os.path.join(os.path.dirname(__file__), 'Example_002')
        example3 = os.path.join(os.path.dirname(__file__), 'Example_003')
        
        for example in [example1, example2, example3]:
            u1 = unisens.Unisens(example)
            entry = MiscEntry('test')
            u1.add_entry(entry)
            u1.save(folder = self.tmpdir)
            u2 = unisens.Unisens(self.tmpdir)
            self.assertTrue(elements_equal(u1.to_element(), u2.to_element()))
            u2.add_entry(MiscEntry('test2'))
            self.assertFalse(elements_equal(u1.to_element(), u2.to_element()))
        

    def test_load_data(self):
        example1 = os.path.join(os.path.dirname(__file__), 'Example_001')
        u = unisens.Unisens(example1)
        signal = u['imp200.bin']
        data = signal.get_data()       
        self.assertEqual(len(data),2)
        self.assertEqual(data.size, 1817200)
        self.assertEqual(data.min(), 1)
        self.assertEqual(data.max(), 32767)
        data = signal.get_data(scaled=False)       
        self.assertEqual(len(data),2)
        self.assertEqual(data.size, 1817200)
        self.assertEqual(data.min(), 1)
        self.assertEqual(data.max(), 32767)
        
        signal = u['ecg200.bin']
        data = signal.get_data()       
        self.assertEqual(len(data), 3)
        self.assertEqual(data.size, 2725800)
        self.assertEqual(data.min(), -0.083329024)
        self.assertEqual(data.max(), 0.08332648100000001)
        data = signal.get_data(scaled=False)       
        self.assertEqual(data.size, 2725800)
        self.assertEqual(data.min(), -32768)
        self.assertEqual(data.max(), 32767)
        
        events = u['valid_signal.csv']
        data = events.get_data(mode='list')       
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0], [10, '('])
        self.assertEqual(data[1], [4521, ')'])
        
        data = events.get_data(mode='numpy')       
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0][0], '10')
        self.assertEqual(data[1][0], '4521')
        
        data = events.get_data(mode='pd')       
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0][0], 10)
        self.assertEqual(data[0][1], 4521)
        
if __name__ == '__main__':
    unittest.main()
    














