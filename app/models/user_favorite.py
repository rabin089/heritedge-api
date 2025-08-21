from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from app.core.database import Base


class UserFavorite(Base):
    __tablename__ = "user_favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    heritage_site_id = Column(Integer, ForeignKey("heritage_sites.id", ondelete="CASCADE"), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("user_id", "heritage_site_id", name="uq_user_site_fav"),
    )
