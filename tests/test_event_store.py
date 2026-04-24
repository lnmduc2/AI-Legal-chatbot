from app.automation.event_store import EventStore, MailStateStore
from app.automation.models import LegalDocumentEvent


def build_event(message_id: str, status: str, action: str) -> LegalDocumentEvent:
    return LegalDocumentEvent(
        event_id=f"event-{message_id}",
        created_at="2026-04-24T10:00:00+00:00",
        message_id=message_id,
        subject="Subject",
        sender="Sender",
        sender_email="sender@example.com",
        filename="doc.md",
        doc_path="docs/law/doc.md",
        action=action,
        status=status,
        heuristic_reason="ok",
        matched_keywords=["privacy"],
        notification_recipients=["legal@example.com"],
        notification_status="sent",
    )


def test_event_store_persists_and_summarizes(tmp_path) -> None:
    store = EventStore(tmp_path / "event_log.json")
    store.append_event(build_event("m1", "processed", "created"))
    store.append_event(build_event("m2", "ignored", "ignored"))

    events = store.list_events()
    summary = store.summary()

    assert [event.message_id for event in events] == ["m2", "m1"]
    assert summary["total"] == 2
    assert summary["processed"] == 1
    assert summary["ignored"] == 1
    assert summary["created"] == 1


def test_mail_state_store_tracks_processed_messages(tmp_path) -> None:
    state = MailStateStore(tmp_path / "mail_state.json")
    state.mark_processed("<abc>", 41)

    assert state.has_processed("<abc>") is True
    assert state.get_last_seen_uid() == 41

    state.update_last_seen_uid(50)
    assert state.get_last_seen_uid() == 50
