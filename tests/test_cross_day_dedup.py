from datetime import date, datetime, timezone
from types import SimpleNamespace

from src.models import (
    ContentItem,
    ProcessingConfig,
    SourceType,
)
from src.orchestrator import HorizonOrchestrator


def story(title: str, url: str) -> str:
    return (
        f"### [{title}]({url}) ⭐️ 8.0/10\n\n"
        "Summary text.\n\nrss · Example · Apr 1, 10:00\n\n---\n\n"
    )


def item(item_id: str, title: str, url: str) -> ContentItem:
    return ContentItem(
        id=item_id,
        source_type=SourceType.RSS,
        title=title,
        url=url,
        published_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
    )


def make_orchestrator(tmp_path, days: int = 7) -> HorizonOrchestrator:
    orchestrator = HorizonOrchestrator.__new__(HorizonOrchestrator)
    orchestrator.config = SimpleNamespace(
        processing=ProcessingConfig(cross_day_dedup_days=days)
    )
    orchestrator.storage = SimpleNamespace(summaries_dir=tmp_path)
    from rich.console import Console

    orchestrator.console = Console(record=True)
    return orchestrator


def test_filters_url_and_title_seen_in_recent_digests(tmp_path):
    (tmp_path / "horizon-2026-04-01-zh.md").write_text(
        story("Atlas preview", "https://example.com/atlas#section"),
        encoding="utf-8",
    )
    (tmp_path / "horizon-2026-04-02-zh.md").write_text(
        story("Same-day briefing", "https://example.com/today"),
        encoding="utf-8",
    )
    items = [
        item("url-repeat", "Atlas 预览", "https://example.com/atlas/"),
        item(
            "title-repeat",
            "Atlas preview!",
            "https://example.com/atlas-copy",
        ),
        item("today", "Same-day briefing", "https://example.com/today"),
        item("new", "Brand new project", "https://example.com/new"),
    ]

    filtered = make_orchestrator(tmp_path).filter_recent_digest_items(
        items, before=date(2026, 4, 2)
    )

    assert [entry.id for entry in filtered] == ["today", "new"]


def test_disabled_cross_day_dedup_keeps_everything(tmp_path):
    (tmp_path / "horizon-2026-04-01-zh.md").write_text(
        story("Atlas preview", "https://example.com/atlas"),
        encoding="utf-8",
    )
    items = [item("repeat", "Atlas preview", "https://example.com/atlas")]

    filtered = make_orchestrator(tmp_path, days=0).filter_recent_digest_items(
        items, before=date(2026, 4, 2)
    )

    assert filtered == items
