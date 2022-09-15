import re
from typing import List, Dict, Optional, Union
from src.data.utils import ROMAN_NUM_UNICODE, CHINESE_UNICODE, CleanStr
from jamo import h2j, j2hcj
from cached_property import cached_property
from boltons.iterutils import pairwise
from itertools import product
from jamo import j2hcj, h2j


EOMI = 'ㅕㅓㅏㅑㅘㅝㅐㅒㅖㅔ'
NUMBERS =  '[' + '0-9' + ''.join(['%s-%s' % (s,e) for s,e in ROMAN_NUM_UNICODE]) + ']'
CHINESE_ENGLISH =  '[A-Za-z' + ''.join(['%s-%s' % (s,e) for s,e in CHINESE_UNICODE]) + ']'


def clean_conju(item : List[Dict[str, str]]) -> str:
  c, a, i= 'conjugation', 'abbreviation', '_info'
  output = [[x[c + i][c], x[a + i][a] if a + i in x.keys() else None] for x in item]
  output = list(filter(lambda x : j2hcj(h2j(x[0]))[-1] in EOMI, output))
  output = sorted(list(filter(None, sum(output, []))), key = lambda x : len(x)) 
  return output[0] if len(output) > 0 else ''
  
  
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
 

class CleanRepr:
  """Revise the representation form of a word
  
  Attributes:
    save_options: whether to return a list of all the possible forms or not
                  (e.g. '밥(을) 먹다' -> ['밥 먹다', '밥을 먹다'])
   """
  def __init__(self, save_options : bool = True):
    self.save_options = save_options

  def space_option(self, 
                   word : str, 
                   options : Optional[List[str]] = None):
    """Change '^' into space or Delete '^' mark"""
    rep = re.sub('\^', ' ', word) #change into space
    with_space = re.sub('\^', '', word) #delete ^ mark
    if rep != word and self.save_options == True:
      options += [rep, with_space]
    
    return rep, options
  
  def word_option(self, 
                  phrase : str, 
                  options : Optional[List[str]] = None):
    """Delete '[Option1/Option2]' in the representation form"""
    rep = re.sub('\[[^\]]+\]', '', phrase)
    if self.save_options == True:
      if len(options) == 0:
        options.append(phrase)
      
      option_list = list(map(lambda x : Options(x).output, options))
      options = list(set(sum(option_list, [])))
      
    return rep, options

  def josa_option(self, 
                  word : str, 
                  options : Optional[List[str]] = None):
    """Delete '(Option)' in the representation form (e.g. 밥(을) 먹다)"""
    rep = re.sub('\([^\)]*\)', '', word)  
    if self.save_options == True:
      if len(options) == 0:
        options.append(word)
      
      without_josa = list(map(lambda x : re.sub('\([^\)]*\)', '', x), options))
      with_josa = list(map(lambda x : re.sub('[\(\)]', '', x), options))
      options = without_josa + with_josa
  
    return rep, options
  
  def run(self, input) -> str:
    """revise word represetation form with all the rules"""
    rep = re.sub('[0-9\-]', '', input)
    options = list() if self.save_options == True else None

    if re.match('.*\^', rep): #delete ^
      rep, options = self.space_option(rep, options)

    if re.match('.*\[.*\]', rep): #delete 
      rep, options = self.word_option(rep, options)

    if re.match('.*\(.*\)', rep):
      rep, options = self.josa_option(rep,options)
    
    if self.save_options == True:
      options += [rep]
      options = list(map(lambda x : re.sub(' +', ' ', x.strip(' ')), options))
      options = list(set(options))
      
    return re.sub(' +', ' ', rep.strip(' ')), options
