import re, unicodedata
from typing import List, Tuple, Union, Optional
from attr import define
from cached_property import cached_property
import numpy as np


OLD_KOR_UNICODE = [('\u3164', '\u318c'),
                   ('\u318e', '\u318f'), 
                   ('\ua960', '\ua97f'),
                   ('\ud7b0', '\ud7ff'),
                   ('\ue000', '\uefff'),
                   ('\uf000', '\uffff'),
                   ('\u1113', '\u115f'),
                   ('\u1176', '\u11a7'),
                   ('\u11c3', '\u11ff')]

CHINESE_UNICODE = [('\u31c0', '\u31ef'),
                   ('\u31f0', '\u31ff'),
                   ('\u3200', '\u32ff'),
                   ('\u3300', '\u33ff'),
                   ('\u3400', '\u4dbf'),
                   ('\u4dc0', '\u4dff'),
                   ('\u4e00', '\u9fff'),
                   ('\uf900', '\ufaff')]

ROMAN_NUM_UNICODE = [('\u2160', '\u217f')]

JAPANESE_UNICODE = [('\u3040', '\u309F'),
                    ('\u30A0', '\u30FF')]

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
  

class RxCodes:#TODO
  def __init__(self):
    """All the Regex strings"""
    self.english, self.number, self.imperfect = '[A-Za-z]', '[0-9]', '[ㄱ-ㅎㅏ-ㅣ]'
    self.chinese = self.rx_string(CHINESE_UNICODE)
    self.old_kor = self.rx_string(OLD_KOR_UNICODE)
    self.japanese = self.rx_string(JAPANESE_UNICODE)
    self.roman_num = self.rx_string(ROMAN_NUM_UNICODE)
    self.blank_ch, self.katakana_middle, self.are_a ='\u3000', '\u30fb', '\u318D'
    self.html = '</?(' + self._wrap(['a','a href','FL','img', 'ptrn', 'DR', 'sub', 'sup',
                                    'equ','sp_', 'each_', 'span', 'br']) + ')([ =/][^>]*)*>'
    self.end, self.endwithcomma = self._wrap(['\.', '\!', '\?']), self._wrap(['\.', '\!', '\?', ','])
    self.quotation, self.apostrophe = self._wrap(['“', '”', '"']), self._wrap(['‘', '’',  "'"])
    self.hyphen = self._wrap(['\u2500', '\u3161', '\u23af', '\u2015', '\-'])
    self.ellipsis = self._wrap(['\.\.\.+', '‥+', '…', '⋯'])
    self.line = self._wrap(['"[^"]+"', "'[^\']+'"])
    self.indirect = self._wrap([' ?(이?라|하)?[고|며|면서]',
                                ' ?이?[라란] ',
                                ' ?하([는니] |였?다)',
                                ' ?할 ',
                                ' ?한([다 ]| 뒤)'])
    self.bracket, self.b_start, self.b_end = Brackets, self._wrap(Brackets.starts()), self._wrap(Brackets.ends())
    self.sickles = self._wrap(np.concatenate([[v.start, v.end] for v in Brackets.search('sickle')]))
    self.inequals = self._wrap(np.concatenate([[v.start, v.end] for v in Brackets.search('inequal')]))
    self.wrong_q = '\"[^가-힣ㄱ-ㅎㅏ-ㅣA-Za-z]*' + self.endwithcomma + '\"?'
    self.eomi = '[요라다까네야오구]'
  
  @staticmethod
  def rx_string(unicode_list : List[Tuple[str, str]]) -> str:
    """Return regular expression string"""
    unicodes = ''.join(['%s-%s' % (s,t) for s, t in unicode_list])
    return '[' + unicodes +']'
  
  @staticmethod
  def build_rx(rx_str : Union[str, List[str]]):
    """Compile regular expression string"""
    return re.compile(''.join(rx_str), re.UNICODE) if type(rx_str) == list else re.compile(rx_str, re.UNICODE)

  def _wrap(self, input : List[str]):
    """Wrap codes into a regex form"""
    return '|'.join(input) if len([_ for _ in input if len(_) > 2]) > 0 else '[' + ''.join(input) + ']'

  def _search_attr(self, name : str):
    """Search attributes in this class and return the values"""
    return [v for k, v in self.__dict__.items() if name in k]
 
  def _add_b(self, input : str, with_all : bool = False):
    """Add brackets to the input, and compile the regex string"""
    target = ''.join([self.b_start, '[\W_]*', input, '+[\W_]*', input,  '*', self.b_end])
    return self.build_rx(self._wrap([target, input])) if with_all == True else self.build_rx(target)
  
  def __getattr__(self, name):
    if name.endswith('_all'):
      target = self._search_attr(re.sub('_all', '', name))
      return self._add_b(target[0], True) if len(target) > 0 else None
    
    if name.endswith('_bracket'):
      target = self._search_attr(re.sub('_bracket', '', name))
      return self._add_b(target[0]) if len(target) > 0 else None

    elif name.endswith('_rx'):
      target = self._search_attr(re.sub('_rx', '', name))
      return self.build_rx(target[0]) if len(target) > 0 else None

    elif name.startswith('bracket_'):
      target = re.sub('bracket_', '', name)
      return self.bracket.search(target) if len(target) > 0 else None

    else:
      return None
  
  
