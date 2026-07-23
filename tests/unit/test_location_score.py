import pytest
import math
from app.services.recommendation_service import calculate_location_score

class MockItem:
    def __init__(self, lat, lon):
        self.latitude = lat
        self.longitude = lon

def test_location_score_same_location():
    # distance = 0, score = 1 / (1 + 0) = 1.0
    item = MockItem(27.7172, 85.3240)
    score = calculate_location_score(27.7172, 85.3240, item)
    assert score == 1.0

def test_location_score_different_location():
    # User at (0, 0), item at (0, 1) -> distance is approx 111.32 km
    # Score = 1 / (1 + 111.32) approx 0.0089
    item = MockItem(0.0, 1.0)
    score = calculate_location_score(0.0, 0.0, item)
    assert 0.0 < score < 0.01

def test_location_score_null_user_location():
    # If user location is not provided, score should be 0.0
    item = MockItem(27.7172, 85.3240)
    assert calculate_location_score(None, 85.3240, item) == 0.0
    assert calculate_location_score(27.7172, None, item) == 0.0
    assert calculate_location_score(None, None, item) == 0.0

def test_location_score_null_item_location():
    # If item location is missing, score should be 0.0
    item1 = MockItem(None, 85.3240)
    item2 = MockItem(27.7172, None)
    item3 = MockItem(None, None)
    
    assert calculate_location_score(27.7172, 85.3240, item1) == 0.0
    assert calculate_location_score(27.7172, 85.3240, item2) == 0.0
    assert calculate_location_score(27.7172, 85.3240, item3) == 0.0

def test_location_score_very_far():
    # User at North pole, item at South pole
    # Distance is approx 20015 km
    item = MockItem(-90.0, 0.0)
    score = calculate_location_score(90.0, 0.0, item)
    assert score > 0.0
    assert score < 0.0001
