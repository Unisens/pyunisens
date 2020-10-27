# -*- coding: utf-8 -*-
"""
Created on Sat Jan  4 16:37:07 2020

@author: skjerns
"""
import os
from unisens import CustomEntry, ValuesEntry, EventEntry, SignalEntry
from unisens import MiscEntry, CustomAttributes, Unisens, FileEntry
from unisens import CsvFileEntry

import unittest
import shutil
import tempfile
import numpy as np
import pickle



def elements_equal(e1, e2):
    assert e1.tag == e2.tag, f'tag not same {e1.tag}!={e2.tag}'
    assert e1.text == e2.text, f'text not same {e1.text}!={e2.text}'
    assert e1.tail == e2.tail, f'tail not same {e1.tail}!={e2.tail}'
    assert e1.attrib == e2.attrib, f'attrib not same {e1.attrib}!={e2.attrib}'
    assert len(e1) == len(e2), f'length not same {len(e1)}!={len(e2)}, {e1}, {e2}'
    return all([elements_equal(c1, c2) for c1, c2 in zip(e1, e2)])


class Testing(unittest.TestCase):
    
    
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix='unisens')
        
    def tearDown(self):
        shutil.rmtree(self.tmpdir)
    
    def test_unisens_creation(self):
        folder = os.path.join(self.tmpdir, 'data', 'record1')
        
        u = Unisens(folder)
        u.save()
        self.assertTrue(os.path.isdir(folder))
        self.assertTrue(os.path.isfile(os.path.join(folder, 'unisens.xml')))
        
        u.key1 = 'value1'
        u.set_attrib('key2', 'value2')
        u.set_attrib('key3', 3)
        
        for i in range(2): # run it once, then save and reload and run again
            self.assertTrue(hasattr(u, 'key1'))
            self.assertTrue(hasattr(u, 'key2'))
            self.assertTrue(hasattr(u, 'key3'))
            
            self.assertEqual(u.attrib['key1'], 'value1')
            self.assertEqual(u.attrib['key2'], 'value2')
            self.assertEqual(u.attrib['key3'], 3)
            
            self.assertEqual(u.key1, 'value1')
            self.assertEqual(u.key2, 'value2')
            self.assertEqual(u.key3, 3)
            
            u.save()
    
        
    def test_unisens_overwrite_load(self):
        folder = os.path.join(self.tmpdir, 'data', 'record2')
        u = Unisens(folder)
        u.key1 = 'value1'
        u.save()
        u = Unisens(folder)
        
        self.assertTrue(hasattr(u, 'key1'))
        self.assertEqual(u.key1, 'value1')
        self.assertEqual(u.attrib['key1'], 'value1')
        
        u = Unisens(folder, makenew=True)
        self.assertFalse(hasattr(u, 'key1'))
        self.assertNotIn('key1', u.attrib)        
        
        
    def test_entry_creation(self):
        folder = os.path.join(self.tmpdir, 'data', 'record2')
        for entrytype in [CustomEntry, ValuesEntry, SignalEntry, EventEntry]:
            
            with self.assertRaises(ValueError):
                entry = entrytype()
            
            entry = entrytype(parent=folder, id='test.csv')
            entry.set_attrib('key1', 'value1')
            entry.key2 = 'value2'
            self.assertTrue(hasattr(entry, 'id'))
            self.assertTrue(hasattr(entry, 'key1'))
            self.assertTrue(hasattr(entry, 'key2'))

            self.assertEqual(entry.id, 'test.csv')
            self.assertEqual(entry.key1, 'value1')
            self.assertEqual(entry.key2, 'value2')
            self.assertEqual(entry.attrib['id'], 'test.csv')
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
        misc.set_attrib('key1', 'value1')
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
        custom.set_attrib('key2', 'value2')
        custom.set_attrib('key1', 'value2')
        self.assertTrue(hasattr(custom, 'key1'))
        self.assertTrue(hasattr(custom, 'key2'))
        self.assertEqual(len(custom.attrib), 2)
        self.assertEqual(custom.key1, 'value2')
        self.assertEqual(custom.key2, 'value2')

        
    def test_unisens_add_entr(self):
        folder = os.path.join(self.tmpdir, 'data', 'record')
        u = Unisens(folder, makenew=True)
        
        for i,entrytype in enumerate([CustomEntry, ValuesEntry,
                                      SignalEntry, EventEntry]):
            entry = entrytype(parent=folder, id='test'+str(i)+'.csv')
            entry.set_attrib('key1', 'value1')
            entry.key2 = 'value2'
            u.add_entry(entry)
            if entrytype == CustomEntry:
                entry.set_data('test')
            else:
                entry.set_data([[1,2,3],[1,2,3]])

        self.assertEqual(len(u), 4)
        self.assertEqual(len(u.entries), 4)
        u.save()
        
        
        u = Unisens(folder)
        self.assertEqual(len(u), 4)
        
        u = Unisens(folder, makenew=True)
        self.assertEqual(len(u), 0)
        
        misc = MiscEntry(name='miscentry')
        misc.set_attrib('key2', 'value2')
        customattr = CustomAttributes('key1', 'value1')
        u.add_entry(misc)
        u.add_entry(customattr)
        self.assertEqual(len(u), 2)

    def test_unisens_autosave(self):
        
        folder = os.path.join(self.tmpdir, 'data', 'record')
        u = Unisens(folder, makenew=True, autosave=True)
        
        for i,entrytype in enumerate([CustomEntry, ValuesEntry,
                                      SignalEntry, EventEntry]):
            entry = entrytype(parent=folder, id=f'test{i}.csv')
            with open(os.path.join(entry._folder, f'test{i}.csv'), 'w'):pass
            entry.set_attrib('key1', 'value1')
            entry.key2 = 'value2'
            u.add_entry(entry)

        self.assertEqual(len(u), 4)
        self.assertEqual(len(u.entries), 4)
    
        u = Unisens(folder)
        self.assertEqual(len(u), 4)
        
 
        
    def test_load_examples(self):
        example1 = os.path.join(os.path.dirname(__file__), 'Example_001')
        
        u = Unisens(example1, readonly=True)
        self.assertEqual(len(u), 9)
        self.assertTrue(hasattr(u, 'entries'))
        self.assertTrue(hasattr(u, 'attrib'))
        for attr in ['version', 'measurementId', 'timestampStart']:
            self.assertIn(attr, u.attrib)
        self.assertEqual(u.attrib['version'], '2.0')
        self.assertEqual(u.attrib['timestampStart'], '2008-07-08T13:32:51')
        self.assertEqual(u.attrib['measurementId'], 'Example_001')

        
        for name in ['customAttributes', 'imp200.bin', 'ecg200.bin', 
                      'valid_signal.csv', 'trig_ref.csv', 'bp.csv',
                      'trig_test_osea_dry.csv', 'picture.jpg', 'default_ecg']:
            self.assertIn(name, u.entries)
            
        entry = u[0]
        self.assertEqual(entry.height, '1.74m')
        
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
            u = Unisens(example, readonly=True)
            entry = MiscEntry('group')
            u1 = u.copy()
            u1._readonly=False
            u1.add_entry(entry)
            u1.save(filename='test.xml')
            u2 = Unisens(folder=u1._folder, filename='test.xml')
            self.assertTrue(elements_equal(u1.to_element(), u2.to_element()))
            u2.add_entry(MiscEntry('binFileFormat'))
            u2.save(filename='test.xml')
            u2 = Unisens(folder=u1._folder,filename='test.xml')
            with self.assertRaises(AssertionError):
                elements_equal(u1.to_element(), u2.to_element())



    def test_load_data(self):
        example1 = os.path.join(os.path.dirname(__file__), 'Example_001')
        u = Unisens(example1, readonly=True)
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
        
        custom = u['picture.jpg']
        data = custom.get_data(dtype='binary')       
        self.assertEqual(len(data), 724116)
        data = custom.get_data(dtype='image')       
        data = np.asarray(data)
        self.assertEqual(data.shape, (1463, 1388, 3))
        
        self.assertEqual('Unisens: Example_001(0:00:00, 9 entries)', str(u))

   


    def test_save_signalentry(self):
        folder = os.path.join(self.tmpdir, 'data', 'record5')

        for dtype in ['int16', 'uint8', 'float', 'int32']:
            u = Unisens(folder, makenew=True)
            data1 = (np.random.rand(5,500)*100).astype(dtype)
            signal = SignalEntry(id='signal.bin', parent=u)
            signal.set_attrib('test', 'asd')
            signal.set_data(data1, sampleRate=500, lsbValue=1, unit='mV', 
                            comment='Test', contentClass='EEG')
            u.save()
            u1 = Unisens(folder)
            data2 = u1['signal.bin'].get_data()
            np.testing.assert_almost_equal(data1, data2)
        
        folder = os.path.join(self.tmpdir, 'data', 'record')
        u = Unisens(folder, makenew=True)
        
        
    def test_save_customtypes(self):
        folder = os.path.join(self.tmpdir, 'data', 'customtypes')
        from collections import OrderedDict
        u = Unisens(folder, makenew=True)
        image = np.random.randint(0, 128, (512, 512, 3), dtype=np.uint8)
        data = OrderedDict({'test':'test', 'asdv': '2345', 'adfg':['3','34','234']})
        text = 'asd,123;456\qwe,678;678'
        
        image_exts = ['.jpeg', '.jpg', '.bmp', '.png', '.tif', '.gif']
        for ext in image_exts:
            custom = CustomEntry(f'image{ext}', parent=u)
            custom.set_data(image)
        

        CustomEntry('data.npy', parent=u).set_data(image)
        CustomEntry('pickle.pkl', parent=u).set_data(data)
        CustomEntry('json.json', parent=u).set_data(data)
        CustomEntry('text.txt', parent=u).set_data(text)
        CustomEntry('text.csv', parent=u).set_data(text)
        u.save()
        
        u = Unisens(folder)
        np.testing.assert_array_equal(u['image.png'].get_data(), image)
        np.testing.assert_array_equal(u['image.bmp'].get_data(), image)
        np.testing.assert_array_equal(u['image.tif'].get_data(), image)
        self.assertEqual(u['text.csv'].get_data(), text)
        self.assertEqual(u['text.txt'].get_data(), text)
        self.assertDictEqual(u['json.json'].get_data(), data)
        np.testing.assert_array_equal(u['data.npy'].get_data(), image)
        self.assertDictEqual(u['pickle.pkl'].get_data(), data)

        
    def test_save_csvetry(self):
        self.tmpdir = tempfile.mkdtemp(prefix='unisens')

        folder = os.path.join(self.tmpdir, 'data', 'record1')
        
        u = Unisens(folder, makenew=True)
        times = [[i*100 + float(np.random.rand(1)), f'trigger {i}'] for i in range(15)]
        event = EventEntry(id='triggers.csv', parent=u, separator=',', decimalSeparator='.')
        event.set_attrib('contentClass','trigger')
        event.set_attrib('comment', 'marks the trigger pointy thingy dingies')
        event.set_data(times, contentClass='triggers', unit='ms')
        u.save()
        u2 = Unisens(folder)
        event2 = u2['triggers.csv']
        times2 = event2.get_data()
        self.assertSequenceEqual(times, times2)

    
        # now test with different separators   
        folder = os.path.join(self.tmpdir, 'data', 'record2')
        u = Unisens(folder, makenew=True)
        times = [[i*100 + float(np.random.rand(1)), f'trigger {i}'] for i in range(15)]
        event = EventEntry(id='triggers.csv', parent=u, separator=';', decimalSeparator=',')
        event.set_attrib('contentClass','trigger')
        event.set_attrib('comment', 'marks the trigger pointy thingy dingies')
        event.set_data(times, contentClass='triggers', unit='ms')
        u.save()
        u2 = Unisens(folder)
        event2 = u2['triggers.csv']
        times2 = event2.get_data()
        self.assertSequenceEqual(times, times2)
        
        # now test with np array
        folder = os.path.join(self.tmpdir, 'data', 'record3')
        u = Unisens(folder, makenew=True)
        times = np.random.rand(5, 15)
        event = EventEntry(id='triggers.csv', parent=u, separator=',', decimalSeparator='.')
        event.set_attrib('contentClass','trigger')
        event.set_attrib('comment', 'marks the trigger pointy thingy dingies')
        event.set_data(times, contentClass='triggers', unit='ms')
        u.save()
        u2 = Unisens(folder)
        event2 = u2['triggers.csv']
        times2 = event2.get_data()
        np.testing.assert_allclose(times, times2)

    def test_save_valuesentry(self):
        self.tmpdir = tempfile.mkdtemp(prefix='unisens')

        folder = os.path.join(self.tmpdir, 'data', 'record1')
        
        u = Unisens(folder, makenew=True)
        times = [[i*100 + float(np.random.rand(1)), f'trigger {i}'] for i in range(15)]
        event = ValuesEntry(id='triggers.csv', parent=u, separator=',', decimalSeparator='.')
        event.set_attrib('contentClass','trigger')
        event.set_attrib('comment', 'marks the trigger pointy thingy dingies')
        event.set_data(times, contentClass='triggers', unit='ms')
        u.save()
        u2 = Unisens(folder)
        event2 = u2['triggers.csv']
        times2 = event2.get_data()
        self.assertSequenceEqual(times, times2)
    
        # now test with different separators   
        folder = os.path.join(self.tmpdir, 'data', 'record2')
        u = Unisens(folder, makenew=True)
        times = [[i*100 + float(np.random.rand(1)), f'trigger {i}'] for i in range(15)]
        event = ValuesEntry(id='triggers.csv', parent=u, separator=';', decimalSeparator=',')
        event.set_attrib('contentClass','trigger')
        event.set_attrib('comment', 'marks the trigger pointy thingy dingies')
        event.set_data(times, contentClass='triggers', unit='ms')
        u.save()
        u2 = Unisens(folder)
        event2 = u2['triggers.csv']
        times2 = event2.get_data()
        self.assertSequenceEqual(times, times2)
        
        # now test with np array
        folder = os.path.join(self.tmpdir, 'data', 'record3')
        u = Unisens(folder, makenew=True)
        times = np.random.rand(5, 15)
        event = ValuesEntry(id='triggers.csv', parent=u, separator=',', decimalSeparator='.')
        event.set_attrib('contentClass','trigger')
        event.set_attrib('comment', 'marks the trigger pointy thingy dingies')
        event.set_data(times, contentClass='triggers', unit='ms')
        u.save()
        u2 = Unisens(folder)
        event2 = u2['triggers.csv']
        times2 = event2.get_data()
        np.testing.assert_allclose(times, times2)
        
    def test_access_no_ext_item(self):
        u = Unisens(tempfile.mkdtemp(prefix='unisens'))
        entry1 = SignalEntry('single.csv', parent=u)
        entry2 = SignalEntry('double.csv', parent=u)
        entry3 = SignalEntry('double.bin', parent=u)
        
        self.assertIs (u['single.csv'], entry1)
        self.assertIs (u['single'], entry1)
        self.assertIs (u['double.csv'], entry2)
        self.assertIs (u['double.bin'], entry3)
        with self.assertRaises(IndexError):
            u['double']
            
        self.assertIn('single.csv', u)
        self.assertIn('single', u)
        self.assertIn('double.csv', u)  
        self.assertNotIn('double', u)  
   
    
    def test_access_no_ext_attrib(self):
        u = Unisens(tempfile.mkdtemp(prefix='unisens'))
        entry1 = SignalEntry('single.csv', parent=u)
        entry2 = SignalEntry('double.csv', parent=u)
        entry3 = SignalEntry('double.bin', parent=u)
        
        self.assertIs (u.single, entry1)
        self.assertIs (u.single_csv, entry1)
        self.assertIs (u.double_csv, entry2)
        self.assertIs (u.double_bin, entry3)
        with self.assertRaises(IndexError):
            u.double
            
    
   
    def test_subentries(self):
        """this is not officially supported, but useful"""
        folder = tempfile.mkdtemp(prefix='unisens_x')
        u = Unisens(folder, makenew=True, autosave=True)
        c = CustomEntry(id='test.bin', parent=u).set_data(b'123')
        CustomEntry('feat1.txt', parent=c).set_data('123')
        CustomEntry('feat2.txt', parent=c).set_data('456')
        self.assertEqual(u['test']['feat1'].get_data(), '123')
        self.assertEqual(u['test']['feat2'].get_data(), '456')
        
        u = Unisens(folder)
        self.assertEqual(u['test']['feat1'].get_data(), '123')
        self.assertEqual(u['test']['feat2'].get_data(), '456')
        
    def test_entries_with_subfolder(self):
        """this is not officially supported, but useful"""
        folder = tempfile.mkdtemp(prefix='unisens_x')
        u = Unisens(folder, makenew=True, autosave=True)
        c = CustomEntry(id='test.bin', parent=u)
        c1=CustomEntry('sub/feat1.txt', parent=c).set_data('123')
        c2=CustomEntry('sub\\feat2.txt', parent=c).set_data('456')
        with self.assertRaises((ValueError, PermissionError)):
            CustomEntry('\\sub\\feat3.txt', parent=c).set_data('789')
            
        self.assertTrue(os.path.isfile(c1._filename), f'{c1._filename} not found')
        self.assertTrue(os.path.isfile(c2._filename), f'{c2._filename} not found')
        with open(os.path.join(folder, 'test.bin'), 'w'):pass
        u = Unisens(folder)
        self.assertEqual(u['test']['feat1'].get_data(), '123')
        self.assertEqual(u['test']['sub/feat2.txt'].get_data(), '456')
        
        
    def test_copy(self):
        folder = tempfile.mkdtemp(prefix='unisens_copy')
        u1 = Unisens(folder, makenew=True, autosave=True)
        CustomEntry('test1.txt', parent=u1).set_data('asd')
        u2 = u1.copy()
        CustomEntry('test2.txt', parent=u1).set_data('qwerty')
        
        u1.asd = 2
        self.assertTrue(hasattr(u1, 'asd'))
        self.assertFalse(hasattr(u2, 'asd'))
        
        self.assertEqual(u1['test1'].get_data(), 'asd')
        self.assertEqual(u2['test1'].get_data(), 'asd')
        self.assertEqual(u1['test2'].get_data(), 'qwerty')
        
        with self.assertRaises(KeyError):
            u2['test2']
        
        
    def test_nostacking(self):
        """this is not officially supported, but useful"""
        folder = tempfile.mkdtemp(prefix='unisens_')
        
        c = CustomEntry(id='test.bin', parent=folder)
        f = FileEntry('feat1.txt', parent=folder)
        c.add_entry(f.copy())
        c.add_entry(f.copy())
        self.assertEqual(len(c), 2)
        
        c = CustomEntry(id='test.bin', parent=folder)
        f = FileEntry('feat1.txt', parent=folder)
        c.add_entry(f.copy(), stack=False)
        c.add_entry(f.copy(), stack=False)
        self.assertEqual(len(c), 1)
        
        c = CustomEntry(id='test.bin', parent=folder)
        f = MiscEntry(name='Test', parent=folder)
        c.add_entry(f.copy().set_attrib('test1','val1'))
        c.add_entry(f.copy().set_attrib('test2','val2'))
        self.assertEqual(len(c), 2)
        self.assertEqual(c['test'][0].test1, 'val1')
        self.assertEqual(c['test'][1].test2, 'val2')
        
        c = CustomEntry(id='test.bin', parent=folder)
        f = MiscEntry(name='Test', parent=folder)
        c.add_entry(f.copy().set_attrib('test1','val1'), stack=False)
        c.add_entry(f.copy().set_attrib('test2','val2'), stack=False)
        self.assertEqual(len(c), 1)
        self.assertEqual(c['test'].test2, 'val2')
        
        
    def test_indexfinding(self):
        """try whether the index finding method is working correctly"""
        folder = tempfile.mkdtemp(prefix='unisens_')
        
        c = CustomEntry(id='test.bin', parent=folder)
        FileEntry('feat1.txt', parent=c)
        FileEntry('FEAT1.bin', parent=c)
        FileEntry('feat2.txt', parent=c)
        
        self.assertEqual(c._get_index('feat2'), (2, 'feat2_txt'))
        self.assertEqual(c._get_index('feat2.txt'), (2, 'feat2_txt'))
        self.assertEqual(c._get_index('feat2_txt'), (2, 'feat2_txt'))
        self.assertEqual(c._get_index('feat1.txt'), (0, 'feat1_txt'))
        self.assertEqual(c._get_index('feat1_txt'), (0, 'feat1_txt'))
        self.assertEqual(c._get_index('feat1.bin'), (1, 'FEAT1_bin'))
        self.assertEqual(c._get_index('feat1_bin'), (1, 'FEAT1_bin'))
        
        
        self.assertEqual(c._get_index('fEAT2'), (2, 'feat2_txt'))
        self.assertEqual(c._get_index('fEAT2.txt'), (2, 'feat2_txt'))
        self.assertEqual(c._get_index('fEAT2_txt'), (2, 'feat2_txt'))
        self.assertEqual(c._get_index('fEAT1.txt'), (0, 'feat1_txt'))
        self.assertEqual(c._get_index('fEAT1_txt'), (0, 'feat1_txt'))
        self.assertEqual(c._get_index('fEAT1.bin'), (1, 'FEAT1_bin'))
        self.assertEqual(c._get_index('fEAT1_bin'), (1, 'FEAT1_bin'))
        
        with self.assertRaises(IndexError):
            c._get_index('feat1')
          
        with self.assertRaises(IndexError):
            c._get_index('FEAT1') 
            
        with self.assertRaises(KeyError):
            c._get_index('feat0')

            
    def test_indexfinding_subfolders(self):
        """try whether the index finding method is working correctly"""
        folder = tempfile.mkdtemp(prefix='unisens_')
        
        c = CustomEntry(id='test.bin', parent=folder)
        FileEntry('feat.txt', parent=c)
        FileEntry('feat/feat.txt', parent=c)
        FileEntry('feat/feat.bin', parent=c)
        FileEntry('feat/one.txt', parent=c)
        FileEntry('feat/one_two.txt', parent=c)
        
        self.assertEqual(c._get_index('feat.txt'), (0, 'feat_txt'))
        
        self.assertEqual(c._get_index('one'), (3, 'feat_one_txt'))
        self.assertEqual(c._get_index('one.txt'), (3, 'feat_one_txt'))
        self.assertEqual(c._get_index('one_two'), (4, 'feat_one_two_txt'))
        self.assertEqual(c._get_index('one_two.txt'), (4, 'feat_one_two_txt'))
        
        with self.assertRaises(IndexError):
            self.assertEqual(c._get_index('feat'), (0, 'feat_txt'))
        

        
    def test_nooverwrite(self):
        folder = tempfile.mkdtemp(prefix='unisens_copy')
        u = Unisens(folder, makenew=True, autosave=True)
        c = CustomEntry('test.txt', parent=u).set_attrib('a1', 'b1')
        self.assertEqual(u.test.a1, 'b1')
        with self.assertRaises(KeyError):
            c = CustomEntry('test.txt', parent=u).set_attrib('a2', 'b2')
            CustomEntry('asd.bin', parent=c)
      
        
    def test_loaddifferentfile(self):
        folder = tempfile.mkdtemp(prefix='unisens_newfile')
        u = Unisens(folder, makenew=True, autosave=False)
        c = CustomEntry('test.txt', parent=u).set_attrib('a1', 'b1').set_data('test')
        self.assertEqual(str(c), '<customEntry(test.txt)>')
        self.assertEqual(repr(c), '<customEntry(test.txt)>')
        u.save(filename='test.xml')
        self.assertTrue(os.path.isfile(os.path.join(u._folder, 'test.xml')))
        u1 = Unisens(folder, autosave=False)
        u2 = Unisens(folder, filename='test.xml', autosave=False)
        
        self.assertNotIn('test', u1)
        self.assertTrue(elements_equal(u.to_element(), u2.to_element()))
        
    def test_loaddifferentfile2(self):
        folder = tempfile.mkdtemp(prefix='unisens')
        u = Unisens(folder, makenew=True, autosave=True)
        CustomEntry('test.bin', parent=u).set_data(b'test')
        u.remove_entry('test.bin')
        
        CustomEntry('test.bin', parent=u).set_data(b'test')
        u.remove_entry('test')
        
        CustomEntry('test.bin', parent=u).set_data(b'test')
        u.remove_entry('test_bin') 
        
    def test_repr_str(self):
        folder = tempfile.mkdtemp(prefix='strrepr')
        u = Unisens(folder, makenew=True, autosave=True)
        u.measurementId = 'thisid'
        u.duration = 60*2 + 60*60*2 + 5
        a = str(u)
        b = repr(u)
        self.assertEqual(a,'Unisens: thisid(2:02:05, 0 entries)')
        self.assertEqual(b,f'Unisens(comment=, duration=2:02:05,  id=thisid,timestampStart={u.timestampStart})')
        
    def test_serialize(self)       :
        folder = tempfile.mkdtemp(prefix='seria')
        u = Unisens(folder, makenew=True, autosave=True)
        CustomEntry('test.bin', parent=u).set_data(b'test')
        CustomEntry('test2.bin', parent=u).set_data(b'test2')
        u.save()
        u.asd='asdf'
        
        with open(folder + '/asd.pkl', 'wb') as f:   
            pickle.dump(u, f)
            
        with open(folder + '/asd.pkl', 'rb') as f:   
            u1 = pickle.load(f)         
            
        elements_equal(u.to_element(), u1.to_element())
        
        
        
    def test_convert_nums(self):
        folder = tempfile.mkdtemp(prefix='convert_nums')
        u = Unisens(folder, makenew=True, autosave=True) 
        u.int = 1
        u.float = 1.5
        u.bool = True
        CustomEntry('entry.csv', parent=u).set_data('test')
        u.entry.int = 1
        u.entry.float = 1.5
        u.entry.bool = True
        
        self.assertEqual(u.int, 1)
        self.assertEqual(u.float, 1.5)
        self.assertEqual(u.bool, True)
        self.assertEqual(u.entry.int, 1)
        self.assertEqual(u.entry.float, 1.5)
        self.assertEqual(u.entry.bool, True)
        
        u1 =  Unisens(folder, readonly=True, convert_nums=False)  
        
        self.assertEqual(u1.int, '1')
        self.assertEqual(u1.float, '1.5')
        self.assertEqual(u1.bool, 'True')
        self.assertEqual(u1.entry.int, '1')
        self.assertEqual(u1.entry.float, '1.5')
        self.assertEqual(u1.entry.bool,'True')
        
        u1 =  Unisens(folder, readonly=True, convert_nums=True)  
        
        self.assertEqual(u1.int, 1)
        self.assertEqual(u1.float, 1.5)
        self.assertEqual(u1.bool, True)
        self.assertEqual(u1.entry.int, 1)
        self.assertEqual(u1.entry.float, 1.5)
        self.assertEqual(u1.entry.bool, True)


if __name__ == '__main__':
    unittest.main()














