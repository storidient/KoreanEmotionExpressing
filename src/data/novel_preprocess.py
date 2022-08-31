
def find_lines(text : str) -> List:
  lines = re.findall(r'\"[^\"]+[?!\.]?\"', text)
  indirect_lines = re.findall(r'\"[^\"]+[?!\.]?\"[고|라|하|한|란|할|랄|며]', text) + re.findall(r"\'[^\']+[?!\.]?\'", text)
  
  indi_lines = []
  for l in indirect_lines:
    indi_lines.append(l[:-1])

  direct_lines = [x for x in lines if x not in indi_lines] 

  return indi_lines, direct_lines



def mark_lines(whole_txt, direct_lines, indi_lines):

  for l in indi_lines:
    whole_txt = whole_txt.replace(l, '--'+ str(indi_lines.index(l))) 

  for l in direct_lines:
    whole_txt = whole_txt.replace(l, "This is a line "+ str(direct_lines.index(l)))

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

  for txt in data['text']: 
    whole_txt +=  txt

  indi_lines, direct_lines = find_lines(whole_txt) 

  whole_txt = mark_lines(whole_txt, direct_lines, indi_lines) 
  splited_txt = split_by_lines(whole_txt, direct_lines) 
  
  
  for sentence in splited_txt:

    
    if re.search('--[0-9]+', sentence):

      if len(re.findall(r'--[0-9]+', sentence)) > 1:
        for idx_mark in re.findall(r'--[0-9]+', sentence):
          idx = int(idx_mark[2:])
          sentence = re.sub(idx_mark, indi_lines[idx], sentence)

      else:  
        idx = int(re.search(r'--[0-9]+', sentence).group()[2:])
        sentence = re.sub(re.search(r'--[0-9]+', sentence).group(), indi_lines[idx], sentence)

    
    if re.search(r'^[0-9]+', sentence):
      idx = int(re.search(r'^[0-9]+', sentence).group())

      if idx < len(direct_lines):
        line = direct_lines[idx]
        final_sentence.append(line)
        sentence = re.sub(re.search(r'^[0-9]+', sentence).group(), '', sentence)
        
    
    if sentence != '.':
      final_sentence.append(sentence)


  return final_sentence

