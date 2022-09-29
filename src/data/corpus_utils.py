import sys
import os
import re
from jamo import j2hcj, h2j, j2h
from itertools import groupby
import json
import argparse
import pandas as pd
from pathlib import Path
from cached_property import cached_property
from typing import List, Dict, Union, Tuple


def adj_conju(item : Dict[str, str]) -> str:
  """Add adjective transformative suffix : (-으)ㄴ, 는"""
  stem = item['repr'][:-1]
  last_syl = j2hcj(h2j(stem[-1]))

  if stem[-1] in ['있', '없'] or '동사' in item['pos']:
    last_stem = last_syl[:-1] if last_syl[-1] == 'ㄹ' else last_syl
    return stem[:-1] + j2h(*last_stem) + '는'

  elif len(last_syl) == 2 or last_syl[-1] == 'ㄹ':
    last_stem = last_syl[:-1] if last_syl[-1] == 'ㄹ' else last_syl
    return stem[:-1] + j2h(*last_stem + 'ㄴ')
  
  elif last_syl[-1] == 'ㅎ' and stem[-1] != '좋':
    return stem[:-1] + j2h(*last_syl[:-1] + 'ㄴ')

  elif last_syl[-1] == 'ㅅ':
    last_stem = last_syl[:-1] if stem[-1] in ['짓', '잇', '젓', '낫', '붓'] else last_syl
    return stem[:-1] + j2h(*last_stem) + '은'
  
  elif stem[-1] in ['곱', '굽'] and item['conjugation'] != '':
    conjugation = item['conjugation'].split('/')[0][-2]
    return stem + '은' if 'ㅂ' in j2hcj(h2j(conjugation)) else stem[:-1] + j2h(*last_syl[:-1]) + '운'
  
  elif last_syl[-1] == 'ㅂ' and stem[-1] not in ['업', '잡', '접', '좁', '줍']:
    return stem[:-1] + '운' if stem[-1] == '웁' else stem[:-1] + j2h(*last_syl[:-1]) + '운'

  else:
    return stem + '은'
  

def add_conjugation(verb : str, conju : str):
  stem, output = verb[:-1], list()
  jamo = j2hcj(h2j(stem))
  
  if conju.endswith('워'):
    output.append(conju[:-1] + '우')
  
  if conju.endswith('와'):
    output.append(conju[:-1] + '오')

  return output

class FindConjugation:
  def __init__(self, word_map : Dict[str, List[Dict[str, str]]]):
    self.word_map = word_map
    self.verb_map = self._get_map(['동사', '형용사'])

  def _get_map(self, pos_list):
    """Return the verb dictionary sorted by the word representation form"""
    return {k : v for k, v in self.word_map.items() if len(
        list(filter(lambda x : x['pos'] in pos_list and x['word_type'] == '일반어', v))
        ) > 0}

  @cached_property
  def conju_data(self):
    """Return the dictionary of word representation and its conjugation"""
    conju_data = {k[:-1]: set(
        [x['conjugation'] for x in v if len(x['conjugation']) > 0 and k[:-1] not in x['conjugation']]
        ) for k, v in self.verb_map.items()}
    output = dict(filter(lambda x : len(x[-1]) > 0, conju_data.items()))
    return {k : [x[-1] if len(x) == len(k) else x[-2:] for x in v] for k,v in output.items()}
  
  @cached_property
  def short_cut(self):
    """Return the dictionary of the last syllable of word and its conjuation form 
    only if their pattern is uniform"""
    output = {k : set(sum([x[-1] for x in g],[])) for k, g in 
              groupby(sorted(self.conju_data.items(), key = lambda x : x[0][-1]), 
                      key = lambda x : x[0][-1])}
    return dict(filter(lambda x : len(x[-1]) == 1, output.items()))

  def vowel(self, word : str) -> bool:
    """Return whether the word is yang-sung(bright) vowel"""
    jamo = j2hcj(h2j(word))
    vowel = jamo[1] if len(jamo) > 2 else jamo[-1]
    return True if vowel in 'ㅏㅗㅑㅛㅐㅚㅘㅒ' else False

  def find(self, word : str) -> str:
    """Return the '어(-Eo)'conjugation form of a word"""
    stem = word[:-1]
    if stem[-1] in self.short_cut.keys():
      conju_set = self.short_cut[stem[-1]]
    
    else:
      last_syl = dict(filter(lambda x : stem[-1] == x[0][-1], self.conju_data.items()))
      conju_set = set(sum(list(last_syl.values()), []))
      
      if len(stem) > 1:
        targets = dict(filter(lambda x : len(x[0]) > 1, last_syl.items()))
        one_half = sum([v for k,v in targets.items() if self.vowel(stem[-2]) == self.vowel(k[-2])], [])
        conju_set = set(one_half) if len(one_half) > 0 else conju_set
        
    return word[:-2] + list(conju_set)[0] if len(conju_set) == 1 else word
  
  
