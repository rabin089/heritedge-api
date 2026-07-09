from pydantic import BaseModel
from typing import List

class RecommendationItem(BaseModel):
    id: str
    name: str
    type: str
    score: float
    reason: str

class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationItem]
