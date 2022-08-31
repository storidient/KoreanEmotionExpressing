
def find_lines(text : str) -> List:
  lines = re.findall(r'\"[^\"]+[?!\.]?\"', text) #모든 대사
  indirect_lines = re.findall(r'\"[^\"]+[?!\.]?\"[고|라|하|한|란|할|랄|며]', text) + re.findall(r"\'[^\']+[?!\.]?\'", text) #간접 인용 대사
  #모든 대사 - 간접 인용 대사 = 직접 대사
  indi_lines = []
  for l in indirect_lines:
    indi_lines.append(l[:-1])

  direct_lines = [x for x in lines if x not in indi_lines] #직접 대사 

  return indi_lines, direct_lines



def mark_lines(whole_txt, direct_lines, indi_lines):

  for l in indi_lines:
    whole_txt = whole_txt.replace(l, '--'+ str(indi_lines.index(l))) 
    #re.sub(l, chr(indi_lines.index(l) + 97), whole_txt)

  for l in direct_lines:
    whole_txt = whole_txt.replace(l, "This is a line "+ str(direct_lines.index(l)))
    #re.sub(l,"This is a line " + str(direct_lines.index(l)), whole_txt)

  return whole_txt


def split_by_lines(whole_txt, direct_lines):
  #for n in range(len(direct_lines)):
  x = whole_txt.split('This is a line ')

  y = []

  for s in x:
    yy = s.split('.')

    for u in yy:
      if len(u) != 0:
        y.append(u.strip(' ') + '.') 

  return y

def refine_enter(data):
  whole_txt = ''
  final_sentence =[]

  for txt in data['text']:  #전체 텍스트 합치기
    whole_txt +=  txt

  indi_lines, direct_lines = find_lines(whole_txt)  #대사 목록 만들기

  whole_txt = mark_lines(whole_txt, direct_lines, indi_lines) #마킹
  splited_txt = split_by_lines(whole_txt, direct_lines) #문장 단위로 나누기
  
  #마킹된 자리에 대사 집어 넣기
  for sentence in splited_txt:

    #간접 인용 대사
    if re.search('--[0-9]+', sentence):

      if len(re.findall(r'--[0-9]+', sentence)) > 1:
        for idx_mark in re.findall(r'--[0-9]+', sentence):
          idx = int(idx_mark[2:])
          sentence = re.sub(idx_mark, indi_lines[idx], sentence)

      else:  
        idx = int(re.search(r'--[0-9]+', sentence).group()[2:])
        sentence = re.sub(re.search(r'--[0-9]+', sentence).group(), indi_lines[idx], sentence)

    #대사 
    if re.search(r'^[0-9]+', sentence):
      idx = int(re.search(r'^[0-9]+', sentence).group())

      if idx < len(direct_lines):
        line = direct_lines[idx]
        final_sentence.append(line)
        sentence = re.sub(re.search(r'^[0-9]+', sentence).group(), '', sentence)
        #print(sentence, 'is sentence')
    
    if sentence != '.':
      final_sentence.append(sentence)


  return final_sentence

