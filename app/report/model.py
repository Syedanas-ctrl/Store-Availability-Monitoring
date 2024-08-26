from sqlalchemy import Column, Integer, ForeignKey, DateTime, BigInteger, Enum
from sqlalchemy.orm import relationship
from ..base import BaseAudit
from .enum import ReportStatus

class Report(BaseAudit):
    __tablename__ = 'reports'

    status = Column(Enum(ReportStatus), nullable=False)
    requested_at = Column(DateTime, nullable=False)
    generated_at = Column(DateTime, nullable=True)

    report_items = relationship('ReportItem', back_populates='report')

# all times will be in minutes
class ReportItem(BaseAudit):
    __tablename__ = 'report_items'

    report_id = Column(BigInteger, ForeignKey('reports.id'))
    store_id = Column(BigInteger, ForeignKey('stores.id'))
    uptime_last_hour = Column(Integer, nullable=True)
    uptime_last_day = Column(Integer, nullable=True)
    uptime_last_week = Column(Integer, nullable=True)

    downtime_last_hour = Column(Integer, nullable=True)
    downtime_last_day = Column(Integer, nullable=True)
    downtime_last_week = Column(Integer, nullable=True)

    store = relationship('Store', back_populates='report_items')
    report = relationship('Report', back_populates='report_items')
