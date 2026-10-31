# English narration

This is HeapMind, a study assistant for one topic: heaps and heap sort. You ask it a question, and it answers only from the MIT six-oh-oh-six, Lecture 4 notes and transcript that I gave it. If the answer isn't in there, it says so, instead of guessing.

Quick refresher on the topic. A heap is an array that we read as a nearly complete binary tree. In a max-heap, every parent is at least as big as its children, so the biggest value always sits at the root. That's what makes it a good fit for a priority queue.

Heap sort builds on that. First, build a max-heap from the array. You do that by calling max-heapify on each internal node, from the bottom up to the root, and the lecture shows this takes linear time. Then repeat: swap the root with the last element of the heap, shrink the heap by one, and fix the root again. The sorted values pile up at the end of the array.

Here's how the app finds its answers. The lecture PDFs are split into small chunks, and every chunk keeps its page number. A question is searched two ways: by meaning, with sentence embeddings, and by keywords, with BM25. Reciprocal rank fusion then merges the two rankings. The top passages go to Gemini to write the answer, with Groq as a backup. And if both are down, the app simply shows the passages themselves.

In the app, you can choose English, Hindi or Hinglish, ask for a beginner-friendly explanation, or switch to quiz mode. Every answer lists its source passages and page numbers. Ask something outside the lecture, and it tells you that it isn't covered. And if a question tries to sneak in instructions, the app treats that text as data, not as a command.

For testing, I tuned the refusal threshold on a separate set of fifteen questions, then ran a thirty-question evaluation. The app correctly refused all ten out-of-scope and adversarial questions. Retrieval is weaker, though: the right page shows up in the top five results for about eighty percent of in-scope questions. This is a small test set, so treat these numbers as indicative, not definitive.

The source material is MIT OpenCourseWare, six-oh-oh-six, Introduction to Algorithms, Fall 2011, Lecture 4, licensed under Creative Commons BY-NC-SA. Thanks for watching.
