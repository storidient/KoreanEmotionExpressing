import json
from typing import Dict, List



class OpenKorean:
  """Get word information from a json file downloaded from Open Korean Dictionary
  (https://opendict.korean.go.kr/main)

  Attributes:
    path : a path of json file
    output : a list of dictionary with word information
       {word : a list of representation form of words
        word_unit : a list of 'unit' of words (e.g. 'phrase', 'word', 'saying')
        definition : a list of definition of words 
        type: a list of type of words (e.g. dialects, North-Korean, old Korean)
        pos: a list of part-of-speech
        source : 'OKD(Open Korean Dictionary)'}
  """
  def __init__(self, path : str):
    with open(path, 'r') as f:
      self.data = json.load(f)
    self.output = self._build()

  def _build(self) -> List[Dict[str, str]]:
    return list(map(self.get_info, self.data['channel']['item']))
    
  def get_info(self, item) -> Dict[str, str]:
    return {'word' : item['wordinfo']['word'],
            'word_unit' : item['wordinfo']['word_unit'],
            'definition' : item['senseinfo']['definition'],
            'type' : item['senseinfo']['type'],
            'pos' : item['senseinfo']['pos'] if 'pos' in item['senseinfo'].keys() else '품사 없음',
            'source' : 'OKD'}


  
class StandardKorean:
  """Get word information from a json file downloaded from Standard Korean Dictionary
  (https://stdict.korean.go.kr/main/main.do)

  Attributes:
    path : a path of json file
    output : a list of dictionary with word information
       {word : a list of representation form of words
        word_unit : a list of 'unit' of words (e.g. 'phrase', 'word', 'saying')
        definition : a list of definition of words 
        type: 일반어(ordinary words)
        pos: a list of part-of-speech
        source : 'SKD(Standard Korean Dictionary)'}
  """
  def __init__(self, path : str):
    with open(path, 'r') as f:
      self.data = json.load(f)
    self.output = self._build()
    
  def _build(self) -> List[Dict[str, str]]:
    return sum(list(map(self.get_info, self.data['channel']['item'])),[])
    
  def get_info(self, item) -> List[Dict[str, str]]:
    item = item['word_info']
    item_pos = item['pos_info']
    item_pattern = item_pos[0]['comm_pattern_info']

    return [{'word' : item['word'],
             'word_unit' : item['word_unit'],
             'pos' : item_pos[0]['pos'],
             'definition': sense_info['definition'],
             'type' : '일반어',
             'source' : 'SKD'} for sense_info in item_pattern[0]['sense_info']]
