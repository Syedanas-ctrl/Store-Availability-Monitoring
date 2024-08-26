from app.crud import BaseCRUDService
from .model import ReportItem

class ReportItemService(BaseCRUDService[ReportItem]):
    def __init__(self):
        super().__init__(ReportItem)
