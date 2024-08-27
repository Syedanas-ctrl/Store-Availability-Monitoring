from sqlalchemy import Column, String, Index
from sqlalchemy.orm import relationship
from ..base import BaseAudit

# have taken timezone schema as store 
# store_id, timezone_str -> id, timezone
class Store(BaseAudit):
    __tablename__ = 'stores'

    timezone = Column(String, default='America/Chicago')
    status_reports = relationship('StoreStatus', back_populates='store')
    business_hours = relationship('BusinessHour', back_populates='store')
    report_items = relationship('ReportItem', back_populates='store')

    __table_args__ = (
        Index('ix_stores_id', 'id'),
    )
