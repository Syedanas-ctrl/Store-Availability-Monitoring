import random
from app.business_hour.service import BusinessHourService
from app.crud import BaseCRUDService
from app.store_status.enum import ActivityStatus
from app.store_status.model import StoreStatus
from app.store_status.service import StoreStatusService
from .model import Store
from sqlalchemy.orm import Session
from app.database import engine
from datetime import datetime
import pytz

class StoreService(BaseCRUDService[Store]):
    def __init__(self, store_status_service: StoreStatusService, business_hour_service: BusinessHourService):
        super().__init__(Store)
        self.store_status_service = store_status_service
        self.business_hour_service = business_hour_service

    def log_store_statuses(self):
        with Session(engine) as db:
            batch_size = 1000;
            statuses = []
            stores = self.findAll(db)
            business_hours = self.business_hour_service.findAll(db)
            for store in stores:
                current_time = datetime.now(pytz.timezone(store.timezone))
                business_hour = next((bh for bh in business_hours if bh.store_id == store.id and bh.day_of_week == current_time.weekday()), None)
                if business_hour and business_hour.start_time <= current_time.time() <= business_hour.end_time:
                    statuses.append(StoreStatus(store_id=store.id, status=random.choice([ActivityStatus.ACTIVE, ActivityStatus.INACTIVE])))
                    if len(statuses) >= batch_size:
                        self.store_status_service.create(db, statuses)
                        statuses = []
            if statuses:
                self.store_status_service.create(db, statuses)


                