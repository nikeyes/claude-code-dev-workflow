import pytest
from api_gateway import APIGateway


def test_allows_initial_request():
    gw = APIGateway()
    assert gw.check_rate_limit("sess-001") is True


def test_blocks_after_max_requests():
    gw = APIGateway(max_requests=3)
    for _ in range(3):
        gw.record_request("sess-002")
    assert gw.check_rate_limit("sess-002") is False


def test_does_not_affect_other_identifiers():
    gw = APIGateway(max_requests=2)
    gw.record_request("sess-003")
    gw.record_request("sess-003")
    assert gw.check_rate_limit("sess-003") is False
    assert gw.check_rate_limit("sess-004") is True


def test_get_remaining_decreases():
    gw = APIGateway(max_requests=5)
    gw.record_request("sess-005")
    gw.record_request("sess-005")
    assert gw.get_remaining("sess-005") == 3


def test_allowlisted_bypasses_limit():
    gw = APIGateway(max_requests=1)
    gw.add_to_allowlist("sess-006")
    gw.record_request("sess-006")
    gw.record_request("sess-006")
    assert gw.check_rate_limit("sess-006") is True


def test_remove_from_allowlist():
    gw = APIGateway(max_requests=1)
    gw.add_to_allowlist("sess-007")
    gw.remove_from_allowlist("sess-007")
    assert gw.is_allowlisted("sess-007") is False


def test_get_top_offenders():
    gw = APIGateway()
    for _ in range(10):
        gw.record_request("sess-heavy")
    for _ in range(3):
        gw.record_request("sess-light")
    top = gw.get_top_offenders(2)
    assert top[0] == "sess-heavy"
    assert len(top) == 2


def test_get_remaining_for_allowlisted():
    gw = APIGateway(max_requests=10)
    gw.add_to_allowlist("sess-vip")
    assert gw.get_remaining("sess-vip") == 10
