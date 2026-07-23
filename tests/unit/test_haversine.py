import pytest
import math
from app.services.recommendation_service import haversine_distance

def test_haversine_distance_zero():
    # Distance between the same point should be 0
    assert haversine_distance(0.0, 0.0, 0.0, 0.0) == 0.0
    assert haversine_distance(27.7172, 85.3240, 27.7172, 85.3240) == 0.0

def test_haversine_distance_known_points():
    # Distance between Kathmandu (27.7172, 85.3240) and Pokhara (28.2096, 83.9856)
    # Approx 140-150 km
    dist = haversine_distance(27.7172, 85.3240, 28.2096, 83.9856)
    assert 140 < dist < 150

def test_haversine_distance_antipodes():
    # Distance between North Pole and South Pole
    # Should be approx half the Earth's circumference (Earth radius * pi)
    dist = haversine_distance(90.0, 0.0, -90.0, 0.0)
    expected = 6371 * math.pi
    assert math.isclose(dist, expected, rel_tol=0.01)

def test_haversine_distance_invalid_coordinates():
    # If any coordinate is None, it should return infinity
    assert haversine_distance(None, 0.0, 0.0, 0.0) == float('inf')
    assert haversine_distance(0.0, None, 0.0, 0.0) == float('inf')
    assert haversine_distance(0.0, 0.0, None, 0.0) == float('inf')
    assert haversine_distance(0.0, 0.0, 0.0, None) == float('inf')

def test_haversine_distance_very_large():
    # Points on the equator on opposite sides of the earth
    dist = haversine_distance(0.0, 0.0, 0.0, 180.0)
    expected = 6371 * math.pi
    assert math.isclose(dist, expected, rel_tol=0.01)
