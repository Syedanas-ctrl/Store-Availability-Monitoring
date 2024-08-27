from .enum import ActivityStatus
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, BigInteger
from sqlalchemy.orm import relationship
from ..base import BaseAudit

class StoreStatus(BaseAudit):
    __tablename__ = 'store_status'

    store_id = Column(BigInteger, ForeignKey('stores.id'))
    timestamp = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(ActivityStatus))
    store = relationship('Store', back_populates='status_reports')

    #I think its a good idea to only index this for a week. based on business requirements
    __table_args__ = (
        Index('ix_store_status_store_id_timestamp', 'store_id', 'timestamp'),
    )