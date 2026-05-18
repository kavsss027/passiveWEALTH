class AppError(Exception):
    """Base application exception"""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class DataIngestionError(AppError):
    def __init__(self, message: str):
        super().__init__(message, code="INGESTION_ERROR")

class NormalizationError(AppError):
    def __init__(self, message: str):
        super().__init__(message, code="NORMALIZATION_ERROR")

class CalculationError(AppError):
    def __init__(self, message: str):
        super().__init__(message, code="CALCULATION_ERROR")

class DatabaseError(AppError):
    def __init__(self, message: str):
        super().__init__(message, code="DATABASE_ERROR")

class ResourceNotFoundError(AppError):
    def __init__(self, message: str):
        super().__init__(message, code="NOT_FOUND")

class ValidationError(AppError):
    def __init__(self, message: str):
        super().__init__(message, code="VALIDATION_ERROR")
