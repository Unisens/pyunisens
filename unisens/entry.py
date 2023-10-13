# -*- coding: utf-8 -*-
"""
Created on Mon Jan 6 21:16:58 2020

@author: skjerns
"""
from __future__ import annotations

import importlib
import os, sys
import warnings
from abc import ABC
from typing import List, Tuple

import numpy as np
import logging
from .utils import validkey, strip, lowercase, make_key, valid_filename, infer_dtype
from .utils import read_csv, write_csv
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import Element
from copy import deepcopy


def get_module(name):
    try:
        module = importlib.import_module(name)
        return module
    except ModuleNotFoundError:
        print(f'{name} is not installed. Install with pip install {name}')
        raise Exception(f'Cant load module {name}')


class Entry(ABC):
    """
    Base class for Unisens entries. All other entries inherit from this.
    
    An Entry has an .attrib dict that specifies the attributes.
    It can have a parent object and child-entries.
    Attributes can be set via Entry.set_attrib(name, value) or directly
    via setting instance.name = value.
    Children can be accessed via instance['child'] or instance.child

    Parameters
    ----------
    attrib : dict, optional
        DESCRIPTION. an attribute dictionary  e.g. {duration:'4'}
    parent : Entry, optional
        DESCRIPTION. a folder or a Entry type.
    **kwargs : TYPE
        DESCRIPTION.
    """

    def __len__(self):
        return len(self._entries)

    def __iter__(self):
        return self._entries.__iter__()

    def __repr__(self):
        return "<{}({})>".format(self._name, self.attrib)

    def __init__(self, attrib=None, parent='.', **kwargs):

        if attrib is None:
            attrib = dict()
        self.__dict__['attrib'] = deepcopy(attrib)
        self.__dict__.update(self.attrib)
        self.__dict__['_entries'] = []
        self.__dict__['_folder'] = parent.__dict__['_folder'] if isinstance(parent, Entry) else parent
        self.__dict__['_parent'] = parent if isinstance(parent, Entry) else None
        self.__dict__['_name'] = lowercase(type(self).__name__)
        for key in kwargs:
            self.set_attrib(key, kwargs[key])
        self._autosave()

    def __contains__(self, item):
        if item in self.__dict__: return True
        if make_key(item) in self.__dict__: return True
        try:
            self.__getitem__(item)
            return True
        except:
            return False

    def __setattr__(self, name: str, value: str):
        """
        Allows settings of attributes via .name = value.
        """
        super.__setattr__(self, name, value)
        if name.startswith('_'): return
        methods = dir(type(self))
        # do not overwrite if it's a builtin method
        if name not in methods and \
                isinstance(value, (int, float, bool, bytes, str)):
            self.set_attrib(name, value)

    def __getattr__(self, key):
        if key == "__setstate__":
            raise AttributeError(key)
        try:
            return self.__dict__[key]
        except:
            pass
        try:
            i, key2 = self._get_index(key)
            return self.__dict__[key2]
        except KeyError:
            return self.__getattribute__(key)

    def __getitem__(self, key):
        if isinstance(key, str):
            i, key = self._get_index(key)
            return self.__dict__[key]
        elif isinstance(key, int):
            return self._entries[key]
        raise KeyError(f'{key} not found')

    def _autosave(self):
        """
        This function will call the `_autosave` method of `_parents`.
        If the uppermost `_parent` is a Unisens object changes will be saved
         according to its attribute `_autosave_enabled`.
        Otherwise nothing happens.
        """
        # not in Java version available
        if self._parent is not None:
            self._parent._autosave()

    def _check_readonly(self):
        """
        will raise an exception if a write operation 
        is requested to readonly file
        If available, the `_parent`'s writability is chosen over the instance's.
        """
        # not in Java version available
        if hasattr(self, '_parent') and hasattr(self._parent, '_check_readonly'):
            return self._parent._check_readonly()
        elif hasattr(self, '_readonly') and self._readonly:
            raise IOError(f'Read only, can\'t write to {self._folder}.')

    def _get_index(self, id_or_name: str, raises: bool = True) -> Tuple[int, str]:
        """
        Receive the index and key-name of an object.
        
        Sub-entries are saved at ._entries as objects in a list and
        in the __dict__ of the parent. The name of the object is either
        the id (eg. samples.csv), if it is a FileEntry, or the name 
        (eg. binFileFormat). This name is made into a attribute-accessible 
        key by make_key(), e.g. samples_csv. This function searches
        for the entry in ._entry and returns its index as well as its
        key name in the __dict__

        Caution: this only returns the first entry's index in _entries when stacking

        :param id_or_name: str
            The name or id of the Entry.
        :param raises: bool, optional
            Raise an exception if not found. The default is True.
        :return:
            i: int, index in ._entries
            key: str, key-name in __dict__, not id/_name in entry
        """

        id_or_name_key_upper = make_key(id_or_name).upper()

        # we don't care about case, gently ignoring Linux file case-sensitivity
        # first check for exact match
        for i, entry in enumerate(self._entries):
            if hasattr(entry, 'id'):
                id_key = make_key(entry.id)
                if id_key.upper() == id_or_name_key_upper:
                    return i, id_key  # check for match in key notation
            else:
                name = entry._name
                name_key = make_key(name)
                if name_key.upper() == id_or_name_key_upper:
                    return i, name

        id_or_name_upper = id_or_name.upper()
        found = []
        for i, entry in enumerate(self._entries):
            if hasattr(entry, 'id'):
                id_upper = entry.id.upper()
                no_ext = id_upper.rsplit('.', 1)[0]  # remove file extension
                # check if file without extension was requested
                # e.g. 'test' for test.txt
                if no_ext == id_or_name_upper:
                    found += [(i, make_key(entry.id))]
                elif '/' in id_upper or '\\' in id_upper:  # remove subdirectories
                    # e.g. 'test' was requested for 'sub/test.txt'
                    if os.path.basename(no_ext) == id_or_name_upper:
                        found += [(i, make_key(entry.id))]
                    # e.g. 'test.txt' was requested for 'sub/test.txt'
                    elif os.path.basename(id_upper) == id_or_name_upper:
                        found += [(i, make_key(entry.id))]

        if len(found) == 1: return found[0]
        if len(found) > 1: raise IndexError(f'More than one match for {id_or_name}: {found}')
        raise KeyError(f'{id_or_name} not found')

    def _set_channels(self, ch_names: List[str], n_data: int):
        """
        Checks existing channel attributes.
        Overwrites channel attributes if ch_names are supplied.
        Writes generic channel names if nothing is given.
        → Use in set_data for classes requiring channel names.

        :param ch_names: List of channel names (str) or single channel name as str or None
        :param n_data: amount of required channel names
            This might match lines / columns of data or
            one less if an index is expected.
        """
        if ch_names is not None:
            if isinstance(ch_names, str): ch_names = [ch_names]
            # this means new channel names are indicated and will overwrite.
            assert len(ch_names) == n_data, f'len {ch_names}!={n_data}'
            if hasattr(self, 'channel'):
                logging.warning('Channels present will be overwritten')
                self.remove_entry('channel')
            for name in ch_names:
                channel = MiscEntry('channel', key='name', value=name)
                self.add_entry(channel)
        elif not hasattr(self, 'channel'):
            # this means no channel names are indicated and none exist
            # we create new generic names for the channels
            logging.info('No channel names indicated, will use generic names')
            for i in range(n_data):
                channel = MiscEntry('channel', key='name', value=f'ch_{i}')
                self.add_entry(channel)
        elif len(self.channel) == n_data:
            # this means channel information is present and matches array
            pass
        else:
            # this means there are channel names there but do not match n_data
            raise ValueError('Channel names must match data')

    def copy(self) -> Entry:
        """
        Create a deep copy of this Entry without copying the parent.
        `_parent` is set to None for the resulting copy.

        Returns
        -------
        copy : Entry
            An Entry object with all attributes as the invoking object.

        """
        # in Java: clone when adding entry
        if hasattr(self, '_parent'):
            _parent = self._parent
            self._parent = None
            copy = deepcopy(self)
            self._parent = _parent
        else:
            copy = deepcopy(self)
        return copy

    def add_entry(self, entry: Entry, stack: bool = True):
        """
        Add an subentry to this entry
        
        The Entry will be added to the ._entries list and
        to the .__dict__ with its name or id as a key.
        The subentry can be accessed via entry.entry_name, entry['entry_name']
        or entry._entries[index]

        Parameters
        ----------
        entry : Entry
            a subentry that should be added.
        stack : bool, optional
            If True, an Entry with the same name/id will be added into a list.
            If False, an already existing Entry will be overwritten.
            The default is True.

        Returns
        -------
        TYPE
            DESCRIPTION.
        """
        # there are several Entries that have reserved names.
        # these should not exist double, therefore they are re-set here
        reserved = ['binFileFormat', 'csvFileFormat', 'customFileFormat']

        name = entry.attrib.get('id', entry.__dict__['_name'])
        name = make_key(name)

        if (not stack or entry._name in reserved):
            # remove old entry with this name if necessary
            try:
                self.remove_entry(name)
            except KeyError:
                pass

        if name in self.__dict__:
            # stack entries with the same name inside a list
            if not isinstance(self.__dict__[name], list):
                self.__dict__[name] = [self.__dict__[name]]
            self.__dict__[name].append(entry)
        else:
            self.__dict__[name] = entry

        self._entries.append(entry)
        entry._parent = self
        self._autosave()
        return self

    def remove_entry(self, name: str):
        """
        Removes a subentry by name.

        Parameters
        ----------
        name : str
            the name of the entry. 
            Can be abbreviated, e.g. 'samples' instead of 'samples.csv'.
        """
        i, key = self._get_index(name)
        del self._entries[i]
        del self.__dict__[key]
        return self

    def set_attrib(self, name: str, value: str):
        """
        Set an attribute of this Entry

        Parameters
        ----------
        name : str
            The name of this attribute
        value : (str, int, float)
            value to be added. will be converted to string.
        """
        name = validkey(name)
        self.attrib[name] = value
        self.__dict__.update({name: value})
        self._autosave()
        return self

    def get_attrib(self, name: str, default=None) -> str:
        """
        Retrieves an attribute of this Entry

        Parameters
        ----------
        name : str
            The name to be retrieved.
        default : str, optional
            What should be returned if not present. The default is None.

        """

        return self.attrib.get(name, default)

    def remove_attr(self, name: str):
        """
        Removes a custom attribute/value of this entry.

        Parameters
        ----------
        name : str
            The name of the custom attribute.

        Returns
        -------
        TYPE
            DESCRIPTION.
        """
        if name in self.attrib:
            del self.attrib[name]
            del self.__dict__[name]
        else:
            logging.error('{} not in attrib'.format(name))
        self._autosave()
        return self

    def to_element(self):
        """
        Converts this Entry and all its subentries into an XML Element.

        Returns
        -------
        element : Element
            An xml.etree.Element instance to be written to xml

        """
        attrib = {}
        for key, value in self.attrib.items():
            attrib[key] = str(value)
        element = Element(self._name, attrib=attrib.copy())
        element.tail = '\n'
        for subelement in self._entries:
            element.append(subelement.to_element())
        return element

    def to_xml(self):
        """
        Creates a string representing this Entry and all its sub-entries
        as XML.

        Returns
        -------
        str
            XML string representing this Entry instance.

        """

        element = self.to_element()
        return ET.tostring(element).decode()

    def print_summary(self, indent=0):
        """
        Prints a summary of this object containing all entries
        """
        print('\t' * indent, self)
        for entry in self._entries:
            entry.print_summary(indent + 1)


