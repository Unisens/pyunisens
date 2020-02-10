# -*- coding: utf-8 -*-
"""
Created on Mon Jan  6 21:16:58 2020

@author: skjerns
"""
import os
import numpy as np
import logging
from utils import validkey, strip, lowercase
from lxml.etree import ElementTree as ET
from lxml.etree import Element


class Entry():
    
    def __len__(self):
        return len(self._entries)
    
    def __iter__(self):
        return self._entries.__iter__()
    
    def __repr__(self):
        return "<{}({})>".format(self._name, self.attrib)
    
    def __init__(self, attrib=None, folder='.'):
        if attrib is None: attrib=dict()
        self.attrib = attrib
        self.__dict__.update(self.attrib)
        self._entries = list()
        self._folder = folder
        self._name = lowercase(type(self).__name__)
    
    def __setattr__(self, name:str, value:str):
        """
        This will allow to set new attributes with .attrname = value
        while warning the user if builtin methods are overwritten
        """
        methods = dir(type(self))
        super.__setattr__(self, name, value)
        # do not overwrite if it's a builtin method
        if name not in methods and not name.startswith('_') and \
            isinstance(value, (int, float, bool, bytes, str)):
            self.set_attr(name, value)



    def add_entry(self, entry:'Entry'):
        self._entries.append(entry)
        name = entry._name
        # if an entry already exists with this exact name
        # we put the entry inside of a list and append the new entry
        # with the same name. This way all entries are saved
        if name in self.__dict__:
            if isinstance(self.__dict__[name], list):
                self.__dict__[name].append(entry)
            else:
                self.__dict__[name] = [self.__dict__[name]]
                self.__dict__[name].append(entry)
        else:
            self.__dict__[entry._name] = entry
        return self

    def remove_entry():
        pass

    def set_attr(self, name:str, value:str):
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
        name = str(name)
        value = str(value)
        name = validkey(name)
        self.attrib[name] = value
        self.__dict__.update(self.attrib)
        return self
    
    def remove_attr(self, name:str):
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
        

    def to_element(self):
        element = Element(self._name, attrib=self.attrib.copy())
        element.tail = '\n  \n  \n  '
        element.text = '\n'
        for subelement in self._entries:
            element.append(subelement.to_element())
        return element
    
    def to_xml(self):
        element = self.to_element()
        return ET.tostring(element).decode()
    
    

class FileEntry(Entry):
    """
    This is a Entry subtype that has an ID, ie a file associated with it.
    Subtypes of FileEntry include ValuesEntry, EventEntry, CustomEntry and
    SignalEntry.
    """
    
    def __repr__(self):
        id = self.attrib.get('id', 'None')
        return "<{}({})>".format(self._name, id)
    
    def __init__(self, id, attrib=None, folder='.', **kwargs):
        super().__init__(attrib=attrib, folder=folder, **kwargs)
        if 'id' in self.attrib:
            self._filename = os.path.join(self._folder, self.id)
            self.set_attr('id', self.id)
            if not os.path.exists(self._filename):
                logging.error('File for {} does not exist'.format(self.id))               
        elif id:
            if os.path.splitext(str(id))[-1]=='':
                logging.warning('id should be a filename, ie. .bin/.csv/...')
            self.set_attr('id', id)
        else:
            raise ValueError('id must be supplied')
        
        
class SignalEntry(FileEntry):
    
    def __init__(self, id=None,  attrib=None, folder='.', **kwargs):
        super().__init__(id=id, attrib=attrib, folder=folder, **kwargs)
        
    def get_data(self, scaled:bool=True, return_type:str='numpy') -> np.array:
        """
        Will try to load the binary data using numpy.
        This might not always work as endianess can't be determined
        with numpy
        
        :param scaled: Scale values using scaling factor or return raw numbers
        :param return_type: numpy, list or pandas. Pandas row indices have the 
                            names of the corresponding channels. List will be
                            in format [[ch_name1, data],[ch_name2, data]]
                            numpy will be as plain numpy array without ch_names
        """
        if return_type!='numpy': raise NotImplementedError
        n_channels = len(self.channel) if isinstance(self.channel,list) else 1
        dtypestr = self.dataType
        dtype = np.__dict__.get(dtypestr)
        data = np.fromfile(self._filename, dtype=dtype)
        if scaled:
            data = (data * float(self.lsbValue))
        data = data.reshape([n_channels, -1])
        return data
    
    def set_data(self, data:np.ndarray, sampleRate:int=None, lsbValue:float=1,
                 unit:str=None, comment:str=None, contentClass:str=None):
        """
        Set the data that is connected to this SignalEntry.
        The data will in any case be saved with Endianness LITTLE,
        as this is the default for numpy. Data will be saved using
        numpy binary data output.
        
        :param data: an numpy array or list with values
        :param sampleRate: the sample rate of this data
        :param lsbValue: the value with which this data is scaled.
                         this means that       
        :param comment: sets a comment associated with this data
        :param contentClass: sets the content class, e.g. EEG, ECG,...
        """
        raise NotImplementedError


