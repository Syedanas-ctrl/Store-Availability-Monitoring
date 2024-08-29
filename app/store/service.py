import random
from app.business_hour.model import DayOfWeek
from app.business_hour.service import BusinessHourService
from app.crud import BaseCRUDService
from app.store_status.enum import ActivityStatus
from app.store_status.model import StoreStatus
from app.store_status.service import StoreStatusService
from .model import Store
from sqlalchemy.orm import Session
from app.database import engine
from datetime import datetime, time
import pytz

class StoreService(BaseCRUDService[Store]):
    def __init__(self, store_status_service: StoreStatusService, business_hour_service: BusinessHourService):
        super().__init__(Store)
        self.store_status_service = store_status_service
        self.business_hour_service = business_hour_service

    def _is_time_within_hours(self, current_time: time, start_time: time, end_time: time) -> bool:
        current_time_utc = current_time.replace(tzinfo=pytz.UTC)
        start_time_utc = start_time.replace(tzinfo=pytz.UTC)
        end_time_utc = end_time.replace(tzinfo=pytz.UTC)
        
        return start_time_utc <= current_time_utc <= end_time_utc

    def log_store_statuses(self):
        with Session(engine) as db:
            batch_size = 1000
            statuses = []
            stores = self.findAll(db, limit=20000)
  
            for store in stores:
                current_time = datetime.now().astimezone(pytz.utc)
                business_hours = self.business_hour_service.findAllBy(db, limit=10000, store_id=store.id, day_of_week=DayOfWeek(current_time.weekday()))

                is_within_business_hours = any(
                    self._is_time_within_hours(current_time.time(), business_hour.start_time, business_hour.end_time)
                    for business_hour in business_hours
                )
                
                if is_within_business_hours:
                    statuses.append(
                        StoreStatus(
                            store_id=store.id,
                            timestamp=current_time,
                            status=random.choice(
                                [ActivityStatus.ACTIVE, ActivityStatus.INACTIVE]),

                            created_by="celery_poller",
                            updated_by="celery_poller",
                        )
                    )
                    if len(statuses) >= batch_size:
                        self.store_status_service.create(db, statuses)
                        statuses = []
            if statuses:
                self.store_status_service.create(db, statuses)
