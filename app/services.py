# import all services from here
from app.report.report_item_service import ReportItemService
from app.report.report_service import ReportService
from .store.service import StoreService
from .store_status.service import StoreStatusService
from .business_hour.service import BusinessHourService

status_service = StoreStatusService()
business_hour_service = BusinessHourService()
store_service = StoreService(status_service, business_hour_service)
report_item_service = ReportItemService()
report_service = ReportService(store_service, status_service, business_hour_service, report_item_service)