class ValuesEntry(FileEntry):
    def __init__(self, id=None, attrib=None, folder='.' , **kwargs):
        super().__init__(id=id, attrib=attrib, folder=folder, **kwargs)
        if not 'csvFileFormat' in self.__dict__:
            logging.warn('csvFileFormat information missing for {}'\
                         .format(self.id))
            # csvFileFormat = MiscEntry(name = 'csvFileFormat')
            # csvFileFormat.set_attr('decimal', '.')
            # csvFileFormat.set_attr('separator', ';')
            # self.add_entry(csvFileFormat)        
            
    def get_data(self, mode:str='list'):
        """
        Will try to load the csv data using a list, pandas or numpy.
        
        :param mode: select the return type
                     valid options: ['list', 'pandas', 'numpy']
        :returns: a list, dataframe or numpy array
        """
        separator = self.csvFileFormat.separator
        decimal = self.csvFileFormat.decimalSeparator
        def make_digit(string): # helper function to convert to numbers
            if string.isdigit(): return int(string)
            try: return float(string.replace(decimal, '.'))
            except: return string
        
        if mode in ('numpy', 'np', 'array'):
            lines = np.genfromtxt(self._filename, delimiter=separator, 
                                 dtype=str)
        elif mode in ('pandas', 'pd', 'dataframe'):
            import pandas as pd
            lines = pd.read_csv(self._filename, sep=separator,
                               header=None, index_col=None)
        elif mode == 'list':

            with open(self._filename, 'r') as f:
                data = f.read()
                data = data.replace('\r', '') # remove unix linebreaks
                lines = data.split('\n')
                lines = [line.split(separator) for line in lines]
                lines = [[x for x in d if not x==''] for d in lines]
                lines = [x for x in lines if x!=[]]
                lines = [[make_digit(e) for e in entry] for entry in lines]
        else:
            raise ValueError('Invalid mode: {}, select from'
                             '["numpy", "pandas", "list"]'.format(mode))
        return lines
        
    
class EventEntry(FileEntry):
    
    def __init__(self, id=None, **kwargs):
        super().__init__(id=id, **kwargs)
        if not 'csvFileFormat' in self.__dict__:
            logging.warn('csvFileFormat information missing for {}'\
                         .format(self.id))
            # csvFileFormat = MiscEntry(name = 'csvFileFormat')
            # csvFileFormat.set_attr('decimal', '.')
            # csvFileFormat.set_attr('separator', ';')
            # self.add_entry(csvFileFormat)
            
    def get_data(self, mode:str='list'):
        """
        Will try to load the csv data using a list, pandas or numpy.
        
        :param mode: select the return type
                     valid options: ['list', 'pandas', 'numpy']
        :returns: a list, dataframe or numpy array
        """
        # we just forward the call to the other function
        return ValuesEntry.get_data(self, mode)


class CustomEntry(FileEntry):
    
    def __init__(self, id=None, **kwargs):
        super().__init__(id=id, **kwargs)      
        
    def get_data(self, dtype='binary'):
        """
        Will load the binary data of this CustomEntry.
        Has builtin functionality to load images using PIL
        
        :param dtype: binary or image.
        :returns: the binary data or an PIL.Image
        """
        if dtype=='binary':
            with open(self._filename, 'rb') as f:
                data = f.read()
        elif dtype=='image':
            from PIL import Image
            data = Image.open(self._filename)
        else:
            raise ValueError('unknown dtype {}'.format(dtype))
        return data
        
    
class CustomAttributes(Entry):
    def __init__(self, key:str=None, value:str=None, **kwargs):
        super().__init__(**kwargs)   
        if key and value:
            self.set_attr(key, value)
        
    def to_element(self):
        element = Element(self._name, attrib={})
        element.tail = '\n  \n  \n  '
        element.text = '\n'
        for key in self.attrib:
            customAttribute = MiscEntry(name = 'customAttribute')
            customAttribute.key = key
            customAttribute.value = self.attrib[key]
            subelement = customAttribute.to_element()
            element.append(subelement)
        return element
    
    def add_entry(self, entry:'MiscEntry'):
        if entry._name != 'customAttribute':
            logging.error('Can only add customAttribute type')
            return
        e.append(entry)
        self.set_attr(entry.key, entry.value)
  
class MiscEntry(Entry):
    def __init__(self, name:str, key:str=None, value:str=None, **kwargs):
        super().__init__(**kwargs) 
        self._name = strip(name)
        if key and value:
            self.set_attr(key, value)
            
class CustomAttribute(MiscEntry):
    def __new__(*args,**kwargs):
        return MiscEntry('customAttribute', **kwargs)


e=[]
if __name__ == '__main__':
    from unisens import Unisens
    u = Unisens('C:/Users/Simon/Desktop/pyUnisens/unisens/test/Example_001')
            
            
            
            
            
        
        
        
        
        