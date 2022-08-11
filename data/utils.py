import re
from cached_property import cached_property
from data.rx_codes import *
from typing import List
from itertools import product

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
  
  def del_chinese(self, item : str) -> str:
    """Delete the Chinese letters and empty brackets (e.g. '[]', '()')"""
    return re.sub('[\[\(][\]\)]', '', self.chinese_rx.sub('', item))

  def del_space(self, item : str) -> str:
    """Delete unneccessary spaces in a word"""
    return re.sub(' +', ' ', item.strip())
  
  def del_all(self, word : str) -> str:
    """Delete all the unneccessary marks
    (e.g. Arabian numbers, under-bar, chinese letters, hyphen, end marks)
    """
    without_chinese = self.blank_chinese.sub(' ', self.del_chinese(word))
    without_underbar = re.sub('_', ' ', without_chinese)
    without_katakana = self.katakana_middle.sub('ㆍ', without_underbar)    
    
    return re.sub('[\.,0-9\-]', '', without_katakana)
