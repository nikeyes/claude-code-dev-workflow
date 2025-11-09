# Temperature CLI

Simple command-line tool for temperature conversions.

## Features

- Convert Celsius to Fahrenheit
- Convert Fahrenheit to Celsius
- **Missing**: Kelvin conversions (intentionally incomplete for workflow testing)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Celsius to Fahrenheit
python -m src.converter --celsius 25

# Fahrenheit to Celsius
python -m src.converter --fahrenheit 77
```

## Testing

```bash
pytest tests/
```

## Known Limitations

This is a **validation project** for testing the claude-code-dev-workflow. The following features are intentionally missing:

- Kelvin temperature scale support
- Kelvin conversion functions
- Kelvin CLI arguments
- Kelvin unit tests

These gaps are designed to exercise the full workflow cycle:
1. Research the codebase
2. Plan the implementation
3. Implement missing features
4. Validate against plan criteria
