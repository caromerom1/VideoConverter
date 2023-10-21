from enum import Enum

class ConversionStatus(Enum):
    FAILED = "FAILED"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
