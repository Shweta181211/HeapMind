from rag.engine import reciprocal_rank_fusion

def test_rrf_rewards_consensus():
    ranked, scores=reciprocal_rank_fusion((["a","b"],["b","a"]))
    assert ranked[0] in {"a","b"}
    assert scores["a"] > 0 and scores["b"] > 0

def test_rrf_consensus_beats_single_low_rank():
    ranked,_=reciprocal_rank_fusion((["a","x","y"],["a","z","y"]))
    assert ranked[0]=="a"
