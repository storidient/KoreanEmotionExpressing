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
    self.output = self._build()
  
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
  
  def __getitem__(self, idx):
    return self.output[idx]
