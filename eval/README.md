# Evaluation

`questions.json` contains the 30 held-out evaluation questions (20 in-scope, 5 out-of-scope, 5 adversarial) with source chunk IDs where applicable. `dev_questions.json` is a distinct 15-question threshold-tuning set. Run:

```bash
python eval/tune_threshold.py
python eval/run_eval.py
```

The report includes hit@5, MRR, refusal accuracy, citation validity, and a rule-based sentence-support check. Faithfulness scores are computed on non-refusal response rows. `llm_auto` invokes Gemini → Groq when credentials and model names are available; otherwise provider counts identify the actual fallback used. Use `python scripts/live_provider_test.py` for one provider smoke test after credentials are configured.
