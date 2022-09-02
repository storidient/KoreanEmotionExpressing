import pandas as pd
import numpy as np
import re
from typing import List, Any, Tuple, Optional
from cached_property import cached_property
from boltons.iterutils import pairwise
from tqdm import tqdm
from toolz import partition
from itertools import product

from src.data.utils import del_zeros
from data.rx_codes import line_rx, end_rx, indirect_rx, after_indirect_rx

class QuotationChanger:
  def __init__(self, 
               input : List[str],
               up_to : int = 20):
    self.input, self.up_to, self.step = input, up_to, 1
    self.output = list() + self.input
    self._build()
  
  def other_mark(self):
    """ if self.mark is ", the other mark is ' """
    return re.sub(self.mark, '', '"\'')

  def _find_loop(self, line : str, idx : int):
    """Search the quotation marks and merge lines"""
    self.step = 1 #Reset self.next

    while line.count(self.mark) % 2 == 1 and self.step < self.up_to:
      if self.step + idx > len(self.output) - 1:
        break

      else:
        next = self.output[idx + self.step]
        line = line + ' ' + next

        if next.count(self.mark) % 2 == 1: 
          break
      
        elif next.count(self.other_mark()) % 2 == 1:
          line = re.sub("'", '"', line)
          break

        else:
          self.step += 1
        
    if line.count(self.mark) % 2 == 0:#Update the changes
      self.output[idx] = line
      for _ in range(1, self.step + 1):
        self.output[idx + _] = ''

  def _revise_q(self):
    """Revise quotation marks if the number of them is not even"""
    for idx, line in enumerate(self.output):
      if line.count(self.mark) % 2 == 1:
        self._find_loop(line, idx)
    self.output = del_zeros(self.output)

  def _force_q(self):
    """Force the quotation marks to make the numbers even"""
    for idx, x in enumerate(self.output):
      if x.count(self.mark) % 2 != 1: pass

      elif len(x.split(' ')) == 1:
        self.output[idx] =  x + self.mark

      elif '⋯' in x and x.find(self.mark) < x.find('⋯'):
        self.output[idx] = x.replace('⋯', '⋯' + self.mark, 1)
  
      else:
        self.output[idx] = re.sub(self.mark, '', x)
  
  def _build(self):
    for m in ['"', "'"]:
      self.mark = m
      self._revise_q()
    
    for m in ['"', "'"]:
      self.mark = m
      self._force_q()

  def __getitem__(self, idx):
    return self.output[idx]
  
  def __len__(self):
    return len(self.output)

  
class LineChanger:
  def __init__(self, input : str):
    self.input = input
    self.line_rx, self.end, self.indirect, self.after_indirect = line_rx, end_rx, indirect_rx, after_indirect_rx 
    self.output = self._build()
    
  def _target(self, mark : str, input : Optional[str] = None) -> List[str]:
    """Get the pairs of the quotation marks' indice"""
    text = self.input if input == None else input  
    indice = np.where(np.array(list(text)) == mark)[0]#find all the indices
    return list(partition(2, indice))#return them in pairs
  
  def _avoid(self, double : List[Tuple[Any]], single : List[Tuple[Any]]):
    """Delete the overlapped indice pairs"""
    return set([s for d, s in product(double, 
                                      single) if d[0] < s[0] and s[-1] < d[-1]])
    
  def _emphasis(self, s : int, e: int, input : Optional[str] = None) -> bool:
    """Decide whether this is a stressed phrase or word, not a line(e.g. the 'cute' dog)"""
    text = self.input if input == None else input
    target, front = text[s:e+1], text[:s]
    a = len(target.split(' ')) < 4 #less than four word
    b = len(self.end.findall(target)) == 0 #no end marks inside the token
    c = not bool(re.fullmatch('.*[\.\?\!] *', front)) if len(front) > 0 else True #no end marks in the token
    return not (a and b and c) #emphasis -> False -> filtered

  @cached_property
  def tokens(self) -> List[str]:
    """Return the parts of text split by " and ' """
    double = self._target('"')
    single = list(filter(lambda x :self._emphasis(x[0], x[1]), self._target("'")))      
    
    total = set(double + single) #a list of tuple
    if len(double) > 0 and len(single) > 0: #to avoid being overlapped
      total -= set(self._avoid(double, single))

    target = [[s, e+1] for s, e in sorted(total, key = lambda x: x[0])]
    target = sorted(sum(target, []) + [0, len(self.input)]) #to cover start to end
    return [self.input[s:e] for s,e in pairwise(target) if len(self.input[s:e]) > 0]

  def _split(self, item : str) -> List[str]:
    """Split items by the end marks(.?!)"""
    item = item.strip(' ')
    l = len(item)
    indices = [min(i+1, len(item)+1) for i, x in enumerate(item) if self.end.match(x) and '-' != item[min(i+1, l-1)]]
    output = [item[s:e] for s, e in pairwise(sorted([0, l+1] + indices))]
    return del_zeros(output)
  
  def _merge(self, input : List[str]) -> List[str]:
    """Merge lines to generate indirect quotation sentence"""
    output = list()
    while len(input) >= 2:#if one is a line, the other should not be a line
      now = bool(re.match('[\'\"]', input[0][-1]))
      next = bool(re.match('[\'\"]', input[1][0]))
      end = not bool(self.end.match(input[0][-1]))
      if (now != next) and end:
        input = [' '.join(input[:2])] + input[2:]
        
      else:
        output.append(input[0])
        input = input[1:]
    
    output += input
    return output 

  def _indirect(self, s : int, e : int, text : str) -> bool:
    """Decide whether this is an indirect quotation"""
    target = text[s:e]
    front, back = text[:s], text[e:]
    a = bool(self.indirect.match(back))#with a quotation eomi/josa
    b = bool(re.match('[^ 때]+[\.\?\!]', back))#followed by one word
    c = len(self.end.findall(target)) == 0#there are no end marks
    d = not bool(self.line_rx.match(back))#not followed by a line
    return not ((a or b or c) and d) #indirect -> False -> filtered

  def _revise(self, token):
    double = self._target('"', token)
    single = list(filter(lambda x :self._emphasis(x[0], x[1], token), self._target("'", token)))      
    total = set(double + single) #a list of tuple
    if len(double) > 0 and len(single) > 0: #to avoid being overlapped
      total -= set(self._avoid(double, single))
    
    target = [[s, e+1] for s, e in sorted(total, key = lambda x: x[0])]
    filtered = list(filter(lambda x: self._indirect(x[0], x[1], token), target))
    filtered = sorted(sum(filtered, []) + [0, len(token)]) #to cover start to end
    return [token[s:e] for s,e in pairwise(filtered) if len(token[s:e]) > 0]
  
  def _build(self):
    """Return the lines split by end marks"""
    divided = sum([[t] if self.line_rx.match(t) else self._split(t) for t in self.tokens],[])
    merged = del_zeros(self._merge(divided))
    return del_zeros(sum(list(map(self._revise, merged)),[]))
