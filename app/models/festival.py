from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Text, Boolean, DateTime, ForeignKey, Enum, Integer
from sqlalchemy.dialects.postgresql import ARRAY, UUID, JSONB
from sqlalchemy.orm import relationship, backref
from app.core.database import Base
import enum
import uuid


class FestivalCategory(str, enum.Enum):
    religious = "religious"
    cultural = "cultural"
    national = "national"


class FestivalStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class DateDeterminationType(str, enum.Enum):
    fixed_gregorian = "fixed_gregorian"
    api_synced_lunar = "api_synced_lunar"
    crowdsourced_variable = "crowdsourced_variable"


class Festival(Base):
    __tablename__ = "festivals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    significance = Column(String)  # cultural meaning
    
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    nepali_date = Column(String)  # optional but powerful
    
    region = Column(String)
    locations = Column(JSONB)  # [LatLng] - multiple allowed
    
    category = Column(Enum(FestivalCategory))  # Religious, Cultural, National
    tags = Column(ARRAY(String))
    
    main_image = Column(String)
    gallery = Column(ARRAY(String))
    
    is_annual = Column(Boolean, default=False)
    views_count = Column(Integer, default=0)
    date_determination = Column(Enum(DateDeterminationType), default=DateDeterminationType.fixed_gregorian)
    last_verified_year = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    status = Column(Enum(FestivalStatus), default=FestivalStatus.pending)
    moderation_note = Column(String, nullable=True)

    # Relationships
    user = relationship("User")
    heritage_sites = relationship("HeritageSite", secondary="festival_heritage_sites", back_populates="festivals", overlaps="festival,heritage_site,heritage_site_associations,festival_associations")
    contributions = relationship("Contribution", back_populates="festival")
    reactions = relationship("FestivalReaction", back_populates="festival", cascade="all, delete-orphan")
    stories = relationship("FestivalStory", back_populates="festival", cascade="all, delete-orphan")
    reminders = relationship("FestivalReminder", back_populates="festival", cascade="all, delete-orphan")

    @property
    def contributor_id(self):
        return self.created_by

    @property
    def contributor_name(self):
        if self.user:
            return self.user.display_name or self.user.name or "Anonymous"
        return "Anonymous"


class FestivalHeritageSite(Base):
    __tablename__ = "festival_heritage_sites"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    festival_id = Column(UUID(as_uuid=True), ForeignKey("festivals.id"), nullable=False)
    heritage_site_id = Column(UUID(as_uuid=True), ForeignKey("heritage_sites.id"), nullable=False)
    
    # Additional relationship metadata
    relationship_type = Column(String, default="hosted_at")  # e.g., "hosted_at", "celebrates", "related_to"
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(String, nullable=False)
    
    # Relationships
    festival = relationship(
        "Festival",
        backref=backref("heritage_site_associations", overlaps="festivals,heritage_sites"),
        overlaps="heritage_sites,festivals",
    )
    heritage_site = relationship(
        "HeritageSite",
        backref=backref("festival_associations", overlaps="festivals,heritage_sites"),
        overlaps="heritage_sites,festivals",
    )
