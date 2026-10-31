from rag.engine import should_refuse

def test_refuses_when_no_retrieval():
    assert should_refuse([], threshold=0.35)

def test_refuses_low_similarity():
    assert should_refuse([{"confidence":0.2}], threshold=0.35)

def test_accepts_above_similarity_threshold():
    assert not should_refuse([{"confidence":0.8}], threshold=0.35)

def test_lexical_gate_refuses_unrelated_query():
    from rag.engine import should_refuse
    hit={"confidence":0.9,"text":"A max-heap stores the maximum key at its root."}
    assert should_refuse([hit],"How does AVL double rotation work?",threshold=.3,min_overlap=.1)
