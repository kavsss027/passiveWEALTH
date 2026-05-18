from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.database.connection import get_db
from app.services.reconstruction_service import ReconstructionService
from app.services.wealth_service import WealthService
from app.services.timeline_service import TimelineService

def get_reconstruction_service() -> ReconstructionService:
    return ReconstructionService()

def get_wealth_service() -> WealthService:
    return WealthService()

def get_timeline_service() -> TimelineService:
    return TimelineService()
