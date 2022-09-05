from bs4 import BeautifulSoup
import requests, re, unicodedata
from boltons.iterutils import pairwise
from typing import List, Any
from cached_property import cached_property
from src.data.utils import CleanStr
import numpy as np


class WikiNovel:
  """Download novels from ko.wikisource
  Attributes:
    wiki : the url of ko.wikisource
    url: the url of the novel 
    text : a list of paragraphs downloaded from ko.wikisource
  """

  wiki = 'https://ko.wikisource.org/wiki/'

  def __init__(self, 
               title : str):
    self.url = self.wiki + title
    self.text = self._build()
  
  def _download(self):
    """Get data from wiki.source with bs4"""
    response = requests.get(self.url)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find('div', 'mw-parser-output')
  
  def _clear(self, line : str):
    """Delete html tags inside a line"""
    return line.lstrip('<p>').rstrip('</p>').strip('br/>').strip(' ')

  def _get_p(self, soup_list : List[Any]):
    """Get text only with <p> from the soup list"""
    txt = [str(t) for t in soup_list if str(t).startswith('<p>')]
    cleaned = list(map(self._clear, txt))
    return [x for x in cleaned if len(x) > 0]
  
  def _get_parts(self, soup : List[Any]):
    """Get paragraphs from the soup"""
    inside_box =  soup.find('div', 'prose')
    input = inside_box if inside_box != None else soup
    
    indice = [idx for idx, t in enumerate(input) if not str(t).startswith('<p>')]
    indice = sorted(indice + [0, len(input)])
    parts = [list(input)[s:e] for s,e in pairwise(indice)] #slice with the indices
    filtered = list(map(lambda x : self._get_p(x), parts)) #leave only <p>
    return [_ for _ in filtered if len(_) > 0]
  
  def _build(self):
    soup = self._download()
    return list() if soup == None else self._get_parts(soup)

  
class CleanLine(CleanStr):
  def __init__(self, input : List[List[str]]):
    self.input = input
    self.left_del = self.rx.build_rx(['['] + self.rx.bracket.starts('\(') +[']'])
    self.right_del = self.rx.build_rx(['['] + self.rx.bracket.ends('\)') +[']'])
    self.output = list(map(self._build, input))
    
  @cached_property
  def no_q(self):
    """Decide whether the text has quotation marks(") or not"""
    total, output = ''.join(np.concatenate(self.input)), 'only'
    if len(self.rx.quotation_rx.findall(total)) > 0: pass

    elif len(self.rx.sickles_rx.findall(total)) > 0:
      output = 'sickles'
    
    elif len(self.rx.inequlas_rx.finall(total)) > 0:
      output = 'inequals'

    return output

  def _change_q(self, line):
    """Change sickles or inequal marks into quotation marks"""
    if self.no_q == 'sickles':
      return  self.rx.sickles_rx.sub('"', line)
    else:
      return self.rx.sickles_rx.sub('"', line) if self.no_q == 'inequals' else line

  def _line(self, line):
    normalized = self.del_space(unicodedata.normalize('NFC', line))
    old_kor = self.rx.old_kor_all.sub('', normalized) #except Are-a
    html = self.clear_html(old_kor)
    ch = self.del_chinese(html)#Delete all Chinese letters
    en = self.del_english(ch)#Delete English letters inside brackets
    jn = self.del_japanese(en)#Delete all Japanese letters
    empty = self.del_empty_bracket(jn)
    num = self.rx.number_bracket.sub('', empty) #Delete Numbers inside brackets
    roman = self.rx.roman_num_bracket.sub('', num) #Delete Roman numbers inside brackets
    unified = self.unify(roman)
    q_changed = self._change_q(unified)
    b_removed = self.right_del.sub('>', self.left_del.sub('<', q_changed))
    return self.del_space(b_removed)
  
  def _build(self, paragraph):
    return list(map(self._line, paragraph))
  
  def __getitem__(self, idx):
    return self.output[idx]
