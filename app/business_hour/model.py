from sqlalchemy import Column, Enum, Time, ForeignKey, Index, BigInteger
from sqlalchemy.orm import relationship, validates
from ..base import BaseAudit
from enum import Enum as PyEnum
from datetime import datetime
import pytz

class DayOfWeek(PyEnum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

class BusinessHour(BaseAudit):
    __tablename__ = 'business_hours'
    
    store_id = Column(BigInteger, ForeignKey('stores.id'), nullable=False)
    day_of_week = Column(Enum(DayOfWeek))
    start_time = Column(Time(timezone=True), nullable=False)
    end_time = Column(Time(timezone=True), nullable=False)

    store = relationship('Store', back_populates='business_hours')

    __table_args__ = (
        Index('ix_business_hours_store_id_day_of_week', 'store_id', 'day_of_week'),
    )

    def _get_default_time(self, is_start_time):
        print("self store",self.store)
        tz = pytz.timezone(self.store.timezone)
        now = datetime.now(tz)
        if is_start_time:
            default_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            default_time = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        return default_time.timetz()

    @validates('start_time', 'end_time')
    def set_default_times(self, key, value):
        if value is None:
            return self._get_default_time(key == 'start_time')
        return value

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.start_time is None:
            self.start_time = self._get_default_time(True)
        if self.end_time is None:
            self.end_time = self._get_default_time(False)