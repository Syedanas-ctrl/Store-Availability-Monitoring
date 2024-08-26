from app.crud import BaseCRUDService
from .model import StoreStatus
from sqlalchemy.orm import Session

class StoreStatusService(BaseCRUDService[StoreStatus]):
    def __init__(self):
        super().__init__(StoreStatus)
