from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src.models import CollectionConfig
from src.orchestrator import HorizonOrchestrator


def make_orchestrator(collection: CollectionConfig) -> HorizonOrchestrator:
    orchestrator = HorizonOrchestrator.__new__(HorizonOrchestrator)
    orchestrator.config = SimpleNamespace(collection=collection)
    return orchestrator


def test_digest_date_uses_configured_timezone():
    orchestrator = make_orchestrator(
        CollectionConfig(digest_timezone="Asia/Shanghai")
    )
    # 23:30 UTC on Nov 25 is 07:30 on Nov 26 in Shanghai.
    now = datetime(2026, 11, 25, 23, 30, tzinfo=timezone.utc)
    assert orchestrator.digest_date(now) == "2026-11-26"


def test_digest_date_defaults_to_utc():
    orchestrator = make_orchestrator(CollectionConfig())
    now = datetime(2026, 11, 25, 23, 30, tzinfo=timezone.utc)
    assert orchestrator.digest_date(now) == "2026-11-25"


def test_collection_rejects_unknown_timezone():
    with pytest.raises(ValidationError, match="digest_timezone"):
        CollectionConfig(digest_timezone="Mars/Olympus")


def test_cross_day_dedup_days_rejects_negative():
    from src.models import ProcessingConfig

    with pytest.raises(ValidationError):
        ProcessingConfig(cross_day_dedup_days=-1)
