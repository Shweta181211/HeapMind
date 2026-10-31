# HeapMind

A small RAG app that answers questions about one topic, heaps and heap sort, using only the lecture material I gave it: MIT 6.006 Introduction to Algorithms (Fall 2011), Lecture 4, "Heaps and Heap Sort" (notes PDF + transcript PDF). If the answer isn't in those PDFs, it says "This is not covered in the lecture material." instead of guessing.

Project page (video, screenshots): https://huggingface.co/spaces/shweta1811/heapmind
Live app: https://9a30fb1638a81c74ab.gradio.live (temporary link; it only works while the app is running on my laptop)
Demo videos (English and Hindi) are in the Drive submission folder.

## What's inside

- `archive/`: the two source PDFs and a manifest of where they came from
- `ingest/`: PDF extraction and chunking (200-300 tokens, page number kept on every chunk)
- `rag/engine.py`: retrieval and answer generation
- `app.py`: the Gradio interface
- `eval/`: 15 dev questions (used to tune the refusal threshold) and a separate 30-question test set, plus results
- `tests/`: pytest suite
- `deliverables/`: slides, demo video (English, with Hindi version), screenshots

## How it works

1. Chunks are embedded with all-MiniLM-L6-v2 and stored in ChromaDB.
2. A question is searched twice, by embedding similarity and by BM25 keywords. Reciprocal rank fusion merges the two rankings.
3. If the best match is too weak (cosine below 0.52 or keyword overlap below 0.30), the app refuses.
4. Otherwise the top passages go to Gemini; Groq is the fallback; if both fail, the raw passages are shown. Each answer lists its sources with page numbers.
5. Text inside questions or passages is treated as data, so "ignore your instructions" style input doesn't change behaviour.

Extras: English / Hindi / Hinglish answers, beginner explanations, quiz mode, and a step-by-step heap visualizer.

## Results (30-question test set)

| Metric | Value |
|---|---|
| Right page in top 5 (in-scope questions) | 0.80 |
| MRR | 0.48 |
| Correct refusals (out-of-scope + adversarial) | 10 / 10 |
| Citation validity | 0.81 |
| Sentence support (rule-based, not human-checked) | 0.63 |

It's a small test set, so read these as rough indicators. Retrieval ranking is the weak spot. Full output is in `eval/results/report.md`.

## Run it yourself

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then add your own Gemini and Groq keys
python ingest/ingest_pdfs.py
python app.py
```

Tests: `pip install -r requirements-dev.txt && python -m pytest -q`
Evaluation: `python eval/run_eval.py`

The transcript has no timestamps, so citations use PDF page numbers.

## Notes and limitations

- The course page for this task names Erik Demaine and Srini Devadas; the supplied Lecture 4 files are MIT 6.006 Fall 2011. Check this against the task page.
- Hugging Face now requires a paid plan for Gradio Spaces, so the Space is a static project page and the live app runs separately.
- The free-tier Gemini/Groq keys are rate limited; the app caps each session at 15 questions per hour.

## Attribution

MIT OpenCourseWare, 6.006 Introduction to Algorithms, Fall 2011, Lecture 4. Licensed CC BY-NC-SA 4.0. This project is non-commercial.
