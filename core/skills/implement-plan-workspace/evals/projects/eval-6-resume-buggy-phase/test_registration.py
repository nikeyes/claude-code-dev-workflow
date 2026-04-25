import pytest
from registration import validate_email, validate_age, validate_username


# --- Phase 1 tests: validators (already "done") ---

def test_validate_email_valid():
    assert validate_email("user@example.com") is True


def test_validate_email_invalid():
    with pytest.raises(ValueError, match="Invalid email format"):
        validate_email("not-an-email")


def test_validate_email_empty():
    with pytest.raises(ValueError, match="Email is required"):
        validate_email("")


def test_validate_age_valid():
    assert validate_age(25) is True


def test_validate_age_too_young():
    with pytest.raises(ValueError, match="Age must be between 18 and 120"):
        validate_age(17)


def test_validate_age_boundary_18():
    assert validate_age(18) is True


def test_validate_age_boundary_120():
    assert validate_age(120) is True


def test_validate_age_none():
    with pytest.raises(ValueError, match="Age is required"):
        validate_age(None)


def test_validate_username_valid():
    assert validate_username("john_doe") is True


def test_validate_username_too_short():
    with pytest.raises(ValueError, match="Username must be at least 3 characters"):
        validate_username("ab")


def test_validate_username_special_chars():
    with pytest.raises(ValueError, match="Username can only contain"):
        validate_username("user@name")


# --- Phase 2 tests: register function ---

def test_register_success():
    from registration import register
    result = register("alice", "alice@example.com", 25)
    assert result["username"] == "alice"
    assert result["email"] == "alice@example.com"
    assert result["age"] == 25
    assert "registered_at" in result


def test_register_invalid_email():
    from registration import register
    with pytest.raises(ValueError, match="Invalid email format"):
        register("alice", "bad-email", 25)


def test_register_underage():
    from registration import register
    with pytest.raises(ValueError, match="Age must be between 18 and 120"):
        register("alice", "alice@example.com", 16)


def test_register_invalid_username():
    from registration import register
    with pytest.raises(ValueError, match="Username must be at least 3 characters"):
        register("ab", "ab@example.com", 25)


# --- Phase 3 tests: batch_register ---

def test_batch_register_all_valid():
    from registration import batch_register
    users = [
        {"username": "alice", "email": "alice@test.com", "age": 25},
        {"username": "bob", "email": "bob@test.com", "age": 30},
    ]
    results = batch_register(users)
    assert len(results["succeeded"]) == 2
    assert len(results["failed"]) == 0


def test_batch_register_mixed():
    from registration import batch_register
    users = [
        {"username": "alice", "email": "alice@test.com", "age": 25},
        {"username": "x", "email": "x@test.com", "age": 25},
        {"username": "bob", "email": "bad-email", "age": 30},
    ]
    results = batch_register(users)
    assert len(results["succeeded"]) == 1
    assert len(results["failed"]) == 2
    assert all("error" in f for f in results["failed"])
