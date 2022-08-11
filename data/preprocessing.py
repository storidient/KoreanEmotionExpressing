import re
from data.utils import Options, CleanWord
from cached_property import cached_property
from typing import List, Dict, Optional

      
class ReviseRep(CleanWord):
  """Revise the representation form of a word
  
  Attributes:
    save_options: whether to return a list of all the possible forms or not
                  (e.g. '밥(을) 먹다' -> ['밥 먹다', '밥을 먹다'])
   """
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
      
      options = list(set(
        sum(list(map(lambda x : Options(x).output, options)), [])
      ))
      
    return rep, options

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


class ReviseDef(CleanWord):
  def __init__(self):
    super().__init__()
  
  def del_numbering(self, item):
    """delete numbers with the word representation
    (e.g. '‘단어01’의 준말')"""
    targets = re.findall("['‘][가-힣]+[0-9]+[’']", item)
    for target in targets:
      without_num = re.sub('[0-9]+', '', target)
      item = re.sub(target, without_num, item)
    
    return re.sub('[\[「][0-9]+[\]」]', '', item)
  
  def main(self, item : str) -> str:
    """Delete all the unneccessary marks in word definition"""
    without_chinese = self.del_chinese(item)
    without_roman = self.roman_bracket.sub('', without_chinese)
    without_numbering = self.del_numbering(without_roman)

    return re.sub('\</?(FL|sub)\>|<DR />', '', without_numbering)
