from enum import Enum

class ReportStatus(Enum):
    PENDING = "pending"
    READY = "ready"
    FAILED = "failed"