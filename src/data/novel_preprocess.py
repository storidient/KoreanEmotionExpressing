import pandas as pd
import numpy as np
import re
from typing import List
from cached_property import cached_property
from boltons.iterutils import pairwise
from tqdm import tqdm
from toolz import partition

from src.data.utils import del_zeros
from data.rx_codes import line_rx, end_rx, indirect_rx, after_indirect_rx

class QuotationChanger:
  def __init__(self, 
               input : List[str],
               up_to : int = 20):
    self.input, self.up_to, self.step = input, up_to, 1
    self.output = list() + self.input
    self._build()
    self._relocate_q()
  
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

  def _relocate_q(self):
    """Revise incorrectly located quotation marks"""
    for idx, x in enumerate(self.output):
      if not re.match('.*\" ?[\.\?\,\!]', x): pass

      elif ',' in x and  x.find(',') < x.find('"'):
        self.output[idx] = x.replace('"', '', 1).replace(', ', ', "', 1)
      
      else:
        self.output[idx] = '"' + x.replace('"', '', 1)

  def __getitem__(self, idx):
    return self.output[idx]
  
  def __len__(self):
    return len(self.output)

class LineChanger:
  def __init__(self, input : str):
    self.input = input
    self.line_rx, self.end, self.indirect, self.after_indirect = line_rx, end_rx, indirect_rx, after_indirect_rx
    self.tokens = self._find()
    self.output = self._build()
    self._merge_behind()
    self._merge_front()
  
  def _get_target(self, 
                  text : str, 
                  mark : str) -> List[str]:
    """Get the pairs of the quotation marks' indice"""
    indice = np.where(np.array(list(text)) == mark)[0]#find all the indices
    return list(partition(2, indice))#return them in pairs

  def _find(self) -> List[str]:
    """Return the parts of text split by " and ' 
    (e.g. 'I was tired. "I wanna go home." I fell asleep.
          -> ['I was tired', '"I wanna go home."', 'I fell asleep.'])
    """
    targets = self._get_target(self.input, '"') + self._get_target(self.input, "'")
    targets = sorted(targets, key = lambda x: x[0])#the pairs of indices
    token_indices = sum([[a, b+1] for a, b in targets], [])
    tokens = [self.input[s:e] for s,e in pairwise(token_indices) if len(self.input[s:e]) > 0]
    return tokens

  def _split(self, item : str) -> List[str]:
    """Split items by the end marks(.?!)"""
    item = item.strip(' ')
    indices = [min(i+1, len(item)+1) for i, x in enumerate(item) if self.end.match(x)]
    output = [item[s:e] for s, e in pairwise(sorted([0, len(item)+1] + indices))]
    return del_zeros(output)

  def _build(self):
    """Return the lines split by end marks"""
    return sum([[t] if self.line_rx.match(t) else self._split(t) for i, t in enumerate(self.tokens)],[])
  
  def _merge_behind(self):
    """Merge lines including indirect quotations, which should not be split by end marks"""
    for idx, token in enumerate(self.output):
      if idx == len(self.output) - 1 or not self.line_rx.match(token):pass
      elif self.after_indirect.match(self.output[idx + 1]):
        self.output[idx] += ' ' + self.output[idx +1]
        self.output[idx + 1] = ''
      
      elif len(self.output[idx+1].split(' ')) == 1 and self.end.match(self.output[idx+1][-1]):
        if '때' not in self.output[idx +1]:
          self.output[idx] += ' ' + self.output[idx + 1]
          self.output[idx + 1] = ''

    self.output = del_zeros(self.output)

  def _merge_front(self):
    """Merge lines including indirect quotations, which should not be split by end marks"""
    for idx, token in enumerate(self.output):
      if idx == len(self.output) - 1 or self.line_rx.match(token): pass
      elif not self.indirect.match(self.output[idx + 1]): pass
      elif len(token) == 0: pass
      elif not self.end.match(token[-1]):
        self.output[idx] += ' ' + self.output[idx +1]
        self.output[idx + 1] = ''

    self.output = del_zeros(self.output)
  
  def __getitem__(self, idx):
    return self.output[idx]
  
  def __len__(self):
    return len(self.output)
