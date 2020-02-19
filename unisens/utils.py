# -*- coding: utf-8 -*-
"""
Created on Mon Jan  6 21:16:58 2020

some helper functions

@author: skjerns
"""

from collections import OrderedDict


# a helper function for anti-camel case first letter


lowercase = lambda s: s[:1].lower() + s[1:] if s else ''

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