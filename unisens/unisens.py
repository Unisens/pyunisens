# -*- coding: utf-8 -*-
"""
Created on Wed Dec 11 20:21:57 2019

A Python interface to the unisens data and container format http://www.unisens.org

Unisens is a universal data format for multi sensor data. 
It was developed at the FZI Research Center for Information Technology and 
the Institute for Information Processing Technology (ITIV) at the KIT 
(formerly University of Karlsruhe). The motivation for specifying a new data 
format was the need for a universal, generic and sustainable format for storing 
and archiving sensor data from various recording systems. Other main requirements 
were a human readable header and the use of future-proof standards like XML.


todo: multi channel
todo: meta information nested
todo: XML
todo: init new object
todo: attrib + items unpack
todo: summary
todo: correct wdir
todo: edf2unisens
todo: __set attr__ for entry inhertance, update attrib
todo: plotting
todo: example file
todo: impolement del__
todo: implement update
todo: add group

@author: skjerns
"""


import os
import csv
import logging
import pandas as pd
import numpy as np
from misc import AttrDict
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import Element
import datetime
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
  

def make_key(string:str):
    """
    A function that turns any string into a valid python value string

    Parameters
    ----------
    string : str
        any string.

    Returns
    -------
    the string corrected for characters other than a-z, 0-9, _.
    """
    allowed = [chr(i) for i in range(97,123)] +\
              [chr(i) for i in range(65,91)]  +\
              [str(i) for i in range(9)] + ['_']
    if string[0].isdigit():
        s = 'x_'
    else:
        s = ''
    for c in string:
        s += c if c in allowed else '_'
    return s
    
  
def strip(string):
    """
    Strip a unisense identifier string of unnecessary elements
    such as version string {https://www.unisens.org/unisens2.0}
    """
    if '}' in string:
        string = string.split('}')[-1]
    return string    
   

def pack(xmldict):
    """
    Packs a dictionary back into elements with subclasses
    """
    attrib = {}
    children = []
    for key, value in xmldict.items():
        if isinstance(value, dict):
            _attrib, _children = pack(value)
            children.extent(_children)
            child = Element(key, attrib)
            children.append(child)
        else:
            attrib[key] = value
    return attrib, children





#
# a helper function for anti-camel case first letter
lowercase = lambda s: s[:1].lower() + s[1:] if s else ''
    
def validkey(key):
    """
    Check if a tag or a key is valid.
    In XML this basically means that the 
    key does not start with a number.
    """
    assert isinstance(key, str), 'Key must be string'
    if key[0].isdigit():
        raise ValueError('Key cannot start with a number: {}'.format(key))
    return key



class Entry():
    
    def __iter__(self):
        return self._entries.__iter__()
    
    def __init__(self, attrib=None, folder='.', id=None, **kwargs):
        if attrib is None: attrib=dict()
        self.attrib = attrib
        self.__dict__.update(self.attrib)
        self._entries = list()
        self._folder = folder
        if 'id' in self.attrib:
            self._filename = os.path.join(self._folder, self.id)
            if not os.path.exists(self._filename):
                logging.error('File for {} does not exist'.format(self.id))
        elif 'id':
            if os.path.splitext(str(id))[-1]=='':
                logging.warning('id should be a filename, ie. .bin/.csv/...')
        # else:
        #     raise ValueError('id must be supplied')
    
    def append(self, entry):
        self._entries.append(entry)
        # for subentry in entry:
            # self.append(subentry)
        # print(entry)
        # self.__dict__[element.tag] = element
        return self
    
    
    def __setattr__(self, name, value):
        """
        This will allow to set new attributes with .attrname = value
        while warning the user if builtin methods are overwritten
        """
        methods = dir(type(self))
        super.__setattr__(self, name, value)
        # do not overwrite if it's a builtin method
        if name not in methods and not name.startswith('_') and \
            isinstance(value, (int, float, bool, bytes, str)):
            self.set(name, value)

            

    def set(self, name, value):
        """
        Set an attribute of this Entry

        Parameters
        ----------
        name : str
            The name of this attribute
        value : (str, int, float)
            DESCRIPTION.

        Returns
        -------
        self

        """
        validkey(name)
        self.attrib[name] = value
        self.__dict__.update(self.attrib)
        return self
                   
        
    def __repr__(self):
        owntype = lowercase(type(self).__name__)
        id = self.attrib.get('id', 'None')
        return "<{}({})>".format(owntype, id)

    def to_element(self):
        owntype = lowercase(type(self).__name__)
        element = Element(owntype, attrib=self.attrib.copy())
        element.tail = '\n  \n  \n  '
        element.text = '\n'
        for subelement in self._entries:
            element.append(subelement.to_element())
        return element
    
    def to_xml(self):
        element = self.to_element()
        return ET.tostring(element).decode()
    
    
    def remove_attr(self, name):
        """
        Removes a custom attribute/value of this entry.
        
        :param key: The name of the custom attribute
        """
        if name in self.attrib: 
            del self.attrib[name]
            del self.__dict__[name]
        else:
            logging.error('{} not in attrib'.format(name))
        return self

        
        
