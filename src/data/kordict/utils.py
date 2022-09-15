import re
from typing import List, Dict, Optional, Union
from src.data.utils import CleanStr
from jamo import h2j, j2hcj
from src.data.utils import ROMAN_NUM_UNICODE, CHINESE_UNICODE
from cached_property import cached_property
from boltons.iterutils import pairwise
from itertools import product


EOMI = 'ㅕㅓㅏㅑㅘㅝㅐㅒㅖㅔ'
NUMBERS =  '[' + '0-9' + ''.join(['%s-%s' % (s,e) for s,e in ROMAN_NUM_UNICODE]) + ']'
CHINESE_ENGLISH =  '[A-Za-z' + ''.join(['%s-%s' % (s,e) for s,e in CHINESE_UNICODE]) + ']'


def clean_conju(conjugation_list : List[str]):
  """Return Eo-conjugation('-어') form of a word"""
  output = list(filter(lambda x :j2hcj(h2j(x['long']))[-1] in EOMI, conjugation_list))
  if len(output) == 0:
    return ''
  
  else:
    output = list(filter(lambda x: x != None, sum([list(x.values()) for x in output],[])))
    output = sorted(output, key = lambda x : len(x)) 
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
  def __init__(self, 
               input : str,
               save_options : bool = True):
    self.input = input
    self.save_options = save_options
    self.output = self._build()

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
  
  def _build(self) -> str:
    """revise word represetation form with all the rules"""
    rep = re.sub('[0-9\-]', '', self.input)
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

  
class CleanDef:
  find_synonym = re.compile('‘[^’]*’')
  number_bracket = re.compile(CleanStr.rx_bracket(NUMBERS))
  letter_bracket = re.compile(CleanStr.rx_bracket(CHINESE_ENGLISH))

  def __init__(self, input :str, word :str):
    self.input, self.word = input, word
    self.output = self._build()
  
  def _split(self, line : str) -> List[str]:
    idx = [[x.start(0), x.end(0)] for x in self.find_synonym.finditer(line)]
    total_idx = sorted(sum(idx, []) + [0, len(line)])
    tokens = [line[s:e] for s,e in pairwise(total_idx) if len(line[s:e]) > 0]
    token_idx = [idx for idx, token in enumerate(tokens) if self.find_synonym.match(token)]
    return tokens, token_idx
  
  def _clean_synonym(self, token : str) -> str:
    """Revise words inside apostrophes‘’"""
    output = self.number_bracket.sub('', token)
    output = re.sub(NUMBERS, '', output) if not re.match('‘[0-9]+’', output) else output
    output = '‘%s’' % (self.word) if output == '‘’' and token != '‘’' else output
    output, _ = CleanRepr(output, False).output
    return re.sub('[\-\.\_\,]', '', output)
  
  def _clean_def(self, token : str) -> str:
    output = self.letter_bracket.sub('', token)
    return re.sub('또는 그런 것\.?$', '',output)

  def _build(self):
    input = CleanStr.clear_html(self.input)
    revised = re.sub('‘.*', '', input) if re.fullmatch('.*‘[^’]*', input) else input
    
    if revised.startswith('→')and len(self.find_synonym.findall(revised)) == 0:#synonym == definition
      output = self._clean_synonym(re.sub('→ ','', revised))
      return '→' + output, [re.sub('[‘’]', '', output)]
    
    elif re.match('.*⇒ ?규범', revised):
      parts = revised.split('⇒')
      definition, rest = parts[0], parts[-1]
      tokens, token_idx = self._split(rest)
      synonym = [re.sub('[‘’]', '',self._clean_synonym(t)) for i, t in enumerate(tokens) if i in token_idx]
      return self._clean_def(definition), synonym
    
    elif re.match('.*<동의 ?(속담|관용구)>', revised):
      parts = re.split('<동의 속담>|<동의 관용구>', revised)
      definition, rest = parts[0], parts[-1]
      tokens, token_idx = self._split(rest)
      synonym = [re.sub('[‘’]', '',self._clean_synonym(t)) for i, t in enumerate(tokens) if i in token_idx]
      return self._clean_def(definition), synonym 

    else:
      tokens, token_idx = self._split(revised)
      output = [self._clean_synonym(t) if i in token_idx else self._clean_def(t) for i, t in enumerate(tokens)]
      definition = ''.join(output[token_idx[0]:]) if revised.startswith('→') else ''.join(output)
      return definition, [re.sub('[‘’]', '',self._clean_synonym(t)) for i, t in enumerate(tokens) if i in token_idx]
