"""Import the supplied workbook without third-party packages or network access."""
import json, re, sys, zipfile, posixpath
from pathlib import Path
import xml.etree.ElementTree as E
N={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships','x':'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
ROOT=Path(__file__).resolve().parents[1]
def convert(path):
 with zipfile.ZipFile(path) as z:
  def xml(p): return E.fromstring(z.read(p))
  def text(el): return ''.join(t.text or '' for t in el.findall('s:t',N)+el.findall('s:r/s:t',N))
  strings=[text(x) for x in xml('xl/sharedStrings.xml')]
  def rels(p):
   rp=posixpath.join(posixpath.dirname(p),'_rels',posixpath.basename(p)+'.rels')
   return {x.get('Id'):posixpath.normpath(posixpath.join(posixpath.dirname(p),x.get('Target'))) for x in xml(rp) if x.get('TargetMode')!='External'} if rp in z.namelist() else {}
  def sheet(i):
   p=f'xl/worksheets/sheet{i}.xml'; root=xml(p); rows=[]; images=[]
   for row in root.findall('s:sheetData/s:row',N):
    cells={}
    for c in row:
     v=c.find('s:v',N); value=v.text if v is not None else ''
     if c.get('t')=='s': value=strings[int(value)]
     elif c.get('t')=='inlineStr': value=text(c)
     if value: cells[re.sub(r'\d','',c.get('r'))]=value
    rows.append((int(row.get('r')),cells))
   for d in root.findall('s:drawing',N):
    dp=rels(p)[d.get('{'+N['r']+'}id')]; dr=rels(dp)
    for anchor in xml(dp):
     row=anchor.find('x:from/x:row',N)
     for b in anchor.findall('.//a:blip',N):
      target=dr.get(b.get('{'+N['r']+'}embed'))
      if target and row is not None: images.append((int(row.text)+1,'assets/'+posixpath.basename(target)))
   return rows,images
  def blocks(i):
   rows,imgs=sheet(i); out=[]
   for rn,c in rows:
    m=re.fullmatch(r'(\d+)\.',c.get('B',''))
    if m: out.append({'id':int(m[1]),'row':rn,'lines':[],'images':[]})
    if out:
     out[-1]['lines'].extend(v for k,v in c.items() if (k not in ('A','B') if i==3 else k in ('C','D')) and v)
   for rn,src in imgs:
    candidates=[b for b in out if b['row']<=rn]
    if candidates:candidates[-1]['images'].append(src)
   return out
  answers={b['id']:''.join(b['lines']) for b in blocks(2)}
  explanations={b['id']:b for b in blocks(3)}
  questions=[]
  for b in blocks(1):
   raw='\n'.join(b['lines']); parts=re.split(r'([①②③④⑤⑥⑦⑧⑨⑩])',raw)
   choices=[{'key':parts[j],'text':parts[j+1].strip()} for j in range(1,len(parts)-1,2)]
   source_note=''
   if b['id']==70:
    assert [c['key'] for c in choices]==['①','②','③','③']
    choices[3]['key']='④'
    source_note='原本では4番目の選択肢も「③」と記載されています。識別のため「④」と表示しています。正答は原本の解説に準拠します。'
   ans=answers[b['id']]; truth=ans in ('○','×'); exp=explanations.get(b['id'],{})
   questions.append({'id':b['id'],'sourceNote':source_note,'prompt':parts[0].strip(),'choices':[{'key':v,'text':v} for v in ('○','×')] if truth else choices,'answer':list(ans),'multiple':len(ans)>1,'images':b['images'],'explanation':'\n'.join(exp.get('lines',[])),'explanationImages':exp.get('images',[])})
  notes=[]
  for i,title in [(4,'メモ'),(5,'グラフ特徴')]:
   rows,imgs=sheet(i)
   content=[{'row':r,'text':' '.join(c.values())} for r,c in rows if c]
   notes.append({'title':title,'lines':content,'images':[{'row':r,'src':s} for r,s in imgs]})
  for name in z.namelist():
   if name.startswith('xl/media/'):
    (ROOT/'assets'/posixpath.basename(name)).write_bytes(z.read(name))
  data={'source':Path(path).name,'questions':questions,'notes':notes}
  (ROOT/'data.js').write_text('window.WORKBOOK = '+json.dumps(data,ensure_ascii=False)+';\n',encoding='utf-8')
  print(f'Imported {len(questions)} questions; {len(answers)} answers; {len(explanations)} explanations.')
  for q in questions:
   assert q['choices'],q['id']
   assert set(q['answer']) <= {c['key'] for c in q['choices']},q['id']
  assert len(questions)==157 and len({q['id'] for q in questions})==157
if __name__=='__main__':convert(sys.argv[1])
