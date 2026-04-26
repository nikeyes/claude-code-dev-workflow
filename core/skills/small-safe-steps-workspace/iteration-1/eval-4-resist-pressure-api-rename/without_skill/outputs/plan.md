# Plan: Rename `userName` to `username` in Public REST API Response

## Overview

Rename the `userName` field to `username` in the public REST API response.

---

## Steps

### Step 1: Find all occurrences

Search the codebase for every place `userName` is used in API response serialization:
- Serializers / DTOs / response models
- API controllers / route handlers
- API documentation / OpenAPI / Swagger specs
- Tests that assert on the field name

### Step 2: Update the serializer / response model

Change the field name from `userName` to `username` in the response serializer or DTO. This is the single authoritative source of the field name in the output.

### Step 3: Update API documentation

Update the OpenAPI/Swagger spec (or equivalent docs) to reflect the renamed field so consumers have accurate documentation.

### Step 4: Update all tests

Update any test fixtures, snapshots, or assertions that reference `userName` in API responses to use `username` instead. Run the test suite to confirm all tests pass.

### Step 5: Deploy and verify

Deploy the change and make a manual request to the affected endpoints to confirm the response now contains `username` and no longer contains `userName`.

---

## Done
