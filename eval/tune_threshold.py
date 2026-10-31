"""Tune refusal thresholds only on a separate 15-question development set."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from rag.engine import HybridRetriever,should_refuse

def main():
 qs=json.loads((ROOT/'eval/dev_questions.json').read_text())
 if len(qs)!=15:raise SystemExit(f'Expected 15 dev questions, found {len(qs)}')
 retriever=HybridRetriever();observed=[]
 for q in qs:observed.append((q,retriever.retrieve(q['question'],k=5)))
 best=None
 for threshold_i in range(4,91):
  threshold=threshold_i/100
  for overlap_i in range(0,31,2):
   overlap=overlap_i/100
   correct=sum(should_refuse(h,q['question'],threshold,overlap)==q['expected_refusal'] for q,h in observed)
   score=correct/len(qs)
   candidate=(score,threshold,overlap)
   if best is None or candidate[0]>best[0] or (candidate[0]==best[0] and candidate[1]>best[1]):best=candidate
 score,threshold,overlap=best
 out={'threshold':threshold,'min_overlap':overlap,'dev_accuracy':score,'dev_questions':len(qs),'dev_scope_counts':{'in_scope':sum(q['category']=='in_scope' for q in qs),'out_of_scope':sum(q['category']=='out_of_scope' for q in qs)},'grid':{'thresholds':[.04,.90,.01],'min_overlap':[0,.30,.02]}}
 (ROOT/'data/refusal_thresholds.json').write_text(json.dumps(out,indent=2))
 (ROOT/'eval/results/threshold_tuning.json').write_text(json.dumps(out,indent=2))
 print(json.dumps(out,indent=2))
if __name__=='__main__':main()
