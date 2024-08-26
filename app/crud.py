from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Generic, TypeVar, Type, List, Optional, Dict, Any
from .base import BaseAudit

T = TypeVar('T', bound=BaseAudit)


class BaseCRUDService(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    def findOne(self, db: Session, **kwargs) -> Optional[T]:
        return db.query(self.model).filter_by(**kwargs).first()

    def findOneBy(self, db: Session, **kwargs) -> Optional[T]:
        return self.findOne(db, **kwargs)

    def findOneById(self, db: Session, id: int) -> Optional[T]:
        return db.query(self.model).filter(self.model.id == id).first()

    def findOrCreate(self, db: Session, defaults: Dict[str, Any] = None, **kwargs) -> T:
        instance = self.findOne(db, **kwargs)
        if instance:
            return instance
        params = {**kwargs, **(defaults or {})}
        return self.create(db, params)

    def findAll(self, db: Session, skip: int = 0, limit: int = 100) -> List[T]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def findAllBy(self, db: Session, skip: int = 0, limit: int = 100, **kwargs) -> List[T]:
        return db.query(self.model).filter_by(**kwargs).offset(skip).limit(limit).all()

    def findAllByAttributes(self, db: Session, skip: int = 0, limit: int = 100, **kwargs) -> List[T]:
        query = db.query(self.model)

        for key, value in kwargs.items():
            column = getattr(self.model, key)
            if isinstance(value, dict):
                for operator, operand in value.items():
                    if operator == '$eq':
                        query = query.filter(column == operand)
                    elif operator == '$ne':
                        query = query.filter(column != operand)
                    elif operator == '$gt':
                        query = query.filter(column > operand)
                    elif operator == '$gte':
                        query = query.filter(column >= operand)
                    elif operator == '$lt':
                        query = query.filter(column < operand)
                    elif operator == '$lte':
                        query = query.filter(column <= operand)
                    elif operator == '$in':
                        query = query.filter(column.in_(operand))
                    elif operator == '$like':
                        query = query.filter(column.like(f'%{operand}%'))
                    elif operator == '$ilike':
                        query = query.filter(column.ilike(f'%{operand}%'))
            else:
                query = query.filter(column == value)
        
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: dict) -> T:
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def createMultiple(self, db: Session, objs_in: List[dict]) -> List[T]:
        db_objs = [self.model(**obj_in) for obj_in in objs_in]
        db.add_all(db_objs)
        db.commit()
        for db_obj in db_objs:
            db.refresh(db_obj)
        return db_objs

    def findAndUpdate(self, db: Session, filter_by: dict, update_data: dict) -> Optional[T]:
        instance = self.findOneBy(db, **filter_by)
        if instance:
            for key, value in update_data.items():
                setattr(instance, key, value)
            db.commit()
            db.refresh(instance)
        return instance

    def updateMultiple(self, db: Session, filter_by: dict, update_data: dict) -> int:
        return db.query(self.model).filter_by(**filter_by).update(update_data)

    def delete(self, db: Session, id: int, soft: bool = True) -> Optional[T]:
        obj = self.findOneById(db, id)
        if obj:
            if soft:
                setattr(obj, 'is_deleted', True)
                db.commit()
            else:
                db.delete(obj)
                db.commit()
        return obj

    def count(self, db: Session, **kwargs) -> int:
        return db.query(func.count(self.model.id)).filter_by(**kwargs).scalar()