class SearchPattern(FindConjugation):
  def __init__(self, data):
    super().__init__(data)
    self.noun_map = self._get_map(['명사'])
    self.suffix_map = self._get_map(['어미', '접사'])
    
  def _revise_unknown(self, word):
    """Split unknown word into stems"""
    splited = [[word[:i], word[i:]] for i in range(len(word)-1, 0, -1)]
    filtered = [x for x in splited if x[0]in self.noun_map.keys() and re.match('이?다', x[-1])]
    with_suffix = list(filter(lambda x: x[-1] in self.suffix_map.keys(), filtered))
    with_verb = list(filter(lambda x: x[-1] in self.verb_map.keys(), filtered))
    if len(with_suffix) > 0:
      return ' '.join(with_suffix[0]) if with_suffix[0] in with_verb else word
    
    elif len(with_verb) > 0:
      return ' '.join(with_verb[0]) if len(with_verb) > 0 else word
    
    else:
      with_josa = (word[:-2], '이다') if word.endswith('이다') else (word[:-1], '다')
      return with_josa[0] if with_josa[0] in self.noun_map.keys() else word
  
  def get_pattern(self, word: str) -> Dict[str, Union[str, Tuple[str]]]:
    if word.endswith('다') and (word not in self.word_map.keys()) and len(word.split(' ')) == 1:
      word = self._revise_unknown(word)
    
    if not word.endswith('다'):
      return {'type': 'not_verb', 'search_pattern' : word}
  
    elif len(word.split(' ')) > 1:
      tokens = word.split(' ')
      noun, verb = ''.join(tokens[:-1]) , tokens[-1]
      conju = self.find(verb)
      output = [verb[:-1]] if verb[:-1] in conju else [verb[:-1], conju]
      output += add_conjugation(verb, conju)

      return {'type' : 'phrase', 'search_pattern' : [noun, list(set(output))]}

    else:
      conju = self.find(word)
      output = [word[:-1]] if word[:-1] in conju else [word[:-1], conju]
      output += add_conjugation(word, conju)
      return {'type' : 'verb', 'search_pattern' : list(set(output))}


if __name__  == '__main__':
  sys.path.append(os.getcwd())
  
  parser = argparse.ArgumentParser()
  parser.add_argument("--kordata_dir", type=str)
  parser.add_argument("--corpus_dir", type=str)
  parser.add_argument("--save_dir", type=str)
  
  args = parser.parse_args()
  
  corpus_data = pd.read_csv(Path(args.corpus_dir))
  with open(Path(args.kordata_dir), 'r') as f:
    kor_data = json.load(f, encoding = 'utf-8')

  search_pattern = SearchPattern(kor_data)
  conju_data = list(map(search_pattern.get_pattern, corpus_data['word']))
  corpus_df = pd.DataFrame(conju_data)
  corpus_df['word'] = corpus_data['word']

  if 'ekman' in corpus_data.columns:
    corpus_df['emotion'] = corpus_data['ekman']

  elif 'emotion_1' in corpus_data.columns:
    emotion = pd.concat([corpus_data['emotion_1'],
                         corpus_data['emotion_2'], 
                         corpus_data['emotion_3']], axis = 1)
    corpus_df['emotion'] = [list(filter(lambda x : type(x) == str, emo_list)) for emo_list in emotion.values]
    
  elif 'emotion' in corpus_data.columns:
    corpus_df['emotion'] = [x.split('/') for x in corpus_data['emotion']]
    
  corpus_df = corpus_df[corpus_df['emotion'] != 'None']
  corpus_df['emotion'] = [[x] if type(x) == str else x for x in corpus_df['emotion']]
  corpus_data = corpus_df.to_dict('records')
  
  fname = 'corpus_' + str(Path(args.corpus_dir).parts[-1]).replace('.csv', '.jsonl')                 
  with open(fname, "w", encoding="utf-8") as f:
    f.write(json.dumps(corpus_data, ensure_ascii=False) + "\n")