class SignalEntry(Entry):
    
    def __init__(self, attrib=None, folder='.', **kwargs):
        super().__init__(attrib=attrib, folder=folder, **kwargs)
        
    def get_data(self, scaled=True):
        """
        Will try to load the binary data using numpy.
        This might not always work as endianess can't be determined
        with numpy
        
        :param scaled: Scale values using scaling factor or return raw numbers
        """
        dtypestr = self.dataType
        dtype = np.__dict__.get(dtypestr)
        data = np.fromfile(self._filename, dtype=dtype)
        if scaled:
            data = (data * float(self.lsbValue)).astype(dtype)
        return data
    
    def set_data(self, data:np.ndarray, sampleRate:int=None, lsbValue:float=1,
                 unit=None, comment=None, contentClass=None):
        """
        Set the data that is connected to this SignalEntry.
        The data will in any case be saved with Endianness LITTLE,
        as this is the default for numpy. Data will be saved using
        numpy binary data output.
        
        :param data: an numpy array or list with values
        :param sampleRate: the sample rate of this data
        :param lsbValue: the value with which this data is scaled.
                         this means that            
        """
        raise NotImplementedError


class ValuesEntry(Entry):
    def __init__(self,attrib=None, folder='.' , **kwargs):
        super().__init__(attrib=attrib, folder=folder, **kwargs)
        if not 'csvFileFormat' in self.__dict__:
            logging.warn('csvFileFormat information missing for {}'\
                         ' assuming decimal=. and sep=;'.format(self.id))
            csvFileFormat = MiscEntry(name = 'csvFileFormat')
            csvFileFormat.set('decimal', '.')
            csvFileFormat.set('separator', ';')
            self.append(csvFileFormat)        
            
    def get_data(self, mode:str='list'):
        """
        Will try to load the csv data using pandas.
        
        :param mode: select the return type
                     valid options: ['list', 'pandas', 'numpy']
        :returns: a list, dataframe or numpy array
        """
        separator = self.csvFileFormat.separator
        if mode in ('numpy', 'np', 'array'):
            data = np.genfromtxt(self._filename, delimiter=separator, dtype=str)
        elif mode in ('pandas', 'pd', 'dataframe'):
            data = pd.read_csv(self._filename, sep=separator,header=None,index_col=0)
        elif mode == 'list':
            dialect = csv.Dialect(csv.Dialect.excel)
            with open(self._filename, 'r') as f:
                dialect = csv.excel
                dialect.delimiter=separator
                reader = csv.reader(f, dialect=dialect)
                data = list(reader)
                data = [[x for x in d if not x==''] for d in data]
        else:
            raise ValueError('Invalid mode: {}, select from'
                             '["numpy", "pandas", "list"]'.format(mode))
        return data
    
