"""Compute source retrieval, refusal, and citation support metrics."""
import json,re,sys
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
SET=ROOT/'eval/questions.json';RESULTS=ROOT/'eval/results'

def metrics(rows,k=5):
 eligible=[r for r in rows if r['category']=='in_scope' and r.get('gold_ids')]
 ranks=[]
 for row in eligible:
  rank=next((i+1 for i,x in enumerate(row['retrieved_ids'][:k]) if x in set(row['gold_ids'])),None);ranks.append(rank)
 refuse_rows=[r for r in rows if 'expected_refusal' in r]
 refusal=sum(bool(r['refused'])==bool(r['expected_refusal']) for r in refuse_rows)/len(refuse_rows) if refuse_rows else None
 return {f'hit@{k}':sum(r is not None for r in ranks)/len(ranks) if ranks else None,'mrr':sum((1/r if r else 0) for r in ranks)/len(ranks) if ranks else None,'refusal_accuracy':refusal,'labeled_retrieval_questions':len(eligible),'refusal_labeled_questions':len(refuse_rows)}

def faithfulness_check(answer,hits,provider):
 """Require each citation to resolve and each cited sentence to overlap its passage."""
 from rag.engine import lexical_overlap,REFUSAL
 if answer.strip()==REFUSAL:return {'citation_validity':None,'sentence_support':None,'cited_sentences':0,'supported_sentences':0}
 valid_ids=set(range(1,len(hits)+1))
 if provider=='passage_fallback':
  blocks=re.split(r'\n\s*\[(\d+)\]\s*',answer)
  citations=[int(blocks[i]) for i in range(1,len(blocks)-1,2)]
  sent_pairs=[]
  for i in range(1,len(blocks)-1,2):
   idx=int(blocks[i]);text=blocks[i+1]
   for sentence in re.split(r'(?<=[.!?])\s+|\n+',text):
    if re.search(r'[A-Za-z0-9]{2,}',sentence):sent_pairs.append((sentence,[idx]))
 else:
  citations=[int(x) for x in re.findall(r'\[(\d+)\]',answer)]
  sent_pairs=[]
  for sentence in re.split(r'(?<=[.!?])\s+|\n+',answer):
   if re.search(r'[A-Za-z0-9]{2,}',sentence):sent_pairs.append((sentence,[int(x) for x in re.findall(r'\[(\d+)\]',sentence)]))
 supported=0
 for sentence,ids in sent_pairs:
  clean=re.sub(r'\[\d+\]',' ',sentence)
  if any(i in valid_ids and lexical_overlap(clean,hits[i-1]['text'])>=.35 for i in ids):supported+=1
 return {'citation_validity':sum(i in valid_ids for i in citations)/len(citations) if citations else 0.0,
         'sentence_support':supported/len(sent_pairs) if sent_pairs else None,'cited_sentences':len(sent_pairs),'supported_sentences':supported}

def _answer(qs,mode):
 from rag.engine import HybridRetriever,generate,should_refuse
 r=HybridRetriever();rows=[]
 for q in qs:
  hits=r.retrieve(q['question'],k=5)
  answer,provider=generate(q['question'],hits,q.get('language','English'),q.get('mode','Answer'),provider_mode=mode)
  rows.append({**q,'retrieved_ids':[x['id'] for x in hits], 'confidence':hits[0]['confidence'] if hits else 0,
    'answer':answer,'provider':provider,'refused':answer.strip().startswith('This is not covered in the lecture material.'),
    'faithfulness':faithfulness_check(answer,hits,provider.split(' ')[0])})
 return rows

