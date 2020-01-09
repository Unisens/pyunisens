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

@author: skjerns
"""
import os
from entry import CustomAttributes, ValuesEntry, SignalEntry, EventEntry, \
                  Entry, Context, CustomEntry
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
        

class Unisens(Element):
    
    def __init__(self, folder, attrib=None, comment:str=None, duration:int=0, 
                 measurementId:str='', timestampStart=None, version=None,
                 root=None):
        
        self._folder = folder
        self.entries = AttrDict()
        self.events  = AttrDict()
        self.signals = AttrDict()
        self.values  = AttrDict()
        self.custom = AttrDict()
        
        if root is None and folder:
            self.read_unisens(folder)
        
        
        if attrib is None: attrib = {}
        _attrib = {'comment'  : comment,
                 'duration' : duration,
                 'measurementId' : measurementId,
                 'timestampStart': timestampStart,
                 'version' : version
                 }
        
        
        _attrib.update(attrib)

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
    
    def save(self,file, folder=None):
        """
        Save this Unisens xml file to filename.
        filename should be
        """
        # folder += '/'
        # file = os.path.join(os.path.dirname(folder), 'unisens.xml')
        ET.register_namespace("", "http://www.unisens.org/unisens2.0")
        et = ET.ElementTree(self)
        et.write(file, xml_declaration=True, default_namespace='', 
                 encoding='utf-8')
        logging.warning('should be folder, TODO')
    
    
    def read_unisens(self, folder):
        """
        Loads an XML Unisens file into this Unisens object.
        That means, self.attrib and self.children are added
        
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
                attrib = unpack(entry)
                entry = CustomAttributes(attrib = attrib)
            elif entryType == 'eventEntry':
                entry = EventEntry(folder=folder, element=entry)
            elif entryType == 'signalEntry':
                attrib = unpack(entry)
                entry = SignalEntry(folder=folder, element=entry)
            elif entryType == 'valuesEntry':
                entry = ValuesEntry(folder=folder, element=entry)
            elif entryType == 'customEntry':
                attrib = unpack(entry)
                entry = CustomEntry(folder=folder, element=entry)
            elif entryType == 'context':
                attrib = unpack(entry)
                entry = Context(attrib=attrib)
                l.append(attrib)
            else:
                logging.warning('Unknown entry type: {}'.format(entryType))
                entry = unpack(entry)
                # entry = CustomAttributes(attrib)
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
            print('nope add for entry {}'.format(entry))
        entryType = entry
        
        if isinstance(entryType, CustomAttributes):
            self.customAttributes = entry
            return self
        elif isinstance(entry, Context):
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
            print('what?', entryType, entry)
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
    

    

    
folder='C:/Users/Simon/Desktop/pyUnisens/unisens/'    
l =[]
self = Unisens(folder)
# a = self.entries['bloodpressure.csv']
b = ValuesEntry(id='values')
self.add_entry(b)
self.save('test.xml')

print(repr(self))
print(self)