import pytest
from event_log import EventLog


@pytest.fixture
def log():
    return EventLog()


def test_log_and_get_event(log):
    event = log.log("user.login", user_id=1, metadata="session started")
    assert event["event_type"] == "user.login"
    assert event["user_id"] == 1
    assert event["metadata"] == "session started"


def test_log_with_json_string_metadata(log):
    import json
    payload = json.dumps({"ip": "1.2.3.4", "browser": "Firefox"})
    event = log.log("user.login", user_id=1, metadata=payload)
    assert event["metadata"] == payload


def test_get_events_by_type(log):
    log.log("user.login", user_id=1)
    log.log("user.login", user_id=2)
    log.log("order.created", user_id=1)
    events = log.get_events_by_type("user.login")
    assert len(events) == 2


def test_get_events_by_user(log):
    log.log("user.login", user_id=42)
    log.log("order.created", user_id=42)
    log.log("user.login", user_id=99)
    events = log.get_events_by_user(42)
    assert len(events) == 2


def test_count_events(log):
    assert log.count_events() == 0
    log.log("ping")
    log.log("ping")
    assert log.count_events() == 2


def test_get_nonexistent_event(log):
    assert log.get_event(999) is None


def test_log_without_user(log):
    event = log.log("system.startup")
    assert event["user_id"] is None
