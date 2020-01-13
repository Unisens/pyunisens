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

@author: skjerns
"""
import os
from entry import CustomAttributes, ValuesEntry, SignalEntry, EventEntry, \
                  Entry, Context, CustomEntry, Group, MiscEntry
from misc import AttrDict
import datetime
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import Element
import logging

    
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


def unpack(element):
    """
    Unpacks an xmltree element iteratively into an OrderedDict/AttrDict
    
    :param element: An xml tree element
    """
    d = AttrDict()
    attribs = element.attrib
    d.update(attribs)
    for child in element:
        key = strip(child.tag)
        i = 1
        while key in d:
            i += 1
            if i>2: key=key[:-5]
            key = key + '_%{}'.format(i)
        d[key] = unpack(child)
    return d
        

class Unisens(Entry):
    
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
        self.events  = AttrDict()
        self.signals = AttrDict()
        self.values  = AttrDict()
        self.custom  = AttrDict()
        
        if os.path.isfile(self._file) and not makenew:
            self.read_unisens(folder)
        else:
            logging.info('New unisens.xml will be created at {}'.format(\
                         self._file))
            if not timestampStart:
                now = datetime.datetime.now()
                timestampStart = now.strftime('%Y-%m-%dT%H:%M:%S')
            attrib = {'comment'  : str(comment),
                     'duration' : str(duration),
                     'measurementId' : str(measurementId),
                     'timestampStart': str(timestampStart),
                     'version' : '2.0'
                     }
            self.attrib  = AttrDict()
            self.set('comment', comment)
            self.set('duration', duration)
            self.set('measurementId', measurementId)
            self.set('timestampStart', timestampStart)
            self.set('version', '2.0')
            self.set('xsi:schemaLocation',"http://www.unisens.org/unisens2.0"+\
                          " http://www.unisens.org/unisens2.0/unisens.xsd")
            self.set('xmlns',"http://www.unisens.org/unisens2.0")
            self.set('xmlns:xsi', "http://www.w3.org/2001/XMLSchema-instance")
            
            self.tag = 'unisens'
            self.attrib = attrib
            self.tail = '\n  \n  \n  \n  '
            self.text = '\n'
        self.__dict__.update(self.attrib)
        

    def __getitem__(self, key):
        if isinstance(key, str):
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
    
    def save(self, filename, folder=None):
        """
        Save this Unisens xml file to filename.
        filename should be
        """
        # folder += '/'
        # file = os.path.join(os.path.dirname(folder), 'unisens.xml')
        ET.register_namespace("", "http://www.unisens.org/unisens2.0")
        et = ET.ElementTree(self)
        file = os.path.join(self._folder, filename)
        et.write(file, xml_declaration=True, default_namespace='', 
                 encoding='utf-8')
        logging.warning('should be folder, TODO')
    
    
    def read_unisens(self, folder):
        """
        Loads an XML Unisens file into this Unisens object.
        That means, self.attrib and self.children are added
        as well as tag, tail and text
        
        :param folder: folder where the unisens.xml is located. 
        :returns: self
        """
        folder += '/'
        file = os.path.join(os.path.dirname(folder), 'unisens.xml')
        if not os.path.exists(file):
            raise FileNotFoundError('{} does not exist'.format(folder))
            
        
        root = ET.parse(file).getroot()
        
        # copy all relevant attributes from root to this Unisens object
        # members will be added later
        self.attrib = root.attrib
        self.tag  = root.tag
        self.tail = root.tail
        self.text = root.text
                
        # attrib = root.attrib
        
        for entry in root:
            entryType = strip(entry.tag)

            l.append(entry)
            
            if entryType == 'customAttributes':
                # attrib = unpack(entry)
                entry = CustomAttributes(element = entry)
            elif entryType == 'eventEntry':
                entry = EventEntry(folder=folder, element=entry)
            elif entryType == 'signalEntry':
                entry = SignalEntry(folder=folder, element=entry)
            elif entryType == 'valuesEntry':
                entry = ValuesEntry(folder=folder, element=entry)
            elif entryType == 'customEntry':
                entry = CustomEntry(folder=folder, element=entry)
            elif entryType == 'context':
                entry = MiscEntry(element=entry)
            elif entryType == 'group':
                entry = MiscEntry(element=entry)
            else:
                logging.warning('Unknown entry type: {}'.format(entryType))
                entry = unpack(entry)
                entry.id = 'unknown'
            self.add_entry(entry)
        return self
    
    
    def add_entry(self, entry:Entry):
        """
        Add an entry to this Unisens object.
        Accepted entries are SignalEntry ValuesEntry, EventEntry, CustomEntry
        
        :param entry: An entry that will be added to this Unsisens meta object
        """
        try:
            self.append(entry)
        except:
            print('nope add for entry {}\n'.format(entry))
        entryType = entry
        
        if isinstance(entryType, (CustomAttributes)):
            self.customAttributes = entry
            return self
        elif isinstance(entry, MiscEntry):
            self.context = entry
            return self
        id = entry.id
        self.entries[id] = entry
        
        if isinstance(entryType, SignalEntry):
            self.signals[id] = entry
        elif isinstance(entryType, EventEntry):
            self.events[id] = entry
        elif isinstance(entryType, ValuesEntry):
            self.values[id] = entry  
        elif isinstance(entryType, CustomEntry):
            self.custom[id] = entry
        else:
            print('what?', entryType, entry,'\n' )
        entry._folder = self._folder
        return self
    

    def remove_entry(self, id:str):
        """
        Remove an entry by its unique ID (=filename)
        
        :param id: a string indicating the filename/id of the entry
        """
        if id not in self.entries:
            logging.error('{} is not in Unisens object'.format(id))
            return self
        for dictname in ['entries', 'values', 'events', 'signals']:
            if id in self.__dict__[dictname]:
                del self.__dict__[dictname][id]        
        return self
    

    def set_comment(self, comment:str):
        """
        Set the meta comment of this Unisens object
        
        :param comment: a string with a human readable commentary
        """
        self.set('comment', comment) 
        return self
    
    def set_duration(self, duration:int):
        """
        Set the duration of the measurements contained in this file
        
        :param duration: an int denoting the recoring length in seconds
        """
        self.set('duration', int)
        return self
        
    #TODO remove this and set automatically?
    def set_version(self, version:str):
        """
        Set the version of this unsisens definition, usually 2.0
        
        :param version: a string with a version number
        """
        self.set('version', version) 
        return self
    
    def set_measurementId(self, measurementId:str):
        """
        Set the name of this measurement
        
        :param measurementId: the id of this measurement, usually string or int
        """
        self.set('measurementId', measurementId) 
        return self

    def set_timestampStart(self, timestampStart:int):
        """
        Set the timestamp of the start of this recording
        
        :param timestampStart: an int of the UNIX timestamp of the recording start
        """
        self.set('timestampStart', timestampStart)
        return self
    
    def update_attributes(self, attr:dict):
        self.attrib.update(attr)
        return self




folder='C:/Users/Simon/Desktop/pyUnisens/unisens/example_003'    
l =[]
self = Unisens(folder)
a = self.customAttributes
a.newkey = 'newvalue'
# a.newkey2 = 'newvalue2'
a.set('newkey3', 'newvalue3')
a.newkey = 'newvalue'

a = self.customAttributes
self.save('test.xml')

print(repr(self))
print(self)