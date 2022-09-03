import re, unicodedata
from typing import List, Tuple, Union, Optional
from attr import define
from cached_property import cached_property
import numpy as np

def del_zeros(input_list : List[str]) -> List[str]:
  """Delete empty strings""" 
  return [_.strip(' ') for _ in input_list if len(_.strip(' ')) > 0]

def prevent_rx(input: str) -> str:
  #Prevent regex error
  for m in ['\[', '\]', '\.', '\!', '\?', '\^', '\(', '\)', '\-']:
    input = re.sub(m, m, input)
  return input

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
  def search(cls, mark_name : str):
    result = {k : v for k,v in cls.__dict__.items() if mark_name in k}
    if len(result) == 0:
      return None
    elif len(result) > 1:
      return result.values()
    else:
      return list(result.values())[0]
    
  @classmethod
  def ends(cls, mark : Optional[str] = None):
    output = [v.end for k,v in cls.__dict__.items() if k.startswith('b')]
    return output if mark == None else [x for x in output if mark not in x]

  @classmethod
  def starts(cls, mark : Optional[str] = None):
    output = [v.start for k,v in cls.__dict__.items() if k.startswith('b')]
    return output if mark == None else [x for x in output if mark not in x]  
  
  @classmethod
  def get_end(cls, start : str):
    output = [cls.end()[idx] for idx, item in enumerate(cls.start()) if item == start]
    return output[0] if len(output) > 0 else None 
  
  @classmethod
  def get_start(cls, end : str):
    output = [cls.start()[idx] for idx, item in enumerate(cls.end()) if item == end]    
    return output[0] if len(output) > 0 else None
  
old_kor_unicode = [('\u3164', '\u318c'),
                   ('\u318e', '\u318f'), 
                   ('\ua960', '\ua97f'),
                   ('\ud7b0', '\ud7ff'),
                   ('\ue000', '\uefff'),
                   ('\uf000', '\uffff'),
                   ('\u1113', '\u115f'),
                   ('\u1176', '\u11a7'),
                   ('\u11c3', '\u11ff')]

chinese_unicode = [('\u31c0', '\u31ef'),
                   ('\u31f0', '\u31ff'),
                   ('\u3200', '\u32ff'),
                   ('\u3300', '\u33ff'),
                   ('\u3400', '\u4dbf'),
                   ('\u4dc0', '\u4dff'),
                   ('\u4e00', '\u9fff'),
                   ('\uf900', '\ufaff')]

roman_num_unicode = [('\u2160', '\u217f')]