class EventEntry(Entry):
    
    def __init__(self,attrib=None, folder='.', **kwargs):
        super().__init__(attrib=attrib,folder=folder, **kwargs)
        if not 'csvFileFormat' in self.__dict__:
            logging.warn('csvFileFormat information missing for {}'\
                         ' assuming decimal=. and sep=;'.format(self.id))
            csvFileFormat = MiscEntry(name = 'csvFileFormat')
            csvFileFormat.set('decimal', '.')
            csvFileFormat.set('separator', ';')
            self.append(csvFileFormat)
            
    def get_data(self, mode:str='list'):
        """
        Will try to load the csv data using pandas.
        
        :param mode: select the return type
                     valid options: ['list', 'pandas', 'numpy']
        :returns: a list, dataframe or numpy array
        """
        separator = self.csvFileFormat.separator
        if mode in ('numpy', 'np', 'array'):
            data = np.genfromtxt(self._filename, delimiter=separator, dtype=str)
        elif mode in ('pandas', 'pd', 'dataframe'):
            data = pd.read_csv(self._filename, sep=separator,header=None,index_col=0)
        elif mode == 'list':
            dialect = csv.excel
            dialect.delimiter=separator
            with open(self._filename, 'r') as f:
                reader = csv.reader(f, dialect=dialect)
                data = list(reader)
                data = [[x for x in d if not x==''] for d in data]
                data = [[float(d[0])] + d[1:] for d in data]
        else:
            raise ValueError('Invalid mode: {}, select from'
                             '["numpy", "pandas", "list"]'.format(mode))
        return data


class CustomAttributes(Entry):
    def __init__(*args,**kwargs):
        Entry.__init__(*args,**kwargs)       

class CustomEntry(Entry):
    def __init__(*args,**kwargs):
        Entry.__init__(*args,**kwargs)       
    

class MiscEntry(Entry):
    def __init__(*args,**kwargs):
        Entry.__init__(*args,**kwargs)       
    
    
