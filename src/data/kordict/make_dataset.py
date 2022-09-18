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
  word : str = field(converter = lambda x : re.sub('[0-9\^\_]','',x))
  options : list = field(converter = lambda x : '&'.join(sorted(x)))
  syntax : list = field(converter = lambda x : '&'.join(sorted(x)))
  synonym : list = field(converter = lambda x : '&'.join(sorted(x)))
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
    
    
class KordictDataset:
  def __init__(self, 
               path : str, 
               standard : bool = True,
               filter_old_kor : bool = True):
    self.path, self.standard, self.filter_old_kor = path, standard, filter_old_kor
    self.output = self._build()
  
  def _open(self, path):
    with open(path, 'r') as f:
      data = json.load(f)
    return data
    
  def _build(self):
    data = self._open(self.path)['channel']['item']
    output = sum(list(map(self._standard_info, data)),[]) if self.standard == True else list(map(self._our_info, data))
  
    if self.filter_old_kor == True:
      from src.data.utils import OLD_KOR_UNICODE
      kor_filter = re.compile('.*'+'['+ ''.join(['%s-%s' % (s,e) for s,e in OLD_KOR_UNICODE]) + ']|[ㄱ-ㅎㅏ-ㅣ]+$', re.UNICODE)
      return list(filter(lambda x : not kor_filter.match(x.repr), output))
    
    else:
      return output
  
  def _standard_info(self, item) -> Dict[str, Union[List[str], str]]:
    """Get word information from a json file downloaded from Standard Korean Dictionary (https://stdict.korean.go.kr/main/main.do)"""
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
    """Get word information from a json file downloaded from Open Korean Dictionary (https://opendict.korean.go.kr/main)"""
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
