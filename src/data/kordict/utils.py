import re, unicodedata
from collections import defaultdict
from cached_property import cached_property
from data.rx_codes import *
from typing import List, Dict
from itertools import product
import numpy as np

def list2str(input : List[Dict[str, str]]) -> str:
  """Split a string in a list and delete the overlapped items """
  output = np.concatenate([x.split('/') for x in input])
  without_zero = [x.strip(' ') for x in output if len(x. strip(' ')) > 0]
  return '/'.join(set(without_zero))


class Options:
  """
  Change the representation form with [/] into a list of all the possible forms
  
  Attributes: 
    input : a representation with [', ']' and '/' (e.g. 밥[빵/국]을 먹다)
    output : a list of all the possible forms (e.g.['밥을 먹다', '빵을 먹다, '국을 먹다'])
  """
  def __init__(self, phrase : str):
    self.input, self.output = phrase, list()
    self._build()
  
  @cached_property
  def targets(self):
    """Returns a range matched with 'OptionOne[OptionTwo/OptionThree]'"""
    return re.findall('[^ ]*\[[^\]]+\]', self.input)

  @cached_property
  def options(self):
    """Returns a list of options"""
    return list(map(self.split_option, self.targets))

  def split_option(self, target : str) -> List[str]:
    """Change a string with [] into a list"""
    items = re.split('[\[\/]', re.sub('\]', '', target))
    return [x for x in items if len(x.strip(' ')) > 0]
  
  def _build(self):
    all_combination = list(product(*self.options))
    
    for option_set in all_combination:
      possible_form = '' + self.input #copy the original form

      for idx, target in enumerate(self.targets):
        target = re.sub('\]', '\]', re.sub('\[', '\[', target))
        possible_form = re.sub(target, option_set[idx], possible_form)
      
      self.output.append(possible_form)
      
      
class CleanWord:
  """Delete unneccessary marks in a word
  Attributes:
    chinese_rx : the regular expression of Chinese letters
    blank_chinese : the regular expression of 'blank' in Chinese letters
    katakana_middle : the regular expression of 'ㆍ' in Japanese(Katakana) letters
  """
  def __init__(self):
    self.chinese_rx = chinese_rx
    self.blank_chinese = blank_chinese
    self.katakana_middle = katakana_middle
    self.roman_bracket = roman_bracket
    self.ch_with_bracket = re.compile('[\(\[]' + build_rx(chinese_unicode) + '+[\)\]]', re.UNICODE)
    self.roman_bracket = roman_bracket
  
  def del_chinese(self, item : str) -> str:
    """Delete the Chinese letters and empty brackets (e.g. '[]', '()')"""
    return self.chinese_rx.sub('', item)
  
  def del_chinese_bracket(self, item : str) -> str:
    """Delete the Chinese letters and empty brackets (e.g. '[]', '()')"""
    return self.ch_with_bracket.sub('', item)
  
  def del_english(self, item : str) -> str:
    """Delete the English letters and empty brackets (e.g. '[]', '()')"""
    return re.sub('[\(\[][ A-Za-z]+[\(\]]', '', item)
    
  def del_space(self, item : str) -> str:
    """Delete unneccessary spaces in a word"""
    return re.sub(' +', ' ', item.strip())
  
  def del_all(self, word : str) -> str:
    """Delete all the unneccessary marks
    (e.g. Arabian numbers, under-bar, chinese letters, hyphen, end marks)
    """
    word = unicodedata.normalize('NFC', word)
    without_chinese = self.blank_chinese.sub(' ', self.del_chinese(word))
    without_katakana = self.katakana_middle.sub('ㆍ', without_chinese)   
    without_roman = self.roman_bracket.sub('', without_katakana)
    without_numbering = re.sub('[\[「]]?[0-9]+[\]」]?', '', without_roman)
    
    return re.sub('[\.,\-_]', '', without_numbering)


class FilterWord:
  """Filter the words

    Attributes:
      allow_old : allow old Korean letters
      allow_broken : allow broken Korean letter
  """
  def __init__(self, 
               allow_old : bool = False,
               allow_broken : bool = False):
    self.allow_old = allow_old
    self.allow_broken = allow_broken #allow
    self._build()
  
  def _build(self):
    if self.allow_old == False:
      from data.rx_codes import old_kor_rx
      self.old_kor_rx = old_kor_rx

    if self.allow_broken == False:
      self.broken_kor_rx = re.compile('^[ㄱ-ㅎㅏ-ㅣ]')

  def run(self, item : str) -> bool:
    item = unicodedata.normalize('NFC', item)

    if self.allow_old == False:
      if self.old_kor_rx.match(item):
        return False

    if self.allow_broken == False:
      if self.broken_kor_rx.match(item):
        return False

    return True
