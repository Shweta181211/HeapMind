"""Make one real, source-grounded provider request; report provider only, never secrets."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from rag.engine import HybridRetriever,generate

def main():
 hits=HybridRetriever().retrieve('What is the max-heap property?',k=5)
 answer,provider=generate('What is the max-heap property?',hits,'English','answer',bypass_cache=True)
 print(f'provider={provider}')
 for line in answer.splitlines():
  if line.startswith('Provider status:'):print(line)
 print('response_contains_citation=',any(f'[{i}]' in answer for i in range(1,len(hits)+1)))
if __name__=='__main__':main()
