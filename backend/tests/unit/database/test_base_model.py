from sqlalchemy import Column, Integer
from app.database.models.base import Base, TimestampMixin

class DummyModel(Base, TimestampMixin):
    __tablename__ = "dummy"
    id = Column(Integer, primary_key=True)

def test_timestamp_mixin():
    assert hasattr(DummyModel, "created_at")
    assert hasattr(DummyModel, "updated_at")
