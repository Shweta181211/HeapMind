from ingest.ingest_pdfs import chunk_words, clean_text, TOKEN_RE

def test_clean_removes_linebreak_hyphen():
    assert clean_text("max-\nheap  property") == "maxheap property"

def test_chunk_overlap_and_bounds():
    words=[f"w{i}" for i in range(620)]
    chunks=chunk_words(" ".join(words),size=250,overlap=40)
    assert len(chunks)==3
    tokenized=[TOKEN_RE.findall(x) for x in chunks]
    assert all(200 <= len(x) <= 300 for x in tokenized)
    assert tokenized[0][-40:]==tokenized[1][:40]
