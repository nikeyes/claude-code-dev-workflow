# Test Patterns and Examples

This document provides detailed examples of good and bad patterns for each Test Desiderata property.

**Attribution:** All Test Desiderata concepts are created by Kent Beck. This document applies those principles with concrete examples.

## 1. Isolated - Independence in Execution Order

### Bad: Shared State
```python
# Tests share class-level variable
class TestUser:
    user_count = 0
    
    def test_create_user(self):
        self.user_count += 1
        assert self.user_count == 1  # Fails if run after test_delete_user
    
    def test_delete_user(self):
        self.user_count -= 1
        assert self.user_count == -1  # Depends on execution order
```

### Good: Independent Setup
```python
class TestUser:
    def setUp(self):
        self.user_count = 0  # Fresh state per test
    
    def test_create_user(self):
        self.user_count += 1
        assert self.user_count == 1
    
    def test_delete_user(self):
        self.user_count = 0
        self.user_count -= 1
        assert self.user_count == -1
```

## 2. Composable - Reusable Test Components

### Bad: Monolithic Test
```python
def test_user_workflow(self):
    # Tests too many things at once
    user = create_user(name="Alice", email="alice@example.com")
    assert user.name == "Alice"
    
    user.update_email("new@example.com")
    assert user.email == "new@example.com"
    
    user.add_role("admin")
    assert "admin" in user.roles
    
    user.deactivate()
    assert not user.is_active
```

### Good: Composable Components
```python
def create_test_user(name="Alice", email="alice@example.com"):
    return create_user(name=name, email=email)

def test_user_creation():
    user = create_test_user()
    assert user.name == "Alice"

def test_email_update():
    user = create_test_user()
    user.update_email("new@example.com")
    assert user.email == "new@example.com"

def test_role_assignment():
    user = create_test_user()
    user.add_role("admin")
    assert "admin" in user.roles
```

## 3. Deterministic - Consistent Results

### Bad: Time-Dependent
```python
def test_expiration():
    session = create_session(duration=60)
    time.sleep(61)  # Flaky - timing issues
    assert session.is_expired()
```

### Good: Controlled Time
```python
def test_expiration(mock_time):
    session = create_session(duration=60)
    mock_time.advance(seconds=61)
    assert session.is_expired()
```

### Bad: Random Data
```python
def test_validation():
    email = f"user{random.randint(1, 1000)}@example.com"
    assert is_valid_email(email)  # Different input each run
```

### Good: Fixed Data
```python
def test_validation():
    assert is_valid_email("user@example.com")
    assert not is_valid_email("invalid-email")
```

## 4. Fast - Quick Execution

### Bad: Unnecessary I/O
```python
def test_user_service():
    # Writes to real database
    db = Database(connection_string)
    user = User(name="Alice")
    db.save(user)
    
    retrieved = db.get_user(user.id)
    assert retrieved.name == "Alice"
```

### Good: In-Memory
```python
def test_user_service():
    # Uses in-memory repository
    repo = InMemoryUserRepository()
    user = User(name="Alice")
    repo.save(user)
    
    retrieved = repo.get_user(user.id)
    assert retrieved.name == "Alice"
```

## 5. Writable - Low Friction

### Bad: Excessive Setup
```python
def test_checkout():
    db = setup_database()
    load_fixtures(db)
    user = create_user_with_payment_method(db)
    cart = create_cart(db, user)
    add_items_to_cart(db, cart, [
        {"sku": "ABC", "quantity": 2, "price": 10.99},
        {"sku": "XYZ", "quantity": 1, "price": 5.99}
    ])
    payment_gateway = MockPaymentGateway()
    # Finally test something...
```

### Good: Test Builders
```python
def test_checkout():
    order = OrderBuilder()
        .with_user()
        .with_items([("ABC", 2), ("XYZ", 1)])
        .build()
    
    result = checkout(order)
    assert result.success
```

## 6. Readable - Clear Intent

### Bad: Unclear Purpose
```python
def test_func():
    x = calc(5, 3, True)
    assert x == 8
```

### Good: Expressive
```python
def test_calculator_adds_numbers_when_add_mode_enabled():
    # Arrange
    calculator = Calculator()
    calculator.set_mode(Mode.ADD)
    
    # Act
    result = calculator.calculate(5, 3)
    
    # Assert
    assert result == 8, "Calculator should add 5 + 3 to get 8"
```

## 7. Behavioral - Sensitive to Behavior Changes

### Bad: Tests Implementation
```python
def test_user_repository():
    repo = UserRepository()
    # Tests internal SQL query structure
    assert repo._build_query() == "SELECT * FROM users WHERE id = ?"
```

