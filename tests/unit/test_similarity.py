import pytest
from app.services.recommendation_service import calculate_similarity_score

class MockProfile:
    def __init__(self, tag_scores):
        self.tag_scores = tag_scores

class MockItem:
    def __init__(self, tags):
        self.tags = tags

def test_similarity_score_exact_match():
    # Jaccard similarity of identical sets is 1.0
    profile = MockProfile({"culture": 5, "history": 3})
    item = MockItem(["culture", "history"])
    assert calculate_similarity_score(profile, item) == 1.0

def test_similarity_score_no_match():
    # Jaccard similarity of disjoint sets is 0.0
    profile = MockProfile({"culture": 5, "history": 3})
    item = MockItem(["nature", "adventure"])
    assert calculate_similarity_score(profile, item) == 0.0

def test_similarity_score_partial_match():
    # Jaccard similarity: intersection / union
    # User: culture, history (2 tags)
    # Item: history, nature (2 tags)
    # Intersection: history (1)
    # Union: culture, history, nature (3)
    # Score: 1/3 = 0.333...
    profile = MockProfile({"culture": 5, "history": 3})
    item = MockItem(["history", "nature"])
    score = calculate_similarity_score(profile, item)
    assert abs(score - 0.3333333333333333) < 0.0001

def test_similarity_score_duplicate_tags():
    # Item has duplicate tags, should be treated as a set
    profile = MockProfile({"culture": 5, "history": 3})
    item = MockItem(["history", "history", "history", "nature"])
    score = calculate_similarity_score(profile, item)
    assert abs(score - 0.3333333333333333) < 0.0001

def test_similarity_score_case_insensitivity():
    # Tags should be compared case-insensitively
    profile = MockProfile({"CULTURE": 5, "History": 3})
    item = MockItem(["culture", "HISTORY"])
    score = calculate_similarity_score(profile, item)
    assert score == 1.0

def test_similarity_score_empty_tags():
    # Item has no tags
    profile = MockProfile({"culture": 5})
    item = MockItem([])
    assert calculate_similarity_score(profile, item) == 0.0

def test_similarity_score_empty_profile_tags():
    # Profile has no tags
    profile = MockProfile({})
    item = MockItem(["culture"])
    assert calculate_similarity_score(profile, item) == 0.0

def test_similarity_score_null_item_tags():
    # Item tags is None
    profile = MockProfile({"culture": 5})
    item = MockItem(None)
    assert calculate_similarity_score(profile, item) == 0.0

def test_similarity_score_null_profile():
    # Profile is None
    item = MockItem(["culture"])
    assert calculate_similarity_score(None, item) == 0.0
