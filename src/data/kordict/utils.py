import re
from src.data.utils import CleanStr
from jamo import h2j, j2hcj
from src.data.utils import OLD_KOR_UNICODE, ROMAN_NUM_UNICODE, CHINESE_UNICODE

EOMI = 'ㅕㅓㅏㅑㅘㅝㅐㅒㅖㅔ'
OLD_KOR = re.compile('.*'+'['+ ''.join(['%s-%s' % (s,e) for s,e in OLD_KOR_UNICODE]) + ']', re.UNICODE)
NUMBERS =  '[' + '0-9' + ''.join(['%s-%s' % (s,e) for s,e in ROMAN_NUM_UNICODE]) + ']'
CHINESE_ENGLISH =  '[A-Za-z' + ''.join(['%s-%s' % (s,e) for s,e in CHINESE_UNICODE]) + ']'

def clean_conju(conjugation_list : List[str]):
  output = list(filter(lambda x :j2hcj(h2j(x['long']))[-1] in EOMI, conjugation_list))
  if len(output) == 0:
    return ''
  
  else:
    output = list(filter(lambda x: x != None, sum([list(x.values()) for x in output],[])))
    output = sorted(output, key = lambda x : len(x)) 
    return output[0] if len(output) > 0 else ''
