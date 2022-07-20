'''
This module contains data structure for
  - SIR instructions
  - SSA instructions
'''

class Instr:
  '''
  Data structure for handling sir and ssa instruction
  '''

  def __init__(self, code, typ, **kwargs):
    assert 'code' not in kwargs
    assert 'typ'  not in kwargs

    self.__dict__ = kwargs
    self.code     = code
    self.typ      = typ
  
  def to_human_readable_sir(self):
    '''
    This function returns a representation of the instruction formatted as 'code typ argN=...'
    '''

    kwargs = ", ".join(f"{k}={repr(self.__dict__[k])}" for k in filter(lambda k: k not in ["code", "typ"], self.__dict__.keys()))
    return f'{self.code} {self.typ} {kwargs}'

class Label:
  '''
  Data structure for handling a sir label
  '''

  def __init__(self, name):
    self.name = name
  
  def __eq__(self, r):
    return isinstance(r, Label) and self.name == r.name
  
  def to_human_readable_sir(self):
    return f'{self.name}:'