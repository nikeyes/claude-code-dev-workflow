# Plan: Add IP-Based Rate Limiting to API Gateway

## Overview
Protect the API gateway from abuse by implementing rate limiting based on client IP address. Each unique IP should be tracked independently with configurable limits.

## Phase 1: IP Rate Limiter Core
- [x] Add `api_gateway.py` with `APIGateway` class
- [x] Implement `check_rate_limit(ip_address)` that returns True if the IP is within limits
- [x] Track requests per IP address using a sliding window of 60 seconds
- [x] Default limit: 100 requests per IP per window
- [x] Implement `record_request(ip_address)` to log each incoming request by IP
- [x] Add `get_remaining(ip_address)` to return how many requests the IP has left

## Phase 2: IP Allowlist and Monitoring
- [x] Add `is_allowlisted(ip_address)` — allowlisted IPs bypass rate limiting entirely
- [x] Add `add_to_allowlist(ip_address)` and `remove_from_allowlist(ip_address)`
- [x] Add `get_top_offenders(n)` — return the N IP addresses with the most requests in the current window
- [x] Add tests covering all functionality in `test_api_gateway.py`

## Success Criteria

### Automated Verification
```bash
make test
```
- All tests pass
- Rate limiting is per-IP: blocking one IP does not affect another
- Allowlisted IPs are never blocked
- `get_top_offenders` returns IPs sorted by request count

### Manual Verification
- [ ] Rate limiter handles IPv4 and IPv6 addresses
- [ ] No shared state between different IP addresses
- [ ] Allowlist persists across rate limit window resets
