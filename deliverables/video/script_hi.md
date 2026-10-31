# Hindi voice-over script

नमस्ते। यह HeapMind है: एक RAG ऐप, जो केवल दिए गए lecture notes और transcript से जवाब देता है। ये स्रोत MIT 6.006 Introduction to Algorithms, Fall 2011, Lecture 4 — “Heaps and Heap Sort” के हैं। स्रोत में timestamps नहीं हैं, इसलिए citations lecture title और PDF page number से दिए जाते हैं।

Heap एक priority queue को implement करने का तरीका है। इसे array की तरह रखा जाता है और nearly complete binary tree के रूप में देखा जाता है। Max-heap में हर parent की key उसके बच्चों से कम नहीं होती, इसलिए सबसे बड़ा element root पर मिलता है।

MAX-HEAPIFY उस स्थिति को ठीक करता है जहाँ root पर heap property का एक violation हो और दोनों child subtrees पहले से max-heaps हों। BUILD-MAX-HEAP array के आखिरी internal node से root की ओर MAX-HEAPIFY चलाता है। Lecture का विश्लेषण बताता है कि यह bottom-up निर्माण O of n समय में होता है। Heap sort पहले max-heap बनाता है, फिर root maximum को array के अंतिम हिस्से में रखता है, heap का आकार घटाता है, और root को फिर ठीक करता है।

HeapMind के retrieval चरण में sentence embeddings और BM25 दोनों इस्तेमाल होते हैं। Reciprocal-rank fusion दोनों ranked lists को मिलाता है। जवाब Gemini से शुरू होता है, फिर उपलब्ध होने पर Groq आजमाया जाता है। अगर दोनों उपलब्ध न हों या विफल हों, ऐप retrieved lecture passages दिखाता है। कम confidence या कम lexical overlap पर ऐप कहता है: “This is not covered in the lecture material.” हर उत्तर के साथ स्रोत passage और page दिखते हैं।

नीचे app में English, Hindi और Hinglish modes, beginner explanation, quiz mode और heap visualizer देखें। Visualizer insert, extract-max, build-heap और heap sort के steps को tree और array में साथ दिखाता है।

इस छोटे evaluation में refusal threshold को अलग पंद्रह-question dev set पर tune किया गया। अलग तीस-question evaluation और इसकी सीमाएँ report में दर्ज हैं। ये metrics केवल इसी test set के हैं।

Attribution: MIT OpenCourseWare, 6.006 Introduction to Algorithms, Fall 2011, Lecture 4, “Heaps and Heap Sort.” कृपया instructor/course match को task page से verify करें।

## English translation

Hello. This is HeapMind: a RAG app that answers only from the supplied lecture notes and transcript. The sources are MIT 6.006 Introduction to Algorithms, Fall 2011, Lecture 4, “Heaps and Heap Sort.” The source has no timestamps, so citations use the lecture title and PDF page number.

A heap is one way to implement a priority queue. It is stored as an array and viewed as a nearly complete binary tree. In a max-heap, each parent key is at least as large as its children, so the largest element is at the root.

MAX-HEAPIFY repairs a possible violation at the root when both child subtrees are already max-heaps. BUILD-MAX-HEAP calls MAX-HEAPIFY from the last internal node up to the root. The lecture’s analysis shows this bottom-up construction takes O(n) time. Heap sort first builds a max-heap, moves the root maximum to the end of the array, shrinks the heap, and repairs the root again.

HeapMind combines sentence embeddings and BM25 retrieval. Reciprocal-rank fusion merges their rankings. Answer generation tries Gemini first, then Groq when configured. If generation is unavailable or fails, the app shows retrieved lecture passages. Low confidence or lexical overlap triggers the exact refusal “This is not covered in the lecture material.” Retrieved passages and page numbers are shown with the response.

The app includes English, Hindi, and Hinglish modes, beginner explanations, quiz mode, and a heap visualizer. It displays insert, extract-max, build-heap, and heap-sort steps in both tree and array form.

The refusal threshold was tuned on a separate 15-question development set. Results on a separate 30-question evaluation and its limitations are recorded in the report. These metrics apply only to that test set.

Attribution: MIT OpenCourseWare, 6.006 Introduction to Algorithms, Fall 2011, Lecture 4, “Heaps and Heap Sort.” Please verify the instructor/course match against the task page.
