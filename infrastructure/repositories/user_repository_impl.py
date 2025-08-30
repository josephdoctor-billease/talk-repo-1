from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
from domain.entities.user import User
from domain.value_objects.user_id import UserId
from domain.value_objects.email import Email
from domain.repositories.user_repository import UserRepository
from infrastructure.database.models import UserModel


class UserRepositoryImpl(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    def _model_to_entity(self, model: UserModel) -> User:
        return User(
            id=UserId(model.id),
            email=Email(model.email),
            username=model.username,
            hashed_password=model.hashed_password,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _entity_to_model(self, entity: User) -> UserModel:
        return UserModel(
            id=str(entity.id),
            email=str(entity.email),
            username=entity.username,
            hashed_password=entity.hashed_password,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
    
    async def create(self, user: User) -> User:
        model = self._entity_to_model(user)
        self.session.add(model)
        try:
            await self.session.flush()
            await self.session.refresh(model)
            return self._model_to_entity(model)
        except IntegrityError as e:
            # Don't manually rollback - let the session dependency handle it
            if "email" in str(e):
                raise ValueError(f"User with email {user.email} already exists")
            elif "username" in str(e):
                raise ValueError(f"User with username {user.username} already exists")
            raise e
    
    async def get_by_id(self, user_id: UserId) -> Optional[User]:
        stmt = select(UserModel).where(UserModel.id == str(user_id))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None
    
    async def get_by_email(self, email: Email) -> Optional[User]:
        stmt = select(UserModel).where(UserModel.email == str(email))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None
    
    async def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(UserModel).where(UserModel.username == username)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None
    
    async def update(self, user: User) -> User:
        stmt = (
            update(UserModel)
            .where(UserModel.id == str(user.id))
            .values(
                email=str(user.email),
                username=user.username,
                hashed_password=user.hashed_password,
                is_active=user.is_active,
                updated_at=user.updated_at
            )
            .returning(UserModel)
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one()
        return self._model_to_entity(model)
    
    async def delete(self, user_id: UserId) -> bool:
        stmt = delete(UserModel).where(UserModel.id == str(user_id))
        result = await self.session.execute(stmt)
        return result.rowcount > 0
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        stmt = select(UserModel).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]
    
    async def exists_by_email(self, email: Email) -> bool:
        stmt = select(UserModel.id).where(UserModel.email == str(email))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    async def exists_by_username(self, username: str) -> bool:
        stmt = select(UserModel.id).where(UserModel.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None