class Unisens(Entry):
    """
    Initializes a Unisens object.
    If a unisens.xml file is already present in the folder, it will load
    the unisens data contained in this xml. If makenew=True is set, 
    the given unisens.xml will be replaced with a new unisens object.
    If no unisens.xml is present, a new unisens object will be created.
    
    :param folder: The folder where the unisens data is stored.
    :param makenew: Create a new unisens.xml, even if one is present.
    If no unisens.xml is present and new=False
    :param attrib: The attribute 
    """
    def __init__(self, folder, makenew=False, comment:str='', duration:int=0, 
                 measurementId:str='NaN', timestampStart=''):
        """
        Initializes a Unisens object.
        If a unisens.xml file is already present in the folder, it will load
        the unisens data contained in this xml. If makenew=True is set, 
        the given unisens.xml will be replaced with a new unisens object.
        If no unisens.xml is present, a new unisens object will be created.
        
        :param folder: The folder where the unisens data is stored.
        :param makenew: Create a new unisens.xml, even if one is present.
        If no unisens.xml is present and new=False
        :param attrib: The attribute 
        """
        os.makedirs(folder, exist_ok=True)
        folder = os.path.dirname(folder + '/')
        self._folder = folder
        self._file = os.path.join(folder, 'unisens.xml')
        self.entries = AttrDict()
        self._entries = list()
        
        if os.path.isfile(self._file) and not makenew:
            logging.info('loading unisens.xml from {}'.format(\
                         self._file))
            self.read_unisens(folder)
        else:
            logging.info('New unisens.xml will be created at {}'.format(\
                         self._file))
            if not timestampStart:
                now = datetime.datetime.now()
                timestampStart = now.strftime('%Y-%m-%dT%H:%M:%S')
            self.attrib  ={}
            self.set('comment', comment)
            self.set('duration', duration)
            self.set('measurementId', measurementId)
            self.set('timestampStart', timestampStart)
            self.set('version', '2.0')
            self.set('xsi:schemaLocation',"http://www.unisens.org/unisens2.0"+\
                          " http://www.unisens.org/unisens2.0/unisens.xsd")
            self.set('xmlns',"http://www.unisens.org/unisens2.0")
            self.set('xmlns:xsi', "http://www.w3.org/2001/XMLSchema-instance")
        
    def __setattr__(self, name, value):
        """
        This will allow to set new attributes with .attrname = value
        while warning the user if builtin methods are overwritten
        """
        return Entry.__setattr__(self, name, value)

    def set(self, name, value):
        return Entry.set(self, name, value)

    def __getitem__(self, key):
        if isinstance(key, str):
            for dictname in ['entries', 'values', 'events', 'signals']:
                if key in self.__dict__[dictname]:
                    return self.__dict__[dictname][key]
            return self.entries[key]
        elif isinstance(key, int):
            return super().__getitem__(key)
    
    def __str__(self):
        duration = self.__dict__.get('duration', 0)
        duration = str(datetime.timedelta(seconds=int(duration)))
        n_entries = len(self.entries)
        id = self.__dict__.get('measurementId', 'no ID')
        s = 'Unisens: {}({}, {} entries)'.format(id, duration, n_entries)
        return s
    
    def __repr__(self):
        comment = self.__dict__.get('comment', '')[:20] + '[..]'
        duration = self.__dict__.get('duration', 0)
        measurementId = self.__dict__.get('timestampStart', 0)
        version = self.__dict__.get('version', '2.0')
        timestampStart = self.__dict__.get('timestampStart', 0)

        s = 'Unisens(comment={}, duration={}, measurementId={}, ' \
            'timestampStart={}, version={})'.format(comment, duration, 
                                                    measurementId, 
                                                    timestampStart, 
              version)
        return s
    
    
    def unpack_element(self, element):
        """
        Unpacks an xmltree element iteratively into an OrderedDict/AttrDict
        
        :param element: An xml tree element
        """
        # iteratively upack_element the subelements of this element
        attrib = element.attrib.copy()
        entryType = strip(element.tag)
        if entryType == 'customAttributes':
            entry = CustomAttributes(attrib=attrib, folder=self._folder)
        elif entryType == 'eventEntry':
            entry = EventEntry(attrib=attrib, folder=self._folder)
        elif entryType == 'signalEntry':
            print(attrib)
            entry = SignalEntry(attrib=attrib, folder=self._folder)
        elif entryType == 'valuesEntry':
            entry = ValuesEntry(attrib=attrib, folder=self._folder)
        elif entryType == 'customEntry':
            entry = CustomEntry(attrib=attrib, folder=self._folder)
        elif entryType in ('context', 'group'):
            entry = MiscEntry(attrib=attrib, folder=self._folder)
        else:
            logging.warning('Unknown entry type: {}'.format(entryType))
            entry = MiscEntry(attrib=attrib, folder=self._folder)
        for subelement in element:
            subentry = self.unpack_element(subelement)
            entry.append(subentry)
        
        return entry
    
    def save(self, folder=None, filename='unisens.xml'):
        """
        Save this Unisens xml file to filename.
        filename should be
        """
        if folder is None:
            folder = self._folder
        ET.register_namespace("", "http://www.unisens.org/unisens2.0")
        element = self.to_element()
        et = ET.ElementTree(element)
        file = os.path.join(folder, filename)
        et.write(file, xml_declaration=True, default_namespace='', 
                 encoding='utf-8')
    
    
    def read_unisens(self, folder):
        """
        Loads an XML Unisens file into this Unisens object.
        That means, self.attrib and self.children are added
        as well as tag, tail and text
        
        :param folder: folder where the unisens.xml is located. 
        :returns: self
        """
        folder += '/' # to avoid any errors and confusion, append /
        file = os.path.join(os.path.dirname(folder), 'unisens.xml')
        if not os.path.exists(file):
            raise FileNotFoundError('{} does not exist'.format(folder))
            
        
        root = ET.parse(file).getroot()
        
        # copy all attributes from root to this Unisens object
        self.attrib = root.attrib
        # now add all elements that are contained in this XML object
        for element in root:
            entry = self.unpack_element(element)
            self.append(entry)
            id = entry.attrib.get('id', 'None')
            self.entries[id] = entry
        self.__dict__.update(self.attrib)
        keys = [make_key(key) for key in self.entries]
        entries = zip(keys, self.entries.values())
        self.__dict__.update(entries)
        return self
    

    

    




folder='C:/Users/Simon/Desktop/pyUnisens/unisens/example_003'    
self = Unisens(folder)
a = self.ecg_m500_250_bin
# a = self.customAttributes
# a.newkey = 'newvalue'

# self.save('test.xml')

