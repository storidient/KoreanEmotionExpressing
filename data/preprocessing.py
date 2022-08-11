import re, unicodedata
from collections import defaultdict
from data.utils import Options, CleanWord, FilterWord
from cached_property import cached_property
from typing import List, Dict, Optional
from tqdm import tqdm

      
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
    output = re.sub('\</?(FL|sub)\>|<DR />', '', without_numbering)

    return self.del_space(output.split('<동의 관용구>')[0])


class CleanInfo:
  """
  Clean word information
  
  Attributes:
    input : a list of dictionaries with word information
    output : a list of dictionaries with cleaned word information
    save_options : save all the possible forms of a word
    allow_old : allow old Korean letters
    allow_broken : allow broken Korean letters
    del_overlapped : delete the overlapped words(same representation and definition)
  """
  def __init__(self, 
               input : List[Dict[str, str]], 
               save_options : bool = True,
               allow_old : bool = False, 
               allow_broken : bool = False,
               del_overlapped : bool = True):
    
    self.input = [] + input
    self._word_clean = ReviseRep(save_options).main
    self._def_clean = ReviseDef().main
    self._filter = FilterWord(allow_old, 
                            allow_broken).main
    self.output = self._build(del_overlapped)
  
  def _get_unit(self, item : Dict[str, str]) -> str:
    """Revise the word unit"""
    if item['pos'] == '구' or item['word_unit'] == '관용구':
      return '구'

    elif item['word_unit'] == '단어':
      return '어휘'

    else:
      return item['word_unit']

  def _get_pos(self, item):
    """Revise the part-of-speech"""
    if item['pos'] == '품사없음' and '어근' in item['definition']:
      return '어근'

    elif item['word_unit'] == '구':
      return '구'

    else:
      return item['pos']
  
  def _get_info(self, item : Dict[str, str]) -> Dict[str,str]:
    """Revise all the inforamtion about a word"""
    word, options = self._word_clean(item['word'])
    item['word'] = word

    if options != None:
      item['other_forms'] = '&'.join(set(options))
    
    item['definition'] = self._def_clean(item['definition'])
    item['word_unit'] = self._get_unit(item)
    item['pos'] = self._get_pos(item)

    return item
  
  @cached_property
  def word_zip(self):
    """Sort and zip all the word informtation to delete overlapped words"""
    output = defaultdict(list)

    for x in tqdm(self.input):
      if self._filter(x['word']):
        word_info = '#%#'.join(
            sorted([k + '%?%' + v for k,v in self._get_info(x).items() if k != 'source'])
            )
        output[word_info].append(x['source'])
    return output

  def _build(self, del_overlapped):
    if del_overlapped == True:
      output = list()

      for word_info, word_source in tqdm(self.word_zip.items()):
        info_list = [x.split('%?%') for x in word_info.split('#%#')]
        item_dict = {key : val for [key, val] in info_list}
        item_dict['source'] = '/'.join(set(word_source))
        output.append(item_dict)

      return output
    
    else:
      return [self._get_info(x) for x in tqdm(self.input) if self._filter(x['word'])]
