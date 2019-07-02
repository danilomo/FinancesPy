import pytest

from financespy import Money

def test_simple_sum():
    m1 = Money(0.1)
    m2 = Money(0.2)

    # Even if initialized with floats, the internal representation use
    # Python3 (long) int, so the test bellow will be valid
    assert Money(0.3) == m1 + m2

def test_overflow():
    m1 = Money(1e20)
    m2 = Money(100)

    # Thanks to Python3's int implementation, we can rest assured
    # overflows will never occur. It switches from a 4-byte integer representation
    # to an arbitrary-sized integer.
    assert Money("100000000000000000100") == m1 + m2

def test_difference():
    result = Money("84.6")
    assert Money(100) - Money(15.4) == result
    assert 100 - Money(15.4) == result
    assert Money(100.0) - 15.4 == result

def test_multiplication():
    assert Money(15) * 4 == Money(60)
    assert 4 * Money(15) == Money(60)
    


