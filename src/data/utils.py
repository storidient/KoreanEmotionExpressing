import re
from typing import List, Tuple, Union
from attr import define
from cached_property import cached_property

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
  b_double_sicke = B('『','』')
  b_double_inequal = B('《', '》')
  b_wrong = B('&lt;', '&gt;')

  @classmethod
  def search(cls, mark_name):
    result = {k : v for k,v in cls.__dict__.items() if mark_name in k}
    if len(result) == 0:
      return None
    elif len(result) > 1:
      return result.values()
    else:
      return list(result.values())[0]
  
  @classmethod
  def excldue(cls, mark_name : Union[List[str], str]):
    if type(mark_name) == list:
      result = dict()
      for m in mark_name:
        for k, v in cls.__dict__.items():
          if m not in k and k.starswith('b_'):
            result[k] = v
      return result.values()
  
    else:
      return {k : v for k, v in cls.__dict__.items() if mark_name not in k and k.starswith('b_')}.values()
    
  @classmethod
  def ends(cls):
    return [v.end for k,v in cls.__dict__.items() if k.startswith('b')]

  @classmethod
  def starts(cls):
    return [v.start for k,v in cls.__dict__.items() if k.startswith('b')]
  
  @classmethod
  def get_end(cls, start):
    output = [cls.end()[idx] for idx, item in enumerate(cls.start()) if item == start]
    return output[0] if len(output) > 0 else None 
  
  @classmethod
  def get_start(cls, end):
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
    self.blank_chinese = self.build_rx('[\u3000]')
    self.katakan_middle = self.build_rx('[\u30fb]')
    self.quotation = '[“”"]'
    self.apostrophe = '[‘’\']'
    self.are_a = '[ㆍ]'
    self.hyphen = '[─ㅡ⎯―\-]'
    self.ellipsis = '\.\.\.+|‥+|…|⋯'
    self.english = '[A-Za-z]'

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
      return self.build_rx([self.b_start,'?',target[0], self.b_end, '?']) if len(target) > 0 else None
    
    elif name.endswith('_bracket'):
      target = self.search_attr(re.sub('_bracket', '', name))
      return self.build_rx([self.b_start,target[0], self.b_end]) if len(target) > 0 else None

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