class FileEntry(Entry):
    """
    This is a Entry subtype that has an ID, ie a file associated with it.
    Subtypes of FileEntry include ValuesEntry, EventEntry, CustomEntry and
    SignalEntry.
    """

    def __repr__(self):
        id = self.attrib.get('id', 'None')
        return "<{}({})>".format(self._name, id)

    def __init__(self, id, attrib=None, parent='.', **kwargs):
        super().__init__(attrib=attrib, parent=parent, **kwargs)
        if 'id' in self.attrib:
            # reading entry (id == None)
            valid_filename(self.id)
            self._filename = os.path.join(self._folder, self.id)
            if not os.access(self._filename, os.F_OK):
                logging.error('File {} does not exist'.format(self.id))
        elif id:
            # writing entry
            valid_filename(id)
            if os.path.splitext(str(id))[-1] == '':
                logging.warning('id should be a filename with extension ie. .bin')
            self._filename = os.path.join(self._folder, id)
            self.set_attrib('id', id)
            # ensure subdirectories exist to write data
            if '/' in id or '\\' in id:
                sub_folder = os.path.dirname(self._filename)
                os.makedirs(sub_folder, exist_ok=True)
        else:
            raise ValueError('The id must be supplied if it is not yet set.')
        if isinstance(parent, Entry): parent.add_entry(self)