### Good: Tests Behavior
```python
def test_user_repository():
    repo = UserRepository()
    user = User(id=1, name="Alice")
    repo.save(user)
    
    retrieved = repo.find_by_id(1)
    assert retrieved.name == "Alice"
```

## 8. Structure-insensitive - Resilient to Refactoring

### Bad: Coupled to Structure
```python
def test_order_processor():
    processor = OrderProcessor()
    # Tests private method
    assert processor._validate_items([item1, item2]) == True
    # Tests internal structure
    assert isinstance(processor._payment_gateway, PayPalGateway)
```

### Good: Tests Public Interface
```python
def test_order_processor():
    processor = OrderProcessor()
    order = Order(items=[item1, item2])
    
    result = processor.process(order)
    
    assert result.success
    assert result.payment_confirmed
```

## 9. Automated - No Manual Steps

### Bad: Manual Verification
```python
def test_report_generation():
    report = generate_report()
    print(report)  # Developer must manually check output
    # No assertions
```

### Good: Automated Checks
```python
def test_report_generation():
    report = generate_report()
    
    assert "Summary" in report
    assert report.record_count == 100
    assert report.generated_date == today()
```

## 10. Specific - Clear Failure Diagnosis

### Bad: Multiple Assertions
```python
def test_user_creation():
    user = create_user("Alice", "alice@example.com", "admin")
    assert user.name == "Alice" and user.email == "alice@example.com" and user.role == "admin"
    # Which assertion failed?
```

### Good: One Assertion per Test
```python
def test_user_has_correct_name():
    user = create_user("Alice", "alice@example.com", "admin")
    assert user.name == "Alice"

def test_user_has_correct_email():
    user = create_user("Alice", "alice@example.com", "admin")
    assert user.email == "alice@example.com"

def test_user_has_correct_role():
    user = create_user("Alice", "alice@example.com", "admin")
    assert user.role == "admin"
```

## 11. Predictive - Production Readiness

### Bad: Missing Critical Scenarios
```python
def test_payment():
    # Only tests happy path
    payment = process_payment(amount=100, card="4111111111111111")
    assert payment.success
```

### Good: Comprehensive Coverage
```python
def test_payment_success():
    payment = process_payment(amount=100, card="4111111111111111")
    assert payment.success

def test_payment_insufficient_funds():
    payment = process_payment(amount=100, card=insufficient_funds_card)
    assert not payment.success
    assert payment.error == "Insufficient funds"

def test_payment_invalid_card():
    payment = process_payment(amount=100, card="invalid")
    assert not payment.success
    assert payment.error == "Invalid card number"

def test_payment_network_timeout():
    with mock_network_timeout():
        payment = process_payment(amount=100, card="4111111111111111")
        assert not payment.success
        assert payment.error == "Network timeout"
```

## 12. Inspiring - Confidence Building

### Bad: Trivial Test
```python
def test_user_class_exists():
    user = User()
    assert user is not None  # Tests nothing meaningful
```

### Good: Meaningful Verification
```python
def test_user_authentication_workflow():
    user = User(username="alice", password=hash("secret123"))
    
    # Successful login
    session = authenticate(username="alice", password="secret123")
    assert session.is_valid()
    assert session.user_id == user.id
    
    # Failed login with wrong password
    with pytest.raises(AuthenticationError):
        authenticate(username="alice", password="wrong")
```

## Common Patterns Across Properties

### Test Data Builders
Help with Writable, Readable, Composable:
```python
class UserBuilder:
    def __init__(self):
        self.name = "Default User"
        self.email = "default@example.com"
        self.role = "user"
    
    def with_name(self, name):
        self.name = name
        return self
    
    def with_admin_role(self):
        self.role = "admin"
        return self
    
    def build(self):
        return User(self.name, self.email, self.role)
```

### Fixture Factories
Help with Fast, Isolated, Writable:
```python
@pytest.fixture
def db_session():
    session = create_in_memory_session()
    yield session
    session.close()

@pytest.fixture
def sample_user(db_session):
    user = User(name="Alice")
    db_session.add(user)
    db_session.commit()
    return user
```

### Custom Assertions
Help with Readable, Specific:
```python
def assert_valid_email(email):
    """Assert email format is valid with clear error message"""
    if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
        pytest.fail(f"'{email}' is not a valid email format")

def assert_user_has_role(user, expected_role):
    """Assert user has the expected role"""
    if expected_role not in user.roles:
        pytest.fail(
            f"User {user.name} does not have role '{expected_role}'. "
            f"Current roles: {user.roles}"
        )
```
