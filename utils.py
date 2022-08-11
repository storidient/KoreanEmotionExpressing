import re
from rx_codes import *

class CleanWord:
  """Delete all the unneccessary marks in a word

  Attributes:
    chinese_rx : the regular expression of Chinese letters
    blank_chinese : the regular expression of 'blank' in Chinese letters
    katakana_middle : the regular expression of 'ㆍ' in Japanese(Katakana) letters
  """
  def __init__(self):
    self.chinese_rx = chinese_rx
    self.blank_chinese = blank_chinese
    self.katakana_middle = katakana_middle
  
  def del_chinese(item : str) -> str:
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
