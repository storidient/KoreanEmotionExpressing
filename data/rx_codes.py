import re
from typing import List, Tuple

def build_rx(unicode_list : List[Tuple[str, str]]) -> str:
  """compile regular expression with unicodes"""
  unicodes = ''.join(['%s-%s' % (s,t) for s, t in unicode_list])
  return '[' + unicodes +']'

old_korean_unicode = [('\u3164', '\u318c'),
                      ('\u318e', '\u318f'), 
                      ('\ua960', '\ua97f'),
                      ('\ud7b0', '\ud7ff'),
                      ('\ue000', '\uefff'),
                      ('\uf000', '\uffff'),
                      ('\u1113', '\u115f'),
                      ('\u1176', '\u11a7'),
                      ('\u11c3', '\u11ff')]

chinese_unicode = [('\u31c0', '\u31ef'),
                   ('\u31f0', '\u31ff'),
                   ('\u3200', '\u32ff'),
                   ('\u3300', '\u33ff'),
                   ('\u3400', '\u4dbf'),
                   ('\u4dc0', '\u4dff'),
                   ('\u4e00', '\u9fff'),
                   ('\uf900', '\ufaff')]

roman_num = [('\u2160', '\u217f')]
line_pattern = '\"[^"]+"|\'[^\']+\''
indirect_pattern = ' ?((이?라|하)?[고|며|면서]|[라란] |하는 |한(다| ?뒤)|하였다\.)'


old_kor_rx = re.compile('.*' + build_rx(old_korean_unicode), re.UNICODE)
chinese_rx = re.compile('[\[\(]?' + build_rx(chinese_unicode) + '[\]\)]?', re.UNICODE)
blank_chinese= re.compile('[\u3000]', re.UNICODE)
katakana_middle = re.compile('[\u30fb]', re.UNICODE)
roman_num_rx = build_rx(roman_num)
roman_bracket = re.compile('[\(\[]' + roman_num_rx + '+[\]\)]', re.UNICODE)
line_rx = re.compile(line_pattern)
end_rx = re.compile('[\.\!\?]')
indirect_rx = re.compile(indirect_pattern)
after_indirect_rx = re.compile('(' + line_pattern + ')' + indirect_pattern)
