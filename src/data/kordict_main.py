import os
import sys
import argparse
import json
import re
import logging
import numpy as np

from typing import Dict, List, Tuple, Union
from pathlib import Path
from tqdm import tqdm
from itertools import groupby
from attrs import define, field, asdict

try:
  from utils import OLD_KOR_UNICODE
  from kordict_utils import CleanRepr, CleanDef, clean_conju

except:
  from src.data.utils import OLD_KOR_UNICODE
  from src.data.kordict_utils import CleanRepr, CleanDef, clean_conju


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
  unit : str = field
  word_type : str = field

  @classmethod
  def update(cls, info : Dict):
    repr, options = CleanRepr(info['word']).output
    definition, synonym = CleanDef(info['definition'],info['word']).output
    unit = '단어' if info['unit'] in ['단어', '어휘'] else '구'
    pos = '구' if unit == '구' else info['pos']
    
    info.update({
      'unit' : unit,
      'pos' : pos,
      'repr' : repr,
      'options' : options,
      'definition' : definition,
      'synonym' : synonym
    })
    
    return cls(**info)
    
    
class KordictDataset:
  filter = re.compile('.*'+'['+ ''.join(['%s-%s' % (s,e) for s,e in OLD_KOR_UNICODE]) + ']|[ㄱ-ㅎㅏ-ㅣ]+$', re.UNICODE)
    
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
    output = list(filter(lambda x : not self.filter.match(x.repr), output)) if self.filter_old_kor == True else output
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
                             'word_type' : '일반어'}) for sense_info in item_pattern[0]['sense_info']]
  
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

  
if __name__ == '__main__':
  sys.path.append(os.getcwd())
  parser = argparse.ArgumentParser()
  parser.add_argument("--skd_dir", 
                      type=str, 
                      default = '', 
                      help = 'The folder of json files downloaded from Standard Korean Dictionary')
  parser.add_argument("--okd_dir", 
                      type=str, 
                      default = '', 
                      help = 'The folder of json files downloaded from Our Korean Dictionary')
  parser.add_argument("--save_dir", type=str, default = './')
  parser.add_argument("--save_as_dict", type=bool, default = False)
  args = parser.parse_args()

  total = list()
  if args.skd_dir != '':
    for x in tqdm(Path(args.skd_dir).glob('**/*.json')):
      total += KordictDataset(x).output
  
  if args.okd_dir != '':
    for x in tqdm(Path(args.okd_dir).glob('**/*.json')):
      total += KordictDataset(x, False).output

  total = list(set(total))
  
  if args.save_as_dict == True:
    output = {k : list(map(lambda x : asdict(x), g)) for k, g in 
              groupby(sorted(total, key = lambda x: x.repr), key = lambda x : x.repr)}
    with open(Path(args.save_dir)/ 'korean_dataset.json', "w", encoding="utf-8") as f:
      json.dump(output, f, ensure_ascii=False)
  
  else:
    with open(Path(args.save_dir)/ 'korean_dataset.jsonl', "w", encoding="utf-8") as f:
      output = list(map(lambda x : asdict(x), total))
      for i in output: 
        f.write(json.dumps(i) + "\n")
