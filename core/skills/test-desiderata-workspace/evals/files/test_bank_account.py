"""
Tests for a simple BankAccount.
Violaciones sembradas:
  - Isolated: balance global compartido entre tests (shared_balance)
  - Deterministic: usa random.randint para un ID de transacción
  - Specific: un solo test verifica deposit, withdraw y balance a la vez
  - Structure-insensitive: assertion sobre atributo interno _ledger
"""
import random
import pytest

shared_balance = 0  # global mutable state used across tests


class BankAccount:
    def __init__(self, owner: str, initial_balance: float = 0):
        self.owner = owner
        self._balance = initial_balance
        self._ledger = []

    def deposit(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Amount must be positive")
        tx_id = random.randint(1000, 9999)  # non-deterministic
        self._ledger.append({"id": tx_id, "amount": amount, "type": "deposit"})
        self._balance += amount
        return self._balance

    def withdraw(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if amount > self._balance:
            raise ValueError("Insufficient funds")
        self._balance -= amount
        self._ledger.append({"amount": -amount, "type": "withdrawal"})
        return self._balance

    def get_balance(self) -> float:
        return self._balance


class TestBankAccount:
    def test_all_operations(self):
        """Single test covering deposit, withdraw and balance check."""
        global shared_balance
        account = BankAccount("Alice", shared_balance)
        account.deposit(100)
        account.withdraw(30)
        shared_balance = account.get_balance()
        # Specific violation: multiple assertions in one test
        assert account.get_balance() == 70
        assert len(account._ledger) == 2  # structure-insensitive violation
        assert account._ledger[0]["type"] == "deposit"

    def test_deposit_updates_ledger(self):
        global shared_balance
        account = BankAccount("Bob", shared_balance)  # depends on previous test's side effect
        account.deposit(50)
        assert len(account._ledger) == 1
        assert account._ledger[0]["type"] == "deposit"

    def test_withdraw_insufficient_funds(self):
        account = BankAccount("Carol", 10)
        with pytest.raises(ValueError, match="Insufficient funds"):
            account.withdraw(100)

    def test_negative_deposit_raises(self):
        account = BankAccount("Dave", 100)
        with pytest.raises(ValueError):
            account.deposit(-10)
