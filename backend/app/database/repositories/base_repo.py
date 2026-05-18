from typing import TypeVar, Generic, Type, Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import DeclarativeBase

ModelType = TypeVar("ModelType", bound=DeclarativeBase)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get_by_id(self, session: AsyncSession, id: int) -> Optional[ModelType]:
        result = await session.execute(select(self.model).filter(self.model.id == id))
        return result.scalars().first()

    async def create(self, session: AsyncSession, obj_in: dict[str, Any]) -> ModelType:
        db_obj = self.model(**obj_in)
        session.add(db_obj)
        await session.flush()
        return db_obj

    async def create_many(self, session: AsyncSession, objs_in: List[dict[str, Any]]) -> List[ModelType]:
        db_objs = [self.model(**obj) for obj in objs_in]
        session.add_all(db_objs)
        await session.flush()
        return db_objs
