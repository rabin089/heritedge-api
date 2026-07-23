import pytest
from app.services.recommendation_service import calculate_category_score

class MockProfile:
    def __init__(self, category_scores):
        self.category_scores = category_scores

class MockCategoryEnum:
    def __init__(self, value):
        self.value = value

class MockItem:
    def __init__(self, category):
        self.category = category

def test_category_score_exact_match():
    # Category score is normalized by 10.0
    profile = MockProfile({"temple": 8.0, "museum": 2.0})
    item = MockItem("temple")
    score = calculate_category_score(profile, item)
    assert score == 0.8

def test_category_score_cap():
    # Category score should be capped at 1.0 (10.0 / 10.0)
    profile = MockProfile({"temple": 15.0})
    item = MockItem("temple")
    score = calculate_category_score(profile, item)
    assert score == 1.0

def test_category_score_no_match():
    # Item category not in profile
    profile = MockProfile({"temple": 8.0})
    item = MockItem("museum")
    score = calculate_category_score(profile, item)
    assert score == 0.0

def test_category_score_empty_profile_scores():
    # Profile has no category scores
    profile = MockProfile({})
    item = MockItem("temple")
    score = calculate_category_score(profile, item)
    assert score == 0.0

def test_category_score_null_profile():
    # Profile is None
    item = MockItem("temple")
    assert calculate_category_score(None, item) == 0.0

def test_category_score_null_item_category():
    # Item category is None
    profile = MockProfile({"temple": 8.0})
    item = MockItem(None)
    assert calculate_category_score(profile, item) == 0.0

def test_category_score_enum_category():
    # Item category is an Enum
    profile = MockProfile({"temple": 5.0})
    item = MockItem(MockCategoryEnum("temple"))
    score = calculate_category_score(profile, item)
    assert score == 0.5

def test_category_score_case_insensitivity():
    # Item category is uppercase, profile is lowercase
    profile = MockProfile({"temple": 6.0})
    item = MockItem("TEMPLE")
    score = calculate_category_score(profile, item)
    assert score == 0.6
