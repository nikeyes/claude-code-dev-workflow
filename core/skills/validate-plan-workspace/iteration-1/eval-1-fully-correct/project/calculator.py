def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


def multiply(a, b):
    return a * b


def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return float(a) / b


def power(base, exponent):
    return base ** exponent


def modulo(a, b):
    if b == 0:
        raise ValueError("Cannot modulo by zero")
    return a % b