class SignalEntry(FileEntry):

    def __init__(self, id=None, attrib=None, parent='.', **kwargs):
        super().__init__(id=id, attrib=attrib, parent=parent, **kwargs)

    def get_data(self, scaled: bool = True, return_type: str = None) -> np.array:
        """
        Will try to load the binary data using numpy.
        This might not always work as endianess can't be determined
        with numpy

        Parameters
        ----------
        scaled : bool, optional
            Scale values using lsb factor or return raw numbers.
            The default is True.

        Returns
        -------
        np.ndarray
            The loaded binary data, in this case as numpy array.

        """

        if return_type is not None:
            warnings.warn(f'The argument `return_type` has no effect and will be removed with the next release.',
                          category=DeprecationWarning, stacklevel=2)

        if self.id.endswith('csv'):
            data = np.genfromtxt(self._filename, dtype=str, delimiter=self.csvFileFormat.separator)
            data = data.astype(float)
            return data.T

        assert self.id.endswith('bin') and 'lsbValue' in dir(self), \
            'incompatible id: SignalEntry only allows for .bin or .csv format'
        n_channels = len(self.channel) if isinstance(self.channel, list) else 1
        dtypestr = self.dataType.lower()
        dtype = np.__dict__.get(dtypestr, f'UNKOWN_DATATYPE: {dtypestr}')
        data = np.fromfile(self._filename, dtype=dtype)
        if scaled:
            if 'baseline' in self.attrib:
                data = ((data - float(self.baseline)) * float(self.lsbValue))
            elif self.lsbValue != 1:
                data = (data * float(self.lsbValue))
        return data.reshape([-1, n_channels]).T

    def set_data(self, data: np.ndarray, sampleRate: float = None, dataType: str = None,
                 ch_names: list = None, unit: str = None,
                 lsbValue: float = None, adcZero: int = None,
                 adcResolution: int = None, baseline: int = None,
                 comment: str = None, contentClass: str = None,
                 source: str = None, sourceId: str = None,
                 decimalSeparator: str = '.', separator: str = ';', **kwargs):
        """
        Set the data that is connected to this SignalEntry.
        The decision between binary and csv output is made with the 'id' from initialization.

        binary: Data will be stored after formatting to dataType. Please ensure that formatting is possible without
        loss of information. Scaling (with lsbValue and baseline) is only supported for reading.
        The data will in any case be saved with Endianness LITTLE,
        as this is the default for numpy. Data will be saved using
        numpy binary data output.

        csv: Similar to ValuesEntry except that the data is expected to be
         consecutive and thus not indexed.

        Parameters
        ----------
        data : np.ndarray
            in lines! len(self.channel) == len(data)
        dataType : str, optional
            The data type of the data. If None, is infered automatically.
            Can be 'DOUBLE', 'FLOAT', 'INT16', 'INT32', 
                   'INT8', 'UINT16', 'UINT32', 'UINT8'
            Will be used for binary stream output format. The default is None.
        ch_names : list, optional
            DESCRIPTION. The default is None.
        sampleRate : int, optional
            the sample rate of this data. The default is 256.
        lsbValue : float, optional
            the value with which this data is scaled this means that. 
            The default is 1.
        unit : str, optional
            the unit which is indicated, e.g. mV, Ohm. The default is None.
        comment : str, optional
            sets a comment associated with this data. The default is None.
        contentClass : str, optional
            sets the content class, e.g. EEG, ECG. The default is None.
        adcResolution : int, optional
            DESCRIPTION. The default is None.
        baseline : float, optional
            DESCRIPTION. The default is None.
        **kwargs : TYPE
            DESCRIPTION.
        """

        self._check_readonly()

        data = np.atleast_2d(np.array(data))
        if dataType is None:
            if 'dataType' in self.attrib:
                dataType = self.dataType
            else:
                dataType = str(data.dtype)
        self.set_attrib('dataType', infer_dtype(dataType).lower())

        if lsbValue is not None:
            self.set_attrib('lsbValue', lsbValue)
        elif 'lsbValue' not in self.attrib:
            self.set_attrib('lsbValue', 1)
        if baseline is not None:
            self.set_attrib('baseline', baseline)

        if self.id.endswith('csv'):
            fileFormat = MiscEntry('csvFileFormat', parent=self)
            fileFormat.set_attrib('decimalSeparator', decimalSeparator)
            fileFormat.set_attrib('separator', separator)
            self.add_entry(fileFormat)

            write_csv(self._filename, data.T, sep=self.csvFileFormat.separator,
                      decimal_sep=self.csvFileFormat.decimalSeparator)
        elif self.id.endswith('bin'):
            order = sys.byteorder.upper()  # endianess
            fileFormat = MiscEntry('binFileFormat', key='endianess', value=order)
            self.add_entry(fileFormat)

            if 'int' in dataType:
                data = np.round(data, 10)
            data_formatted = data.astype(dataType)
            assert abs(np.sum(data - data_formatted)) < 1e-10, \
                f"Can't format to dataType {dataType} without loss."

            # save data transposed because unisens reads rows*columns not columns*rows like numpy
            data_formatted.T.tofile(self._filename)
        else:
            raise ValueError('incompatible id: SignalEntry only allows for .bin or .csv format')

        self._set_channels(ch_names, n_data=len(data))

        if sampleRate is not None: self.set_attrib('sampleRate', sampleRate)
        assert 'sampleRate' in self.attrib, "Please specify sampleRate for correct visualization."
        if unit is not None: self.set_attrib('unit', unit)
        if comment is not None: self.set_attrib('comment', comment)
        if contentClass is not None: self.set_attrib('contentClass', contentClass)
        if adcZero is not None: self.set_attrib('adcZero', adcZero)
        if adcResolution is not None: self.set_attrib('adcResolution', adcResolution)
        if source is not None: self.set_attrib('source', source)
        if sourceId is not None: self.set_attrib('sourceId', sourceId)

        # set all other keyword arguments/comments as well.
        for key in kwargs:
            self.set_attrib(key, kwargs[key])

        self._autosave()
        return self