class RxCodes:
  def __init__(self):
    self.bracket = Brackets
    self.line = '\"[^"]+"|\'[^\']+\''
    self.indirect = ' ?((이?라|하)?[고|며|면서]|[라란] |하[는니였]|[한하](다| ?뒤)|할 )'
    self.end = '[\.\!\?]'
    self.chinese = self.rx_string(chinese_unicode)
    self.old_kor = self.rx_string(old_kor_unicode)
    self.roman_num = self.rx_string(roman_num_unicode)
    self.b_start = '[' + ''.join(Brackets.starts()) + ']'
    self.b_end = '[' + ''.join(Brackets.ends()) + ']'
    self.blank_chinese = '\u3000'
    self.katakana_middle = '\u30fb'
    self.quotation = '[“”"]'
    self.apostrophe = '[‘’\']'
    self.are_a = 'ㆍ'
    self.hyphen = '[─ㅡ⎯―\-ㅡ]'
    self.ellipsis = '\.\.\.+|‥+|…|⋯'
    self.english = '[A-Za-z]'
    self.html = '</?(a|a href|FL|img|ptrn|DR|sub|sup|equ|sp_|each_|span|br/?)([ =][^>]*)*>'
    self.number = '[0-9]'
    self.imperfect = '[ㄱ-ㅎㅏ-ㅣ]'
    self.sickles = '[' + ''.join(np.concatenate([[v.start, v.end] for v in Brackets.search('sickle')])) + ']'
    self.inequals = '[' + ''.join(np.concatenate([[v.start, v.end] for v in Brackets.search('inequal')])) + ']'
    self.wrong_q = '[\"\'][^가-힣]*[\.\?\,\!]'
    self.end_eomi = '[요라다까네]'
   
  @staticmethod
  def rx_string(unicode_list : List[Tuple[str, str]]) -> str:
    """Return regular expression string"""
    unicodes = ''.join(['%s-%s' % (s,t) for s, t in unicode_list])
    return '[' + unicodes +']'
  
  @staticmethod
  def build_rx(rx_str : Union[str, List[str]]):
    if type(rx_str) == list:
      rx_str = ''.join(rx_str)
    return re.compile(rx_str, re.UNICODE)

  def search_attr(self, name):
    return [v for k, v in self.__dict__.items() if name in k]

  def __getattr__(self, name):
    target = [v for k, v in self.__dict__.items() if re.sub('_all', '', name) in k]
      
    if name.endswith('_all'):
      target = self.search_attr(re.sub('_all', '', name))
      if len(target) > 0:
        component = [self.b_start, '?', target[0], '+ ?', target[0],  '*', self.b_end, '?']
        return self.build_rx(component)
      else:
        return None

    elif name.endswith('_bracket'):
      target = self.search_attr(re.sub('_bracket', '', name))
      if len(target) > 0:
        component = [self.b_start, target[0], '+ ?', target[0],  '*', self.b_end]
        return self.build_rx(component)
      else:
        return None

    elif name.endswith('_rx'):
      target = self.search_attr(re.sub('_rx', '', name))
      return self.build_rx(target) if len(target) > 0 else None
    
    elif name.endswith('_after'):
      target = self.search_attr(re.sub('_after', '', name))
      return self.build_rx('.*' + target) if len(target) > 0 else None

    elif name.startswith('bracket_'):
      target = re.sub('bracket_', '', name)
      return self.bracket.search(target) if len(target) > 0 else None

    else:
      return None
  
  
class CleanStr:
  rx = RxCodes()
  
  @classmethod
  def del_space(cls, item : str) -> str:
    """Delete unneccessary spaces in a word"""
    return re.sub(' +', ' ', item.strip())
  
  @classmethod
  def clear_html(cls, line : str):
    revised = re.sub(u'\xa0', ' ', re.sub('\n', ' ', line))
    output = re.sub('&gt;', "'", re.sub('&lt;', "'", revised))
    return cls.rx.html_rx.sub('', output)
  
  @classmethod
  def del_chinese(cls, line : str, extent : str = 'all'):
    output = cls.del_space(cls.rx.blank_chinese_rx.sub(' ', line))
    if extent == 'all':
      return cls.rx.chinese_all.sub('', output)

    else:
      return cls.rx.chinese_bracket.sub('', output) if extent == 'bracket' else output
  
  @classmethod
  def del_english(cls, line : str, extent : str = 'bracket'):
    if extent == 'all':
      return cls.rx.english_all.sub('', line)

    else:
      return cls.rx.english_bracket.sub('', line) if extent == 'bracket' else line
  
  @classmethod
  def del_imperfect(cls, line : str, extent : str = 'bracket'):
    if extent == 'all':
      return cls.rx.imperfect_all.sub('', line) 

    else:
      return cls.rx.imperfect_bracket.sub('', line) if extent == 'bracket' else line

  @classmethod
  def unify(cls, line, middle : bool = True, hyphen : bool = True,
            ellipsis : bool = True, quotation : bool = True, apostrophe : bool = True):
    """Unify different marks"""
    line = cls.rx.katakana_middle_rx.sub(cls.rx.are_a, line)
    
    if middle == True:
      line = cls.rx.are_a_rx.sub(',', line)
    
    if hyphen == True:
      line = cls.rx.build_rx([cls.rx.hyphen, '+']).sub('-', line)
    
    if ellipsis == True:
      line = cls.rx.ellipsis_rx.sub('⋯', line)

    if quotation == True:
      line = cls.rx.quotation_rx.sub('"', line)
      
    if apostrophe == True:
      line = cls.rx.apostrophe_rx.sub("'", line)
      
    return line