class CleanStr:
  rx = RxCodes()
  
  @classmethod
  def del_space(cls, item : str) -> str:
    """Delete unneccessary spaces in a line"""
    return re.sub(' +', ' ', item.strip())
  
  @classmethod
  def clear_html(cls, line : str):
    """Delete html tags in a line"""
    revised = re.sub(u'\xa0', ' ', re.sub('\n', ' ', line))
    output = re.sub('&gt;', "'", re.sub('&lt;', "'", revised))
    return cls.rx.html_rx.sub('', output)
  
  @classmethod
  def del_chinese(cls, line : str, extent : str = 'all'):
    """Delete Chinese letters in a line"""
    revised = cls.del_space(cls.rx.blank_ch_rx.sub(' ', line))
    if extent == 'all':
      return cls.rx.chinese_all.sub('', revised)
    else:
      return cls.rx.chinese_bracket.sub('', revised) if extent == 'bracket' else revised
  
  @classmethod
  def del_english(cls, line : str, extent : str = 'bracket'):
    """Delete English letters in a line"""
    if extent == 'all':
      return cls.rx.english_all.sub('', line)
    else:
      return cls.rx.english_bracket.sub('', line) if extent == 'bracket' else line
    
  @classmethod
  def del_japanese(cls, line : str, extent : str = 'all'):
    """Delete Japanese letters in a line"""
    if extent == 'all':
      return cls.rx.japanese_all.sub('', line)
    else:
      return cls.rx.japanese_bracket.sub('', line) if extent == 'bracket' else line
  
  @classmethod
  def del_imperfect(cls, line : str, extent : str = 'bracket'):
    """Delete imperfect Korean letters in a line"""
    if extent == 'all':
      return cls.rx.imperfect_all.sub('', line)
    else:
      return cls.rx.imperfect_bracket.sub('', line) if extent == 'bracket' else line
  
  @classmethod
  def del_empty_bracket(cls, line: str):
    return cls.rx.build_rx([cls.rx.b_start, ' *', cls.rx.b_end]).sub('', line)
  
  @classmethod
  def unify(cls, line, 
            middle : bool = True, 
            hyphen : bool = True,
            ellipsis : bool = True, 
            quotation : bool = True, 
            apostrophe : bool = True):
    """Unify middle, hyphen, ellipsis, quotation, apostrophe marks"""
    k_unified = cls.rx.katakana_middle_rx.sub(cls.rx.are_a, line)
    mid_unified = cls.rx.are_a_rx.sub(',', k_unified) if middle == True else k_unified
    h_unified = cls.rx.build_rx([cls.rx.hyphen, '+']).sub('-', mid_unified) if hyphen == True else mid_unified
    e_unified = cls.rx.ellipsis_rx.sub('⋯', h_unified) if ellipsis == True else h_unified
    q_unified = cls.rx.quotation_rx.sub('"', e_unified) if quotation == True else e_unified
    return cls.rx.apostrophe_rx.sub("'", q_unified) if apostrophe == True else q_unified
