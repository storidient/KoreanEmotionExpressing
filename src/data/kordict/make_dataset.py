import json, re
from typing import Dict, List, Tuple, Union
from src.data.kordict.utils import CleanRepr, CleanDef, clean_conju
import numpy as np
from attrs import define, field


@define(frozen = True)
class Wordinfo:
  repr : str
  definition : str
  pos : str
  conjugation : list = field(converter = clean_conju)
  word : str = field(converter = lambda x : re.sub('[0-9\^\_]','',x),
                     eq = False)
  options : list = field(converter = lambda x : '&'.join(sorted(x)),
                         eq = False)
  syntax : list = field(converter = lambda x : '&'.join(sorted(x)), 
                        eq = False)
  synonym : list = field(converter = lambda x : '&'.join(sorted(x)),
                         eq = False)
  unit : str = field(eq = False)
  word_type : str = field(eq = False)

  @classmethod
  def update(cls, info : Dict):
    repr, options = CleanRepr(info['word']).output
    definition, synonym = CleanDef(info['definition'],info['word']).output
    info.update({
        'repr' : repr,
        'options' : options,
        'definition' : definition,
        'synonym' : synonym

    })
    return cls(**info)

    
class KoreanCorpus:
  def __init__(self, 
               path : str, 
               standard : bool = True):
    self.standard = standard
    with open(path, 'r') as f:
      data = json.load(f)
    self.output = self._build(data)
  
  def _build(self, data):
    if self.standard == True:
      return sum(list(map(self._standard_info, data['channel']['item'])),[])
    
    else:
      return list(map(self._our_info, data['channel']['item']))
  
  def get_conju(self, item : List[Dict[str, str]]) -> List[Tuple[str, str]]:
    """Return conjugation forms of a word"""
    return [(x['conjugation_info']['conjugation'],
             x['abbreviation_info']['abbreviation'] if 'abbreviation_info' in x.keys() else None) for x in item]
  
  def _standard_info(self, item) -> Dict[str, Union[List[str], str]]:
    """Get word information from a json file downloaded from Standard Korean Dictionary
    (https://stdict.korean.go.kr/main/main.do)"""
    item = item['word_info']
    item_pos = item['pos_info']
    item_pattern = item_pos[0]['comm_pattern_info']
    pos = item_pos[0]['pos']
    pattern = [item_pattern[0]['pattern_info']['pattern']] if 'pattern_info' in item_pattern[0].keys() else list()
    conjugation = item['conju_info'] if 'conju_info' in item.keys() else list()

    return [Wordinfo.update({'word' : item['word'], 
                             'unit' : item['word_unit'],
                             'syntax' : pattern,
                             'conjugation' : conjugation,
                             'pos' : pos,
                             'definition' : sense_info['definition'],
                             'word_type' : '표준어'}) for sense_info in item_pattern[0]['sense_info']]
  
  def _our_info(self, item) -> Dict[str, Union[List[str], str]]:
    """Get word information from a json file downloaded from Open Korean Dictionary
    (https://opendict.korean.go.kr/main)"""
    pos = item['senseinfo']['pos'] if 'pos' in item['senseinfo'].keys() else '품사 없음'
    pattern = [x['pattern'] for x in item['senseinfo']['pattern_info']] if 'pattern_info' in item['senseinfo'].keys() else list()
    conjugation = item['wordinfo']['conju_info'] if 'conju_info' in item['wordinfo'].keys() else list()

    return Wordinfo.update({'word' : item['wordinfo']['word'],
                            'unit' : item['wordinfo']['word_unit'],
                            'syntax' : pattern,
                            'conjugation' : conjugation,
                            'pos' : pos,
                            'definition' : item['senseinfo']['definition'],
                            'word_type' : item['senseinfo']['type']})
