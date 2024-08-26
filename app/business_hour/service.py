from app.crud import BaseCRUDService
from .model import BusinessHour
from sqlalchemy.orm import Session

class BusinessHourService(BaseCRUDService[BusinessHour]):
    def __init__(self):
        super().__init__(BusinessHour)
