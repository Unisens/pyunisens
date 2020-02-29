# -*- coding: utf-8 -*-
"""
Created on Mon Jan  6 21:16:58 2020

some helper functions

@author: skjerns
"""
import numpy as np
from collections import OrderedDict


# a helper function for anti-camel case first letter


lowercase = lambda s: s[:1].lower() + s[1:] if s else ''



def num2str(element, decimal_sep):
    """
    A helper function that converts strings to numbers if possible
    and replaces the float decimal separator with the given value
    """
    if isinstance(element, float):
        return str(element).replace('.', decimal_sep)
    return str(element)
    
def str2num(string, decimal_sep):
    """
    A helper function that converts numbers to strings if possible
    and replaces the float decimal separator with the given value
    """
    if string.isdigit(): return int(string)
    try: return float(string.replace(decimal_sep, '.'))
    except: return string
    
    
def write_csv(csv_file, data_list, sep=';', decimal_sep='.', comment=None):
    """
    Parameters
    ----------
    csv_file : str
        a filename.
    data_list : list
        a list of list. each list is a new line, 
        each list of list is an entry there.
    sep : str, optional
        the separator to be used. The default is ';' (excel standard).
    decimal : str, optional
        the decimal separator to be used. The default is '.'.
    comment : str, optional
        a comment that will be inserted to the beginning, starting with #
        
    Returns
    -------
    lines : TYPE
        DESCRIPTION.

    """
    # we accept data_lists or arrays
    assert decimal_sep!=sep, 'Error, sep cannot be same as decimal_sep'
    assert isinstance(data_list, (list, np.ndarray)), 'Must be list or array'
    if isinstance(data_list, np.ndarray):
        if data_list.ndim==1:
            data_list = [line for line in data_list]
        elif data_list.ndim==2:
            data_list = [[x for x in d] for d in data_list]
        else:
            raise ValueError('Array must be 1D or 2D')

    # first add the comments if there are any
    csv_string = '' 
    if comment is not None:
        comment = comment.split('\n')
        csv_string += '# ' + '\n# '.join(comment) + '\n'
    
    # now go through the data list or array.
    for line in data_list:
        # if it contains several elements, we separate them with sep.
        # additionally we convert the decimal separator
        if isinstance(line, (list, np.ndarray)):            
            csv_string += sep.join([num2str(e, decimal_sep)for e in line])
        # if it's not a list, we just convert to string
        else:
            csv_string += num2str(line, decimal_sep)
        csv_string += '\n'

    with open(csv_file, 'w') as f:
        f.write(csv_string)
    return True

def read_csv(csv_file, comment='#', sep=';', decimal_sep='.',
             convert_nums=True, keep_empty=False):
    """
    simply load an csv file with a separator and newline as \\n
    comments are annotated as starting with # and are removed
    empty lines are removed
    
    :param csv_file: a csv file to load
    :param sep: set a different separator. this is language specific
    :param comment: lines starting with this sign will be ignored
    :param convert_nums: convert numbers to int and float automatically
    """
    with open(csv_file, 'r') as f:
        content = f.read()
        
    # split in lines
    lines = content.split('\n')
    
    # ignore comments and remove whitespaces
    lines = [line.strip() for line in lines if not line.startswith(comment)]
    
    # remove empty lines
    if not keep_empty:
        lines = [line for line in lines if (line!='' and line!=[])]
    
    # split into subentries and strip of whitespaces
    lines = [[el.strip() for el in line.split(sep)] for line in lines]
    
    # remove empty last element
    if not keep_empty:
        for i, line in enumerate(lines):
            if line[-1]=='': lines[i] = line[:-1]

    # convert to numbers if requested
    if convert_nums:
        lines = [[str2num(e, decimal_sep=decimal_sep) for e in line] \
                 for line in lines]
    return lines


class AttrDict(OrderedDict):
    """
    A dictionary that is ordered and can be accessed 
    by both dict[elem] and by dict.elem
    """

    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
        

def make_key(string:str):
    """
    A function that turns any string into a valid python variable string

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

def strip(string):
    """
    Strip a unisense identifier string of unnecessary elements
    such as version string {https://www.unisens.org/unisens2.0}
    """
    if '}' in string:
        string = string.split('}')[-1]
    return string   