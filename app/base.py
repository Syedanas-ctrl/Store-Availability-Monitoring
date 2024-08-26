import uuid
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, String, BigInteger
from sqlalchemy.sql import func

Base = declarative_base()

#Note- all audit time stamps are in UTC
class BaseAudit(Base):
    __abstract__ = True

    id = Column(BigInteger, primary_key=True, default=lambda: uuid.uuid4().int & (1<<63)-1)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    created_by = Column(String, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    updated_by = Column(String, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String, nullable=True)

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"