class CsvFileEntry(FileEntry):
    """
    A FileEntry that links a csv file.
    """

    def __init__(self, id=None, attrib=None, parent='.',
                 decimalSeparator='.', separator=';', **kwargs):
        super().__init__(id=id, attrib=attrib, parent=parent, **kwargs)
        assert decimalSeparator and separator, 'Must supply separators'

        if not self.id.endswith('csv'):
            logging.warning(f'id "{id}" does not end in .csv')

        csvFileFormat = MiscEntry('csvFileFormat', parent=self)
        csvFileFormat.set_attrib('decimalSeparator', decimalSeparator)
        csvFileFormat.set_attrib('separator', separator)
        self.add_entry(csvFileFormat)

    def set_data(self, data: list, **kwargs):
        """
        Set data of this csv object.


        Parameters
        ----------
        data : list
            the data as list or np array.
        **kwargs : str
            DESCRIPTION.
        """

        self._check_readonly()

        assert 'csvFileFormat' in self.__dict__, 'csvFileFormat information' \
                                                 'missing: No separator and decimal set'
        assert isinstance(data, (list, np.ndarray)), \
            f'data must be list of lists, is {type(data)}'
        sep = self.csvFileFormat.separator
        dec = self.csvFileFormat.decimalSeparator

        if len(data) == 0 or len(data[0]) < 2: logging.warning('Should supply at least two columns: ' \
                                                               'time and data')

        write_csv(self._filename, data, sep=sep, decimal_sep=dec)

        for key in kwargs:
            self.set_attrib(key, kwargs[key])
        self._autosave()
        return self

    def get_data(self, mode: str = 'list'):
        """
        Will try to load the csv data using a list, pandas or numpy.
        
        :param mode: select the return type
                     valid options: ['list', 'pandas', 'numpy']
        :returns: a list, dataframe or numpy array
        """
        sep = self.csvFileFormat.separator
        dec = self.csvFileFormat.decimalSeparator

        if mode in ('numpy', 'np', 'array'):
            lines = np.genfromtxt(self._filename, delimiter=sep,
                                  dtype=str)
        elif mode in ('pandas', 'pd', 'dataframe'):
            import pandas as pd
            lines = pd.read_csv(self._filename, sep=sep,
                                header=None, index_col=None)
        elif mode == 'list':
            lines = read_csv(self._filename, sep=sep, decimal_sep=dec,
                             convert_nums=True)
        else:
            raise ValueError('Invalid mode: {}, select from'
                             '["numpy", "pandas", "list"]'.format(mode))
        return lines

    def get_times(self):
        """
        Retrieves the times or samples of this CSV entry

        Returns
        -------
        times
            list of int or float denotating the times of the events
        """
        data = self.get_data()
        times, _ = zip(*data)
        return list(times)

    def get_labels(self):
        """
        Retrieves the labels this CSV entry

        Returns
        -------
        times
            list of int or float denotating the times of the events
        """
        data = self.get_data()
        _, labels = zip(*data)
        return list(labels)


