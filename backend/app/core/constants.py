from enum import Enum

class ActionType(str, Enum):
    SPLIT = "SPLIT"
    BONUS = "BONUS"
    DIVIDEND = "DIVIDEND"

class Exchange(str, Enum):
    NSE = "NSE"
    BSE = "BSE"

class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class ImpactType(str, Enum):
    STRUCTURAL = "STRUCTURAL"
    REALIZED = "REALIZED"
