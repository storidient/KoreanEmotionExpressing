import re, unicodedata
from collections import defaultdict
from src.data.utils import Options, CleanWord, FilterWord, list2str
from cached_property import cached_property
from typing import List, Dict, Optional, Union
from tqdm import tqdm
import numpy as np

      
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
    rep = re.sub('\([^\)]*\)', '', word)    
    
    if self.save_options == True:
      if len(options) == 0:
        options.append(word)
      
      without_josa = list(map(lambda x : re.sub('\([^\)]*\)', '', x), options))
      with_josa = list(map(lambda x : re.sub('[\(\)]', '', x), options))
      options = without_josa + with_josa
  
    return rep, options

  def run(self, word : str) -> str:
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
    self.clean_rep = ReviseRep(False).run
  
  def del_numbering(self, item : str) -> str:
    """delete numbers with the word representation
    (e.g. '‘단어01’의 준말')"""
    
    targets = re.findall("‘[^’]*’", item)
      
    for target in targets:
      revised = self.clean_rep(target)[0]
      
      if revised != target:
        target = re.sub('\]', '\]', re.sub('\[', '\[', target))
        target = re.sub('\)', '\)', re.sub('\(', '\(', target))
        item = re.sub(target, revised, item)
    
    return re.sub('[\[「][0-9]*[\]」]', '', item)
  
  def leave_synonym(self, item : str) -> str:
    """If the definition of word consists of synonym, leave the synonym and delete others"""
    if '→' in item:
      item = '→ ' + re.sub('→ |[0-9\.]', '', item)

    elif '⇒' in item:
      synonym_list = re.findall('‘.*’', item.split('⇒')[-1])
      if len(synonym_list) > 0:
        item = '→ ' + re.sub('[‘’]', '', synonym_list[0])
    
    elif '준말' in item or '줄여' in item:
      synonym_list = re.findall('‘.*’', item)
      if len(synonym_list) > 0:
        item = '→ ' + re.sub('[‘’]', '', synonym_list[0])
      
    return item
  
  def run(self, item : str) -> str:
    """Delete all the unneccessary marks in word definition"""
    without_chinese = self.del_chinese(item)
    without_english = self.del_english(item)
    without_numbering = self.del_numbering(without_chinese)
    without_marks = re.sub('</?(FL|sub|sup|equ|sp_no|each_sense_no|span|img|ptrnno)[^>]*>|<DR />|_', '', without_numbering)
    without_roman = self.roman_bracket.sub('', without_marks)
    without_etc = re.sub('또는 ?그런 ?것\.?', '', without_roman)
    without_broken = re.sub(' ‘[^’]*\.$', '', without_etc)
    output = self.leave_synonym(without_broken)

    return self.del_space(re.split('<동의 (속담|관용구)>', output)[0])


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
               input : List[Dict[str, Union[str, List[str]]]], 
               save_options : bool = True,
               allow_old : bool = False, 
               allow_broken : bool = False,
               del_overlapped : bool = True):
    
    self.input = input
    self._word_clean = ReviseRep(save_options).run
    self._def_clean = ReviseDef().run
    self._filter = FilterWord(allow_old, 
                            allow_broken).run
    self.output = self._build(del_overlapped)
  
  def _get_unit(self, item : Dict[str, str]) -> str:
    """Revise the word unit"""
    if item['pos'] == '구' or item['word_unit'] in ['관용구', '속담']:
      return '구'

    elif item['word_unit'] == '단어':
      return '어휘'

    else:
      return item['word_unit']

  def _get_pos(self, item : Dict[str, str]) -> str:
    """Revise the part-of-speech"""
    if item['pos'] == '품사없음' and '어근' in item['definition']:
      return '어근'

    elif item['word_unit'] == '구':
      return '구'

    else:
      return item['pos']
  
  def _get_info(self, item : Dict[str, str]) -> Dict[str, str]:
    """Revise all the inforamtion about a word"""
    word, options = self._word_clean(item['word'])
    item['word'] = word

    if options != None:
      item['other_forms'] = '/'.join(set(options))
    
    item['definition'] = self._def_clean(item['definition'])
    item['word_unit'] = self._get_unit(item)
    item['pos'] = self._get_pos(item)

    return item
  
  def _gen_dict(self, items : List[Dict[str, str]]) -> Dict[str, str]:
    """Sum the values in a list and generate a dictionary"""
    output = {'word' : items[0]['word']}
    output.update(
        {key : list2str([_[key] for _ in items]) for key in items[0].keys() if key not in ['definition','word']}
    )
    return output

  def _wrap(self, 
            input_list : List[Dict[str, str]],
            with_def : bool = False) -> Dict[str, List[Dict[str, str]]]:
    """Sort and zip all the word informtation to delete overlapped words"""
    output = defaultdict(list)
    for x in input_list:
      key = x['word'] + '#%#' + x['definition'] if with_def == True else x['word']
      output[key].append(x)
    return output
  
  def _del_item(self, items : List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Delete overlapped items in a list"""
    def_list = [_['definition'] for _ in items]
      
    if len(set([re.sub(' ' , '', x) for x in def_list])) == 1: #different in spacing
      new_dict = self._gen_dict(items)
      new_dict['definition'] =  items[0]['definition']
      items = [new_dict]
    
    elif def_list[0] in def_list[-1]: # B includes A
      new_dict = self._gen_dict(items)
      new_dict['definition'] =  items[-1]['definition']
      items = [new_dict]

    elif def_list[-1] in def_list[0]: # A includes B
      new_dict = self._gen_dict(items)
      new_dict['definition'] =  items[0]['definition']
      items = [new_dict]
      
    else:
      a_tokens, b_tokens = def_list[0].split(' '), def_list[-1].split(' ')
      
      if len(set(a_tokens) - set(b_tokens)) == 0:
        new_dict = self._gen_dict(items)
        new_dict['definition'] =  items[0]['definition']
        items = [new_dict]

      elif len(set(a_tokens) - set(b_tokens)) == 1 and len(set(b_tokens) - set(a_tokens)) == 1:
        new_dict = self._gen_dict(items)
        new_dict['definition'] =  ' '.join(
            [x if x in a_tokens else x + '(' + '/'.join(set(a_tokens) - set(b_tokens)) + ')' for x in b_tokens]
            )
        items = [new_dict]
        print(new_dict['definition'], def_list)

      elif len(set(b_tokens) ^ set(a_tokens)) < 3:
        new_dict = self._gen_dict(items)
        new_dict['definition'] =  ' '.join(
            [x if x in b_tokens else x + '(' + '/'.join(set(b_tokens) - set(a_tokens)) + ')' for x in a_tokens]
            )
        items = [new_dict]
        #print('b-a', new_dict['definition'], def_list)

      else:
        pass#print(def_list)
        
    return items
        
  def _build(self, del_overlapped : bool) -> List[Dict[str, str]]:
    output = [self._get_info(x) for x in tqdm(self.input) if self._filter(x['word'])]

    if del_overlapped == False:
      return output

    else:
      del_same, del_similar = list(), list()
      
      for key, items in tqdm(self._wrap(output, True).items()):
        word, definition = key.split('#%#')
        item_dict = self._gen_dict(items)
        item_dict['definition'] = definition
        del_same.append(item_dict)

      for key, items in tqdm(self._wrap(del_same).items()):
        source = [_['source'] for _ in items]
        result = self._del_item(items) if source.count('OKD') == 1 and source.count('SKD') == 1 and len(source) == 2 else items
        del_similar += result
      return del_similar

  def __getitem__(self, idx):
      return self.output[idx]
  
  def __len__(self):
      return len(self.output)
