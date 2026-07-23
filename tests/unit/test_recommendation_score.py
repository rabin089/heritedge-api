import pytest
import uuid
from collections import namedtuple
from app.services.recommendation_service import generate_recommendations, WEIGHT_CATEGORY, WEIGHT_INTERACTION, WEIGHT_SIMILARITY, WEIGHT_LOCATION
from app.models.user_activity import ItemType

class MockDB:
    def __init__(self, profiles, activities, items):
        self.profiles = profiles
        self.activities = activities
        self.items = items
        self.added = []

    def query(self, model):
        class QueryBuilder:
            def __init__(self, db, model):
                self.db = db
                self.model = model
            def filter(self, *args):
                return self
            def first(self):
                if self.model.__name__ == 'UserInterestProfile':
                    return self.db.profiles
                return None
            def all(self):
                if self.model.__name__ == 'UserActivity':
                    return self.db.activities
                elif self.model.__name__ == 'HeritageSite':
                    return self.db.items.get('site', [])
                elif self.model.__name__ == 'Festival':
                    return self.db.items.get('festival', [])
                elif self.model.__name__ == 'IntangibleHeritage':
                    return self.db.items.get('intangible', [])
                return []
        return QueryBuilder(self, model)

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        pass

class MockProfile:
    def __init__(self, user_id, category_scores, tag_scores):
        self.user_id = user_id
        self.category_scores = category_scores
        self.tag_scores = tag_scores

class MockItem:
    def __init__(self, id, name, category, tags, lat, lon):
        self.id = id
        self.name = name
        self.category = category
        self.tags = tags
        self.latitude = lat
        self.longitude = lon

def test_generate_recommendations_ranking():
    user_id = uuid.uuid4()
    profile = MockProfile(user_id, {"temple": 10.0}, {"culture": 5})
    activities = []
    
    # Create two items. Item 1 matches category perfectly. Item 2 doesn't.
    item1 = MockItem(uuid.uuid4(), "Temple A", "temple", ["culture"], 27.0, 85.0)
    item2 = MockItem(uuid.uuid4(), "Museum B", "museum", ["art"], 28.0, 84.0)
    
    db = MockDB(profile, activities, {'site': [item1, item2]})
    
    recs = generate_recommendations(db, user_id, lat=27.0, lon=85.0, limit=10, item_type=ItemType.site)
    
    assert len(recs) == 2
    # Item 1 should have a higher score because it matches category and tags
    assert recs[0]["id"] == str(item1.id)
    assert recs[1]["id"] == str(item2.id)
    assert recs[0]["score"] > recs[1]["score"]

def test_generate_recommendations_explanation_category():
    user_id = uuid.uuid4()
    # High category preference
    profile = MockProfile(user_id, {"temple": 10.0}, {})
    item1 = MockItem(uuid.uuid4(), "Temple A", "temple", [], None, None)
    db = MockDB(profile, [], {'site': [item1]})
    
    recs = generate_recommendations(db, user_id)
    assert len(recs) == 1
    assert "matches your preferred heritage categories" in recs[0]["reason"]

def test_generate_recommendations_limit():
    user_id = uuid.uuid4()
    profile = MockProfile(user_id, {}, {})
    # Create 15 items
    items = [MockItem(uuid.uuid4(), f"Site {i}", "misc", [], None, None) for i in range(15)]
    db = MockDB(profile, [], {'site': items})
    
    recs = generate_recommendations(db, user_id, limit=5, item_type=ItemType.site)
    assert len(recs) == 5

def test_generate_recommendations_history_saved():
    user_id = uuid.uuid4()
    profile = MockProfile(user_id, {}, {})
    item1 = MockItem(uuid.uuid4(), "Temple A", "temple", [], None, None)
    db = MockDB(profile, [], {'site': [item1]})
    
    generate_recommendations(db, user_id)
    
    assert len(db.added) == 1
    assert db.added[0].__class__.__name__ == 'RecommendationHistory'
    assert db.added[0].user_id == user_id
    assert len(db.added[0].recommendations) == 1
