from fastapi import HTTPException
from typing import List, Tuple
from app.business_hour.service import BusinessHourService
from app.crud import BaseCRUDService
from app.report.enum import ReportStatus
from app.store_status.enum import ActivityStatus
from app.redis import redis_cache
from .report_item_service import ReportItemService
from app.store.service import StoreService
from app.store_status.service import StoreStatusService
from .model import Report, ReportItem
from sqlalchemy.orm import Session
from app.database import engine
from datetime import datetime, timedelta
import pytz
import csv
import io
from fastapi.responses import StreamingResponse
from redis import Redis
from app.config import Config

class ReportService(BaseCRUDService[Report]):
    def __init__(self, store_service: StoreService, status_service: StoreStatusService, business_hour_service: BusinessHourService, report_item_service: ReportItemService):
        super().__init__(Report)
        self.store_service = store_service
        self.status_service = status_service
        self.business_hour_service = business_hour_service
        self.report_item_service = report_item_service
        self.redis_client = Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=Config.REDIS_DB)

    def _calculate_uptime_downtime(self, business_hours, store_statuses, start_date: datetime, end_date: datetime) -> Tuple[int, int, int]:
        total_uptime, total_downtime, expected_uptime = 0, 0, 0
        current_date = start_date.date()
        total_duration = (end_date - start_date).total_seconds() / 60

        #Iterate through each day in the date range
        while current_date <= end_date.date():
            day_of_week = current_date.weekday()

            #Filter business hours for the current day of the week
            day_business_hours = [
                bh for bh in business_hours if bh.day_of_week.value == day_of_week]

            #Iterate through each business hour in the day
            for bh in day_business_hours:
                start_datetime = max(datetime.combine(current_date, bh.start_time), start_date)
                end_datetime = min(datetime.combine(current_date, bh.end_time), end_date)
                
                if end_datetime <= start_datetime:
                    #add a day to end_datetime
                    end_datetime += timedelta(days=1)

                #Calculate the duration of the business hour period
                period_duration = min((end_datetime - start_datetime).total_seconds() / 60, total_duration - expected_uptime)
                expected_uptime += period_duration

                #Filter store statuses for the current business hour period
                period_status_reports = [sr for sr in store_statuses if start_datetime <= sr.timestamp <= end_datetime]

                #If there are no store statuses for the current business hour period, add the duration to downtime
                if not period_status_reports:
                    total_downtime += period_duration
                    continue

                #Initialize the last check time and status
                #Assume the first store status is inactive
                last_check_time, last_status = start_datetime, False

                #Iterate through each store status in the current business hour period
                for sr in period_status_reports:
                    duration = (sr.timestamp - last_check_time).total_seconds() / 60
                    #if the last status is active, add the duration to uptime, otherwise add it to downtime
                    total_uptime += duration if last_status else 0
                    total_downtime += duration if not last_status else 0

                    last_check_time = sr.timestamp
                    last_status = (sr.status == ActivityStatus.ACTIVE)

                final_duration = (end_datetime - last_check_time).total_seconds() / 60
                #if the last status is active, add the duration to uptime, otherwise add it to downtime
                total_uptime += final_duration if last_status else 0
                total_downtime += final_duration if not last_status else 0

            current_date += timedelta(days=1)

        return int(total_uptime), int(total_downtime), int(expected_uptime)

    def generate_report(self, report_id: int) -> None:
        with Session(engine) as db:
            stores = self.store_service.findAllBy(db, limit=20000)
            self._process_stores_in_batches(db, stores, report_id)
            self.mark_report_as_ready(report_id)
           
    def _process_stores_in_batches(self, db: Session, stores: List, report_id: int, batch_size: int = 1000):
        report_items = []
        for store in stores:
            report_item = self._generate_store_report(db, store, report_id)
            report_items.append(report_item)
            
            if len(report_items) >= batch_size:
                self.report_item_service.createMultiple(db, objs_in=report_items)
                report_items = []

        if report_items:
            self.report_item_service.createMultiple(db, objs_in=report_items)

    def _generate_store_report(self, db: Session, store, report_id: int) -> dict:
        #adjust current time as per the requirement
        current_time = datetime.strptime("2023-01-19 08:03:07.391994", "%Y-%m-%d %H:%M:%S.%f").astimezone(pytz.UTC)
        one_hour_ago = current_time - timedelta(hours=1)
        one_day_ago = current_time - timedelta(days=1)
        one_week_ago = current_time - timedelta(weeks=1)

        business_hours = self.business_hour_service.findAllBy(db, limit=10000, store_id=store.id)

        store_statuses = self.status_service.findAllByAttributes(db, limit=10000, store_id=store.id, timestamp={'$gte': one_week_ago})
        store_statuses.sort(key=lambda x: x.timestamp)

        store_statuses_last_hour = [sr for sr in store_statuses if one_hour_ago <= sr.timestamp <= current_time]
        store_statuses_last_day = [sr for sr in store_statuses if one_day_ago <= sr.timestamp <= current_time]
        store_statuses_last_week = [sr for sr in store_statuses if one_week_ago <= sr.timestamp <= current_time]    

        uptime_last_hour, downtime_last_hour, expected_uptime_last_hour = self._calculate_uptime_downtime(business_hours, store_statuses_last_hour, one_hour_ago, current_time)
        uptime_last_day, downtime_last_day, expected_uptime_last_day = self._calculate_uptime_downtime(business_hours, store_statuses_last_day, one_day_ago, current_time)
        uptime_last_week, downtime_last_week, expected_uptime_last_week = self._calculate_uptime_downtime(business_hours, store_statuses_last_week, one_week_ago, current_time)

        return {
            "store_id": store.id,
            "report_id":report_id,
            "uptime_last_hour":uptime_last_hour,
            "uptime_last_day":uptime_last_day,
            "uptime_last_week":uptime_last_week,
            "downtime_last_hour":downtime_last_hour,
            "downtime_last_day":downtime_last_day,
            "downtime_last_week":downtime_last_week,
            "created_by":"system",
            "updated_by":"system"
        }

    def mark_report_as_ready(self, report_id: int) -> None:
        with Session(engine) as db:
            self.findAndUpdate(db, filter_by={"id":report_id}, update_data={"status":ReportStatus.READY,"generated_at":datetime.now().astimezone(pytz.UTC)})

    def mark_report_as_failed(self, report_id: int) -> None:
        with Session(engine) as db:
            self.findAndUpdate(db, filter_by={"id":report_id}, update_data={"status":ReportStatus.FAILED})
    
    def prepare_report(self) -> int:
        with Session(engine) as db:
            report = {
                "status": ReportStatus.PENDING,
                "requested_at": datetime.now().astimezone(pytz.UTC),

                "created_by":"system",
                "updated_by":"system"
            }
            return self.create(db, obj_in=report).id
        
    def get_report(self, report_id: int):
        with Session(engine) as db:
            report = self.findOneById(db, report_id)
            if report is None:
                raise HTTPException(status_code=404, detail="Report not found")
            if report.status == ReportStatus.FAILED:
                return "Failed"
            if report.status != ReportStatus.READY:
                return "Running"
            
            reportItems = self.report_item_service.findAllBy(db, limit=20000, report_id=report.id)
            return StreamingResponse(self._generate_csv(reportItems), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=report_{report_id}.csv"})
        
    def _generate_csv(self, report_items: List[ReportItem]):
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        
        writer.writerow(['store_id', 'uptime_last_hour', 'uptime_last_day', 'uptime_last_week', 'downtime_last_hour', 'downtime_last_day', 'downtime_last_week'])
        
        for row in report_items:
            writer.writerow([
                row.store_id, 
                round(row.uptime_last_hour, 2), 
                round(row.uptime_last_day/60, 2), 
                round(row.uptime_last_week/60, 2), 
                round(row.downtime_last_hour, 2), 
                round(row.downtime_last_day/60, 2), 
                round(row.downtime_last_week/60, 2)
            ])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

              