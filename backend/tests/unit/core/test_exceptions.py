import pytest
from app.core.exceptions import AppError, DataIngestionError, NormalizationError, CalculationError, DatabaseError, ResourceNotFoundError, ValidationError

def test_app_error_base():
    err = AppError("Something went wrong", "TEST_CODE")
    assert err.message == "Something went wrong"
    assert err.code == "TEST_CODE"
    assert str(err) == "Something went wrong"

def test_data_ingestion_error():
    err = DataIngestionError("Failed to fetch")
    assert err.code == "INGESTION_ERROR"
    assert err.message == "Failed to fetch"

def test_validation_error():
    err = ValidationError("Invalid input")
    assert err.code == "VALIDATION_ERROR"
    assert err.message == "Invalid input"

def test_all_exceptions_catchable_as_app_error():
    errors = [
        DataIngestionError("e"),
        NormalizationError("e"),
        CalculationError("e"),
        DatabaseError("e"),
        ResourceNotFoundError("e"),
        ValidationError("e")
    ]
    for err in errors:
        with pytest.raises(AppError):
            raise err
