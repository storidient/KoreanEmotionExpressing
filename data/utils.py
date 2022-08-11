import re
from rx_codes import chinese_rx, blank_chinese, katakana_middle
from cached_property import cached_property
from typing import List, Dict, Optional
from itertools import product

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

      
      
      
class ReviseRep(CleanWord):
  def __init__(self, save_options : bool = True):
    super().__init__()
    self.save_options = save_options

  def space_option(self, word : str, options : Optional[List[str]] = None):
    """Change '^' into space or Delete '^' mark"""
    rep = re.sub('\^', ' ', word) #change into space
    with_space = re.sub('\^', '', word) #delete ^ mark
    if rep != word and self.save_options == True:
      options += [rep, with_space]
    return rep, options
  
  def word_option(self, phrase : str, options : Optional[List[str]] = None):
    """Delete '[Option1/Option2]' in the representation form"""
    rep = re.sub('\[[^\]]+\]', '', phrase)
    if self.save_options == True:
      if len(options) == 0:
        options.append(phrase)
      
      options = sum(list(map(lambda x : Options(x).output, options)), [])
    return rep, list(set(options))

  def josa_option(self, word : str, options : Optional[List[str]] = None):
    """Delete '(Option)' in the representation form (e.g. 밥(을) 먹다)"""
    rep = re.sub('\(.*\)', '', word)    
    
    if self.save_options == True:
      if len(options) == 0:
        options.append(word)
      
      without_josa = list(map(lambda x : re.sub('\(.*\)', '', x), options))
      with_josa = list(map(lambda x : re.sub('[\(\)]', '', x), options))
      options = without_josa + with_josa
    
    return rep, options

  def main(self, word : str) -> str:
    """revise word represetation form with all the rules"""
    rep = self.del_all(word)
    options = list() if self.save_options == True else None

    if re.match('.*\^', rep): #delete ^
      rep, options = self.space_option(rep, options)

    if re.match('.*\[.*\]', rep): #delete 
      rep, options = self.word_option(rep, options)

    if re.match('.*\(.*\)', rep):
      rep, options = self.josa_option(rep,options)
    
    rep = self.del_space(rep)
    
    if self.save_options == True:
      options = list(map(self.del_space, options))
      options.append(rep)

    return rep, options
