# -*- coding: utf-8 -*-
"""
Created on Mon Jan  6 21:16:58 2020

@author: skjerns
"""

from collections import OrderedDict

class AttrDict(OrderedDict):
    """
    A dictionary that is ordered and can be accessed 
    by both dict[elem] and by dict.elem
    """

    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
        
        
        
    # def __setattr__(self, item, value):
    #     return self.__setitem__( item, value)
    # def __getitem__(self, item, value):
    #     return self.__item__(item, value)
    
    # def __setitem__(self, item, value):
    #     print(4444444444)
    #     allowed = ''.join([str(chr(char)) for char in range(97,123)])
    #     allowed += ''.join([str(chr(char)).upper() for char in range(97,123)])
    #     allowed += ''.join([str(x) for x in  range(10)])
    #     reserved = ['False','def','if','raise','None','del','import','return',
    #                 'True','elif','in','try','and','else','is','while','as',
    #                 'except','lambda','with','assert','finally','nonlocal',
    #                 'yield','break','for','not','','class','from','or','',
    #                 'continue','global','pass']
    #     item = str(item)
    #     for char in item:
    #         if char not in allowed:
    #             item = item.replace(char, '_')
    #     if item in reserved:
    #         item += '_'
    #     print(item, value)
    #     OrderedDict.__setitem__(self, item, value)