class ValuesEntry(CsvFileEntry):
    """
    Hello, it's me, ValuesEntry
    
    :param test: test
    """

    def __init__(self, id=None, attrib=None, parent='.', **kwargs):
        super().__init__(id=id, attrib=attrib, parent=parent, **kwargs)

    def set_data(self, data: list, ch_names=None, **kwargs):
        # if we get a string supplied, we convert to list
        super().set_data(data, **kwargs)

        self._set_channels(ch_names, n_data=len(data[0]) - 1)

        self._autosave()
        return self


class EventEntry(CsvFileEntry):
    def __init__(self, id=None, attrib=None, parent='.', **kwargs):
        super().__init__(id=id, attrib=attrib, parent=parent, **kwargs)


class CustomEntry(FileEntry):

    def __init__(self, id=None, **kwargs):
        super().__init__(id=id, **kwargs)
        self._autosave()

    def get_data(self, dtype='auto'):
        """
        Will load the binary data of this CustomEntry.
        
        The following datatypes can be loaded automatically:
            text:  .txt .csv .ini
            image: .jpeg .jpg .bmp .png .tif .gif
            json:  .json (using json-tricks or json)
            numpy: .npy
            pickle: .pkl
            binary: anything else
        
        :param dtype: [binary, image, text, numpy, json]
        :returns: the binary data or the otherwise loaded data
        """

        if dtype == 'auto':

            ext = os.path.splitext(self._filename)[-1].lower()
            txt_exts = ['.txt', '.csv', '.ini']
            img_exts = ['.jpeg', '.jpg', '.bmp', '.png', '.tif', '.gif']

            if hasattr(self, 'dataType'):
                dtype = self.dataType
            elif ext in img_exts:
                dtype = 'image'
            elif ext in txt_exts:
                dtype = 'text'
            elif ext == '.json':
                dtype = 'json'
            elif ext == '.npy':
                dtype = 'numpy'
            elif ext == '.pkl':
                dtype = 'pickle'
            else:
                dtype = 'binary'

        if dtype == 'binary':
            with open(self._filename, 'rb') as f:
                data = f.read()
        elif dtype == 'csv':
            data = read_csv(self._filename)
        elif dtype == 'text':
            with open(self._filename, 'r') as f:
                data = f.read()
        elif dtype == 'image':
            imageio = get_module('imageio.v2')
            data = imageio.imread(self._filename)

        elif dtype == 'pickle':
            pickle = get_module('pickle')
            with open(self._filename, 'rb') as f:
                data = pickle.load(f)
        elif dtype == 'json':
            try:
                import json_tricks as json
            except:
                json = get_module('json')
            with open(self._filename, 'r') as f:
                data = json.load(f)
        elif dtype == 'numpy':
            data = np.load(self._filename)
        else:
            raise ValueError('unknown dtype {}'.format(dtype))

        self.dataType = dtype
        return data

    def set_data(self, data, dtype='auto', **kwargs):
        """
        Will save custom data to disk.
        
        :param data: the data to be saved to disc.
        :param dtype: binary or image.
        :returns: the binary data or an PIL.Image
        """
        self._check_readonly()

        # infer datatype automatically
        if dtype == 'auto':
            ext = os.path.splitext(self._filename)[-1].lower()
            txt_exts = ['.txt', '.ini', '.csv']
            img_exts = ['.jpeg', '.jpg', '.bmp', '.png', '.tif', '.gif']

            if ext in img_exts:
                dtype = 'image'
            elif ext in txt_exts:
                dtype = 'text'
            elif ext == '.json':
                dtype = 'json'
            elif ext == '.pkl':
                dtype = 'pickle'
            elif ext == '.npy':
                dtype = 'numpy'
            else:
                dtype = 'binary'

        # file saving from here on
        if dtype == 'binary':
            with open(self._filename, 'wb') as f:
                f.write(data)
        elif dtype == 'text':
            with open(self._filename, 'w') as f:
                f.write(data)
        elif dtype == 'image':
            imageio = get_module('imageio')
            imageio.imsave(self._filename, data)
        elif dtype == 'pickle':
            pickle = get_module('pickle')
            with open(self._filename, 'wb') as f:
                data = pickle.dump(data, f, protocol=3)
        elif dtype == 'json':
            try:
                import json_tricks as json
                tricks_installed = True
            except:
                json = get_module('json')
                tricks_installed = False
            with open(self._filename, 'w') as f:
                if tricks_installed:
                    json.dump(data, f, allow_nan=True)
                else:
                    json.dump(data, f)
        elif dtype == 'numpy':
            data = np.save(self._filename, data)
        else:
            raise ValueError('unknown dtype {}'.format(dtype))

        for key in kwargs:
            self.set_attrib(key, kwargs[key])

        # save dtype within the entry
        self.dataType = dtype

        self._autosave()
        return self


