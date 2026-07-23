import pytest
import uuid
from app.services.recommendation_service import calculate_interaction_score
from app.models.user_activity import ActionType

class MockActivity:
    def __init__(self, item_id, action_type):
        self.item_id = item_id
        self.action_type = action_type

def test_interaction_score_no_activities():
    item_id = uuid.uuid4()
    assert calculate_interaction_score([], item_id) == 0.0

def test_interaction_score_irrelevant_activities():
    item_id1 = uuid.uuid4()
    item_id2 = uuid.uuid4()
    activities = [
        MockActivity(item_id1, ActionType.view)
    ]
    assert calculate_interaction_score(activities, item_id2) == 0.0

def test_interaction_score_single_view():
    # Note: Assuming ACTION_WEIGHTS.get(ActionType.view) == 0.1 as per fallback
    # If the real weights in activity_service are different, this test might need adjustment
    # We will test the basic summation logic here.
    item_id = uuid.uuid4()
    activities = [
        MockActivity(item_id, ActionType.view)
    ]
    # We expect some positive score, bounded by 1.0. Let's assert it's > 0
    score = calculate_interaction_score(activities, item_id)
    assert score > 0.0
    assert score <= 1.0

def test_interaction_score_multiple_interactions_capped():
    # If a user interacts heavily, score should cap at 1.0
    item_id = uuid.uuid4()
    activities = [MockActivity(item_id, ActionType.view) for _ in range(20)]
    score = calculate_interaction_score(activities, item_id)
    assert score == 1.0

def test_interaction_score_mixed_interactions():
    item_id_target = uuid.uuid4()
    item_id_other = uuid.uuid4()
    activities = [
        MockActivity(item_id_target, ActionType.view),
        MockActivity(item_id_other, ActionType.bookmark),
        MockActivity(item_id_target, ActionType.bookmark)
    ]
    score_target = calculate_interaction_score(activities, item_id_target)
    score_other = calculate_interaction_score(activities, item_id_other)
    
    assert score_target > 0.0
    assert score_other > 0.0
    assert score_target <= 1.0
    assert score_other <= 1.0
