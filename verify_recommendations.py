import os
from dotenv import load_dotenv

# Load env before importing app
load_dotenv(".env.development")
load_dotenv(".env")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.user import User
from app.models.heritage_site import HeritageSite
from app.models.festival import Festival
from app.models.intangible_heritage import IntangibleHeritage
from app.models.contribution import Contribution
from app.models.site_review import SiteReview
from app.models.festival_interaction import FestivalReaction, FestivalReminder, FestivalStory
from app.models.user_activity import UserActivity, ItemType, ActionType
from app.models.user_interest_profile import UserInterestProfile
from app.models.recommendation_history import RecommendationHistory
from app.services.activity_service import record_activity
from app.services.recommendation_service import generate_recommendations
import uuid

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("No DATABASE_URL found.")
    exit(1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def verify():
    db = SessionLocal()
    
    print("Creating dummy user for recommendations test...")
    user_id = uuid.uuid4()
    dummy_user = User(
        id=user_id,
        email=f"test_rec_{user_id}@example.com",
        name="Test Recommender"
    )
    db.add(dummy_user)
    db.commit()
    
    print(f"Created Dummy User: {dummy_user.email}")
    
    # Check if there are sites/festivals
    site = db.query(HeritageSite).first()
    festival = db.query(Festival).first()
    
    if site:
        print(f"Simulating activity for Site: {site.name}")
        record_activity(db, user_id, site.id, ItemType.site, ActionType.view)
        record_activity(db, user_id, site.id, ItemType.site, ActionType.favorite)
    
    if festival:
        print(f"Simulating activity for Festival: {festival.name}")
        record_activity(db, user_id, festival.id, ItemType.festival, ActionType.bookmark)
        
    print("Generating recommendations...")
    recommendations = generate_recommendations(db, user_id, limit=5)
    
    print("\n--- TOP RECOMMENDATIONS ---")
    for r in recommendations:
        print(f"{r['score']} | {r['type']} | {r['name']} -> {r['reason']}")
    
    print("Verification complete.")
    db.close()

if __name__ == "__main__":
    verify()
