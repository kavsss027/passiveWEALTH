import os
from unittest import mock
from pydantic import ValidationError
import pytest
from app.core.config import Settings

def test_settings_load_from_env():
    with mock.patch.dict(os.environ, {"DATABASE_URL": "postgresql+asyncpg://test:test@localhost/testdb"}):
        settings = Settings()
        assert settings.DATABASE_URL == "postgresql+asyncpg://test:test@localhost/testdb"
        assert settings.ENVIRONMENT == "development"

def test_settings_missing_required():
    with mock.patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValidationError):
            Settings(_env_file=None)