class CustomAttributes(Entry):
    def __init__(self, key: str = None, value: str = None, **kwargs):
        super().__init__(**kwargs)
        if key and value:
            self.set_attrib(key, value)

    def to_element(self):
        element = Element(self._name, attrib={})
        element.tail = '\n  \n  \n  '
        element.text = '\n'
        for key, value in self.attrib.items():
            subelement = Element('customAttribute', key=key, value=str(value))
            element.append(subelement)
        return element

    def add_entry(self, entry: MiscEntry):
        """ When reading the unisens.xml file, each CustomAttribute is an entry (i.e. subelement)
        to CustomAttributes and only contains key and value.
        In contrast, pyunisens will save a CustomAttribute as attribute to CustomAttributes"""
        assert entry._name == 'customAttribute', 'Can only add customAttribute type'
        self.set_attrib(entry.key, entry.value)
        self._autosave()


class MiscEntry(Entry):
    def __init__(self, name: str, key: str = None, value: str = None, **kwargs):
        """ For various smaller types of entries. The `name` describes the type and can be
        ['channel', 'context', 'customAttribute', 'group', 'groupEntry',
        'binFileFormat', 'csvFileFormat', 'customFileFormat']"""
        super().__init__(**kwargs)
        self._name = strip(name)
        if key and value:
            self.set_attrib(key, value)
        self._autosave()


class CustomAttribute(MiscEntry):
    """dummy class for reading from unisens.xml.
    An actual CustomAttribute is stored as attribute to CustomAttributes not as entry."""
    def __new__(*args, **kwargs):
        warnings.warn("CustomAttribute will be removed in the next release. "
                      "Use CustomAttributes.set_attrib('key', 'value') instead.",
                      category=DeprecationWarning, stacklevel=2)
        return MiscEntry('customAttribute', *args, **kwargs)
