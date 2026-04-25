# Plan: Add Payment Processing Module

## Overview
Add a payment processing module that validates payment details, calculates fees, and processes transactions with proper error handling.

## Phase 1: Payment Validation
- [x] Add `payment_processor.py` with `PaymentProcessor` class
- [x] Implement `validate_card(card_number)` using Luhn algorithm
- [x] Implement `validate_expiry(month, year)` that rejects expired cards
- [x] Implement `calculate_fee(amount, payment_type)` — 2.9% for credit, 0.5% for debit, flat $0.30 per transaction
- [x] Add tests in `test_payment_processor.py`

## Phase 2: Transaction Processing
- [x] Implement `process_payment(card_number, amount, payment_type)` that validates, calculates fee, and returns a transaction result
- [x] `process_payment` returns dict with keys: `success`, `amount`, `fee`, `net_amount`, `transaction_id`
- [x] Return `success: False` with `error` key if validation fails
- [x] Add tests for transaction processing

## Success Criteria

### Automated Verification
```bash
make test
```
- All tests pass
- Luhn validation correctly identifies invalid card numbers
- Expired cards are rejected
- Fees calculated correctly for both credit and debit
- `process_payment` returns proper error structure on validation failure

### Manual Verification
- [ ] Fee calculations match business requirements (2.9% credit, 0.5% debit, +$0.30)
- [ ] Transaction IDs are unique
- [ ] No sensitive card data stored in memory after processing
