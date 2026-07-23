import pytest
from unittest.mock import patch
from app.models.user_activity import ItemType

@patch("app.api.v1.recommendations.generate_recommendations")
def test_get_recommendations_success(mock_generate, as_user):
    # Mock the return value of the recommendation service
    mock_generate.return_value = [
        {"id": "test-uuid-1", "type": "site", "name": "Pashupatinath", "score": 9.5, "reason": "High rating"},
        {"id": "test-uuid-2", "type": "festival", "name": "Dashain", "score": 8.0, "reason": "Trending"}
    ]
    
    response = as_user.get("/api/v1/recommendations?limit=10")
    
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) == 2
    assert data["recommendations"][0]["name"] == "Pashupatinath"
    mock_generate.assert_called_once()

@patch("app.api.v1.recommendations.generate_recommendations")
def test_get_recommendations_with_filters(mock_generate, as_user):
    mock_generate.return_value = []
    
    response = as_user.get(
        "/api/v1/recommendations?limit=5&latitude=27.7&longitude=85.3&item_type=site"
    )
    
    assert response.status_code == 200
    mock_generate.assert_called_once()
    kwargs = mock_generate.call_args.kwargs
    assert kwargs["lat"] == 27.7
    assert kwargs["lon"] == 85.3
    assert kwargs["limit"] == 5
    assert kwargs["item_type"] == ItemType.site

def test_get_recommendations_requires_auth(client):
    response = client.get("/api/v1/recommendations")
    assert response.status_code == 401