def main():
 qs=json.loads(SET.read_text())
 if len(qs)!=30 or Counter(q['category'] for q in qs)!=Counter({'in_scope':20,'out_of_scope':5,'adversarial':5}):raise SystemExit('Expected exactly 30 questions: 20 in-scope, 5 out-of-scope, 5 adversarial.')
 if any(not q.get('gold_ids') for q in qs if q['category']=='in_scope'):raise SystemExit('In-scope questions require source-verified gold IDs.')
 RESULTS.mkdir(parents=True,exist_ok=True)
 outputs={}
 for mode,name in [('passage_only','passage_only'),('auto','llm_auto')]:
  rows=_answer(qs,mode);result=metrics(rows);faith=[r['faithfulness'] for r in rows]
  cvalid=[x['citation_validity'] for x in faith if x['citation_validity'] is not None]
  result['citation_validity']=sum(cvalid)/len(cvalid) if cvalid else None
  supports=[x['sentence_support'] for x in faith if x['sentence_support'] is not None]
  result['sentence_support']=sum(supports)/len(supports) if supports else None
  result['provider_counts']=dict(Counter(r['provider'] for r in rows))
  outputs[name]={'metrics':result,'rows':rows};(RESULTS/f'rows_{name}.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
  (RESULTS/f'metrics_{name}.json').write_text(json.dumps(result,indent=2))
 summary={'run_utc':datetime.now(timezone.utc).isoformat(),'retriever':'all-MiniLM-L6-v2 cosine + Okapi BM25 + RRF@60','auto_provider_counts':outputs['llm_auto']['metrics']['provider_counts'],'thresholds':json.loads((ROOT/'data/refusal_thresholds.json').read_text()) if (ROOT/'data/refusal_thresholds.json').exists() else {'fallback':.35,'min_overlap':.05},'modes':{n:v['metrics'] for n,v in outputs.items()}}
 (RESULTS/'metrics.json').write_text(json.dumps(summary,indent=2))
 report=['# HeapMind evaluation','',f"Run: {summary['run_utc']}",'','Retriever: '+summary['retriever'],f"Tuned refusal settings: {summary['thresholds']}",f"Auto provider counts (actual): {summary['auto_provider_counts']}",'','Thirty questions: 20 in-scope, 5 out-of-scope, 5 adversarial. Retrieval metrics use the 20 source-labeled in-scope questions; refusal accuracy uses the labeled out-of-scope and adversarial items. Faithfulness is a rule-based lexical-support check, not human judgment.','']
 for name,data in outputs.items():
  report+=['## '+('Passage-only' if name=='passage_only' else 'Gemini/Groq auto chain (provider counts are actual run results)'), '']
  if name=='llm_auto' and set(data['metrics']['provider_counts']).issubset({'passage_fallback','retrieval_refusal'}):report.append('No provider key was configured in this run; no live LLM generation occurred. This section reports the auto chain falling through to passage fallback/refusal.\n')
  report += [f"- **{k}:** {v}" for k,v in data['metrics'].items()]
  report.append('')
 rerank=json.loads((RESULTS/'reranker_trial.json').read_text()) if (RESULTS/'reranker_trial.json').exists() else {}
 report+=['## Before/after context','','Before threshold/lexical tuning: hit@5 0.80, MRR 0.4767, refusal accuracy 0.50 (recorded prior run). After values appear above; differences are reported without smoothing. The confidence/overlap values were selected on the 15-question development set; its 15/15 accuracy is the tuning-set score, not an independent generalization estimate.','',f"Cross-encoder trial: {rerank.get('result','not run')} ({rerank.get('decision','')})",'']
 (RESULTS/'report.md').write_text('\n'.join(report),encoding='utf-8')
 try:make_chart(outputs)
 except Exception as exc:(RESULTS/'chart_status.txt').write_text(f'Chart not generated: {type(exc).__name__}: {exc}')
 print(json.dumps({n:v['metrics'] for n,v in outputs.items()},indent=2))

def make_chart(outputs):
 from PIL import Image,ImageDraw,ImageFont
 W,H=1200,680;im=Image.new('RGB',(W,H),'#f6f8fb');d=ImageDraw.Draw(im)
 try:font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',21);title=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',34)
 except Exception:font=ImageFont.load_default();title=font
 d.text((50,35),'HeapMind evaluation: baseline vs tuned',fill='#102a43',font=title)
 labels=['Hit@5','MRR','Refusal accuracy','Citation validity','Sentence support'];base=[.8,.4767,.5,None,None];after=[outputs['llm_auto']['metrics'].get(k) for k in ['hit@5','mrr','refusal_accuracy','citation_validity','sentence_support']]
 x0=320;scale=740
 for i,label in enumerate(labels):
  y=130+i*100;d.text((50,y+5),label,fill='#243b53',font=font)
  d.rectangle((x0,y,x0+scale,y+28),fill='#e4eaf0')
  if base[i] is not None:
   d.rectangle((x0,y,x0+scale*base[i],y+28),fill='#829ab1');d.text((x0+scale*base[i]+8,y+3),f'{base[i]:.2f} before',fill='#334e68',font=font)
  if after[i] is not None:
   d.rectangle((x0,y+38,x0+scale*after[i],y+66),fill='#2f80ed');d.text((x0+scale*after[i]+8,y+40),f'{after[i]:.2f} after',fill='#102a43',font=font)
 d.text((50,630),'Grey: previous run · Blue: tuned run (auto chain fell through to passage mode here) · N/A means no prior baseline.',fill='#486581',font=font)
 im.save(RESULTS/'metrics_comparison.png')
if __name__=='__main__':main()
