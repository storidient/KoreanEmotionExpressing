import re
from typing import List, Tuple, Union, Optional
from attr import define
import numpy as np

ROMAN_NUM_UNICODE = '[\u2160-\u217f]'

JAPANESE_UNICODE = '[\u3040-\u309F\u30A0-\u30FF]'

OLD_KOR_UNICODE = '['+ ''.join(['%s-%s' % (s, e) for s, e in [('\u3164', '\u318c'),
                                                              ('\u318e', '\u318f'), 
                                                              ('\ua960', '\ua97f'),
                                                              ('\ud7b0', '\ud7ff'),
                                                              ('\ue000', '\uefff'),
                                                              ('\uf000', '\uffff'),
                                                              ('\u1113', '\u115f'),
                                                              ('\u1176', '\u11a7'),
                                                              ('\u11c3', '\u11ff')]]) + ']'
                                
CHINESE_UNICODE = '[' + ''.join(['%s-%s' % (s, e) for s, e in [('\u31c0', '\u31ef'),
                                                               ('\u31f0', '\u31ff'),
                                                               ('\u3200', '\u32ff'),
                                                               ('\u3300', '\u33ff'),
                                                               ('\u3400', '\u4dbf'),
                                                               ('\u4dc0', '\u4dff'),
                                                               ('\u4e00', '\u9fff'),
                                                               ('\uf900', '\ufaff')]]) + ']'

INDIRECT = ' ?' + '(' + '|'.join(['(이?라|하)?(고|며 |면[서은]?는? )',
                                  '이?[라란] ',
                                  '하([는나] |였?([다던]|으나)|기에?는|여도? |[더자]?니 |자(마자)? )',
                                  '할 ',
                                  '한(다| 뒤?)']) + ')'

HTML = '</?(a|a href|FL|img|ptrn|DR|sub|sup|equ|sp_|each_|span|br)([ =/][^>]*)*>'

def del_zeros(input_list : List[str]) -> List[str]:
  """Delete empty strings""" 
  return [_.strip(' ') for _ in input_list if len(_.strip(' ')) > 0]

def prevent_rx(input: str) -> str:
  #Prevent regex error
  for m in ['\[', '\]', '\.', '\!', '\?', '\^', '\(', '\)', '\-']:
    input = re.sub(m, m, input)
  return input

def build_rx(input : Union[str, List[str]], rx : bool = True):
  """Compile regular expression string"""
  if type(input) == list:
    input = '(' + '|'.join(input) + ')' if len(list(filter(lambda x : len(x) > 2, input))) > 0 else '[' + ''.join(input) + ']'
  return re.compile(input, re.UNICODE) if rx == True else input

@define
class B:
  start : str
  end : str

class Brackets:
  b_small = B('\(', '\)')
  b_inequal_a = B('<', '>')
  b_inequal_b = B('〈','〉')
  b_middle_a = B('\[','\]')
  b_middle_b = B('〔', '〕')
  b_big = B('{', '}')
  b_sickle = B('「', '」')
  b_double_sickle = B('『','』')
  b_double_inequal = B('《', '》')
    
  @classmethod
  def ends(cls, mark : Optional[str] = None):
    output = [v.end for k,v in cls.__dict__.items() if k.startswith('b')]
    return output if mark == None else [x for x in output if mark not in x]

  @classmethod
  def starts(cls, mark : Optional[str] = None):
    output = [v.start for k,v in cls.__dict__.items() if k.startswith('b')]
    return output if mark == None else [x for x in output if mark not in x]  
  
  @classmethod
  def search(cls, mark_name : str):
    result = {k : v for k,v in cls.__dict__.items() if mark_name in k}
    if len(result) == 0:
      return None
    
    elif len(result) > 1:
      return result.values()
    
    else:
      return list(result.values())[0]

    
class CleanStr:
  blank_ch, katakana_mid, are_a = '\u3000', '\u30fb', '\u318D'
  quotation, apostrophe = '[“”"]', "[‘’']"
  hyphen = '[\u2500\u3161\u23af\u2015\u2014\-]+'
  ellipsis = '\.\.\.+|‥+|…|⋯'
  b_start = build_rx(Brackets.starts(), False)
  b_end = build_rx(Brackets.ends(), False)
  
  @staticmethod
  def del_space(item : str) -> str:
    """Delete unneccessary spaces in a line"""
    return re.sub(' +', ' ', item.strip())
  
  @staticmethod
  def clear_html(line : str) -> str:
    """Delete html tags in a line"""
    revised = re.sub(u'\xa0', ' ', re.sub('\n', ' ', line))
    output = re.sub('&gt;', "'", re.sub('&lt;', "'", revised))
    return re.sub(HTML, '', output)
   
  @classmethod
  def del_empty(cls, line : str) -> str:
    """Delete empty brackets in a line"""
    return re.sub(cls.b_start + ' *' + cls.b_end, '', line)
 
  @classmethod
  def rx_bracket(cls, rx_str_list : List[str]) -> str:
    """Return the input items surrounded with brackets"""
    input = build_rx(rx_str_list, False)
    if len(input) > 0:
      input += '+'
    return cls.b_start + '[\W_]*' + input + '[\W_]*' + cls.b_end
  
  @classmethod
  def unify(cls, line : str) -> str:
    """Unify middle, hyphen, ellipsis, quotation, apostrophe marks"""   
    line = re.sub(cls.blank_ch, ' ', line)
    line = re.sub('[' + cls.katakana_mid + cls.are_a + ']', ',', line)
    line = re.sub(cls.hyphen, '-', line)
    line = re.sub(cls.ellipsis, '⋯', line)
    line = re.sub(cls.quotation, '"', line)
    return re.sub(cls.apostrophe, "'", line)   
