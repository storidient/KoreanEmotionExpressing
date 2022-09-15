import json, re
from typing import Dict, List, Union
import numpy as np


class KoreanDictionary:
  """
  Attributes:
    path : a path of json file
    output : a list of dictionaries with word information
       {word : a list of representation form of words
        word_unit : a list of 'unit' of words (e.g. 'phrase', 'word', 'saying')
        definition : a list of definition of words 
        type: a list of type of words (e.g. dialects, North-Korean, old Korean)
        pos: a list of part-of-speech
        source : 'OKD(Open Korean Dictionary)'}
  """
  def __init__(self, data, standard : bool = True):
    input = data['channel']['item']
    self.output = list(map(self.standard_info, input)) if standard == True else list(map(self.our_info, input))
  
  @staticmethod
  def get_conju(item : List[Dict[str, str]]) -> List[str]:
    """Return conjugation forms of a word"""
    return [{'long' : x['conjugation_info']['conjugation'],
             'short' : x['abbreviation_info']['abbreviation'] if 'abbreviation_info' in x.keys() else None
            } for x in item]
  
  @staticmethod
  def standard_info(item) -> Dict[str, Union[List[str], str]]:
    """Get word information from a json file downloaded from Standard Korean Dictionary
    (https://stdict.korean.go.kr/main/main.do)"""
    item = item['word_info']
    item_pos = item['pos_info']
    item_pattern = item_pos[0]['comm_pattern_info']
    pos = item_pos[0]['pos']
    pattern = [item_pattern[0]['pattern_info']['pattern']] if 'pattern_info' in item_pattern[0].keys() else list()
    conjugation = get_conju(item['conju_info']) if ('형용사' in pos or '동사' in pos) and ('conju_info' in item.keys()) else list()

    return {'word' : item['word'],
            'word_unit' : item['word_unit'],
            'pattern' : pattern,
            'conjugation' : conjugation,
            'pos' : pos,
            'definition': [_['definition'] for _ in in item_pattern[0]['sense_info']],
            'type' : '일반어',
            'source' : 'SKD'}
  
  @staticmethod
  def our_info(item) -> Dict[str, Union[List[str], str]]:
    """Get word information from a json file downloaded from Open Korean Dictionary
    (https://opendict.korean.go.kr/main)"""
    pos = item['senseinfo']['pos'] if 'pos' in item['senseinfo'].keys() else '품사 없음'
    pattern = [x['pattern'] for x in item['senseinfo']['pattern_info']] if 'pattern_info' in item['senseinfo'].keys() else list()
    conjugation = get_conju(item['wordinfo']['conju_info']) if ('형용사' in pos or '동사' in pos) and ('conju_info' in item['wordinfo'].keys()) else list()
    
    return {'word' : item['wordinfo']['word'],
            'word_unit' : item['wordinfo']['word_unit'],
            'pattern' : pattern,
            'conjugation' : conjugation,
            'definition' : [item['senseinfo']['definition']],
            'type' : item['senseinfo']['type'],
            'pos' : pos,
            'source' : 'OKD'}
