# HeapMind evaluation

Run: 2026-10-25T17:31:05.678740+00:00

Retriever: all-MiniLM-L6-v2 cosine + Okapi BM25 + RRF@60
Tuned refusal settings: {'threshold': 0.52, 'min_overlap': 0.3, 'dev_accuracy': 1.0, 'dev_questions': 15, 'dev_scope_counts': {'in_scope': 8, 'out_of_scope': 7}, 'grid': {'thresholds': [0.04, 0.9, 0.01], 'min_overlap': [0, 0.3, 0.02]}}
Provider counts: {'Gemini (cache)': 15, 'retrieval_refusal': 8, 'Gemini': 7}

Thirty questions: 20 in-scope, 5 out-of-scope, 5 adversarial. Retrieval metrics use the 20 source-labeled in-scope questions; refusal accuracy uses the labeled out-of-scope and adversarial items. Faithfulness is a rule-based lexical-support check, not human judgment.

## Results (Gemini, Groq fallback, passages as last resort)

- **hit@5:** 0.8
- **mrr:** 0.4766666666666667
- **refusal_accuracy:** 1.0
- **labeled_retrieval_questions:** 20
- **refusal_labeled_questions:** 10
- **citation_validity:** 0.8095238095238095
- **sentence_support:** 0.6298185941043084
- **provider_counts:** {'Gemini (cache)': 15, 'retrieval_refusal': 8, 'Gemini': 7}

## Before/after context

Before threshold/lexical tuning: hit@5 0.80, MRR 0.4767, refusal accuracy 0.50 (recorded prior run). After values appear above; differences are reported without smoothing. The confidence/overlap values were selected on the 15-question development set; its 15/15 accuracy is the tuning-set score, not an independent generalization estimate.

Cross-encoder trial: unavailable (Do not enable the reranker; no valid before/after reranking metric could be measured.)
